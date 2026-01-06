"""
Evaluation Runner
=================

評価実行エンジン
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, UTC
from typing import Optional, AsyncIterator
import uuid

from .models import (
    EvaluationConfig,
    EvaluationDataset,
    EvaluationDocument,
    EvaluationResult,
    EvaluationStatus,
    EvaluationSummary,
    DocumentEvaluationResult,
    CheckEvaluationResult,
    RepeatResult,
    MetricResult,
    MetricType,
)
from src.review.engine import ReviewEngine
from src.review.models import ReviewRequest, ReviewOptions


class EvaluationRunner:
    """評価実行エンジン"""
    
    def __init__(
        self,
        use_llm: bool = False,
    ):
        self.use_llm = use_llm
        self._datasets: dict[str, EvaluationDataset] = {}
        self._results: dict[str, EvaluationResult] = {}
    
    def register_dataset(self, dataset: EvaluationDataset) -> None:
        """データセットを登録"""
        self._datasets[dataset.id] = dataset
    
    def get_dataset(self, dataset_id: str) -> Optional[EvaluationDataset]:
        """データセットを取得"""
        return self._datasets.get(dataset_id)
    
    def list_datasets(self) -> list[EvaluationDataset]:
        """データセット一覧"""
        return list(self._datasets.values())
    
    async def run_evaluation(
        self,
        config: EvaluationConfig,
    ) -> EvaluationResult:
        """評価を実行"""
        evaluation_id = f"eval-{uuid.uuid4().hex[:12]}"
        
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            config=config,
            status=EvaluationStatus.RUNNING,
            started_at=datetime.now(UTC).isoformat(),
        )
        
        try:
            # データセット取得
            dataset = self._datasets.get(config.dataset_id)
            if not dataset:
                raise ValueError(f"Dataset not found: {config.dataset_id}")
            
            # 繰り返し実行
            all_repeat_results = []
            for run_number in range(1, config.repeat_count + 1):
                run_result = await self._run_single_evaluation(
                    config=config,
                    dataset=dataset,
                    run_number=run_number,
                )
                all_repeat_results.append(run_result)
            
            # 最初の実行結果を使用
            result.document_results = all_repeat_results[0]["document_results"]
            result.summary = all_repeat_results[0]["summary"]
            
            # 繰り返し結果を記録
            if config.repeat_count > 1:
                result.repeat_results = [
                    RepeatResult(
                        run_number=r["run_number"],
                        accuracy=r["summary"].accuracy,
                        processing_time_ms=r["summary"].total_processing_time_ms,
                        results_hash=r["results_hash"],
                    )
                    for r in all_repeat_results
                ]
                
                # 一貫性率を計算
                hashes = [r["results_hash"] for r in all_repeat_results]
                unique_hashes = len(set(hashes))
                result.summary.consistency_rate = 1.0 / unique_hashes if unique_hashes > 0 else 0.0
            
            # メトリクス追加
            result.metrics = self._calculate_metrics(result.summary)
            
            result.status = EvaluationStatus.COMPLETED
            result.completed_at = datetime.now(UTC).isoformat()
            
        except Exception as e:
            result.status = EvaluationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(UTC).isoformat()
        
        self._results[evaluation_id] = result
        return result
    
    async def _run_single_evaluation(
        self,
        config: EvaluationConfig,
        dataset: EvaluationDataset,
        run_number: int,
    ) -> dict:
        """単一評価実行"""
        engine = ReviewEngine(use_llm=self.use_llm)
        
        document_results = []
        summary = EvaluationSummary()
        all_check_results = []
        
        for doc in dataset.documents:
            doc_result = await self._evaluate_document(
                engine=engine,
                document=doc,
                check_item_ids=config.check_item_ids,
                parallel=config.parallel,
            )
            document_results.append(doc_result)
            all_check_results.extend(doc_result.check_results)
            
            # サマリー更新
            summary.total_documents += 1
            summary.total_checks += doc_result.total_checks
            summary.correct_checks += doc_result.correct_checks
            summary.total_processing_time_ms += doc_result.processing_time_ms
        
        # TP/FP/TN/FN計算
        for check_result in all_check_results:
            expected_fail = check_result.expected_result == "fail"
            actual_fail = check_result.actual_result == "fail"
            
            if expected_fail and actual_fail:
                summary.true_positives += 1
            elif not expected_fail and actual_fail:
                summary.false_positives += 1
            elif not expected_fail and not actual_fail:
                summary.true_negatives += 1
            else:  # expected_fail and not actual_fail
                summary.false_negatives += 1
        
        # メトリクス計算
        summary.calculate_metrics()
        
        # 結果ハッシュ計算（再現性検証用）
        results_data = [
            {
                "document_id": r.document_id,
                "check_item_id": r.check_item_id,
                "actual_result": r.actual_result,
            }
            for r in all_check_results
        ]
        results_hash = hashlib.md5(
            json.dumps(results_data, sort_keys=True).encode()
        ).hexdigest()
        
        return {
            "run_number": run_number,
            "document_results": document_results,
            "summary": summary,
            "results_hash": results_hash,
        }
    
    async def _evaluate_document(
        self,
        engine: ReviewEngine,
        document: EvaluationDocument,
        check_item_ids: Optional[list[str]],
        parallel: bool,
    ) -> DocumentEvaluationResult:
        """文書を評価"""
        start_time = time.time()
        
        # 評価対象チェック項目を決定
        target_check_ids = check_item_ids
        if not target_check_ids:
            target_check_ids = [gt.check_item_id for gt in document.ground_truth]
        
        # レビュー実行
        request = ReviewRequest(
            document_id=document.id,
            document_content=document.content,
            document_type=document.document_type,
            check_item_ids=target_check_ids,
            options=ReviewOptions(parallel=parallel),
        )
        
        review_result = await engine.review_document(request)
        
        # 正解データとマッチング
        check_results = []
        correct_count = 0
        
        ground_truth_map = {gt.check_item_id: gt for gt in document.ground_truth}
        
        for check_result in review_result.check_results:
            gt = ground_truth_map.get(check_result.check_item_id)
            if not gt:
                continue
            
            actual_result = check_result.status.value
            is_correct = actual_result == gt.expected_result
            
            if is_correct:
                correct_count += 1
            
            # 指摘事項のマッチング
            actual_findings = [f.title for f in check_result.findings]
            finding_match_count = len(
                set(gt.expected_findings) & set(actual_findings)
            )
            
            check_results.append(CheckEvaluationResult(
                check_item_id=check_result.check_item_id,
                document_id=document.id,
                expected_result=gt.expected_result,
                actual_result=actual_result,
                is_correct=is_correct,
                expected_findings=gt.expected_findings,
                actual_findings=actual_findings,
                finding_match_count=finding_match_count,
                processing_time_ms=check_result.execution_time_ms,
            ))
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return DocumentEvaluationResult(
            document_id=document.id,
            document_name=document.name,
            check_results=check_results,
            total_checks=len(check_results),
            correct_checks=correct_count,
            accuracy=correct_count / len(check_results) if check_results else 0.0,
            processing_time_ms=processing_time_ms,
        )
    
    def _calculate_metrics(self, summary: EvaluationSummary) -> list[MetricResult]:
        """メトリクスを計算"""
        metrics = [
            MetricResult(
                metric_type=MetricType.PRECISION,
                value=summary.precision,
                details={"formula": "TP / (TP + FP)"},
            ),
            MetricResult(
                metric_type=MetricType.RECALL,
                value=summary.recall,
                details={"formula": "TP / (TP + FN)"},
            ),
            MetricResult(
                metric_type=MetricType.F1_SCORE,
                value=summary.f1_score,
                details={"formula": "2 * (P * R) / (P + R)"},
            ),
            MetricResult(
                metric_type=MetricType.ACCURACY,
                value=summary.accuracy,
                details={"formula": "correct / total"},
            ),
            MetricResult(
                metric_type=MetricType.PROCESSING_TIME,
                value=summary.avg_processing_time_ms,
                details={
                    "unit": "ms",
                    "total": summary.total_processing_time_ms,
                },
            ),
        ]
        return metrics
    
    def get_result(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """評価結果を取得"""
        return self._results.get(evaluation_id)
    
    def list_results(self) -> list[EvaluationResult]:
        """評価結果一覧"""
        return list(self._results.values())


async def run_evaluation_streaming(
    runner: EvaluationRunner,
    config: EvaluationConfig,
) -> AsyncIterator[dict]:
    """評価をストリーミング実行"""
    evaluation_id = f"eval-{uuid.uuid4().hex[:12]}"
    
    yield {
        "type": "started",
        "evaluation_id": evaluation_id,
        "config": config.model_dump(),
    }
    
    dataset = runner.get_dataset(config.dataset_id)
    if not dataset:
        yield {
            "type": "error",
            "message": f"Dataset not found: {config.dataset_id}",
        }
        return
    
    engine = ReviewEngine(use_llm=runner.use_llm)
    total_docs = len(dataset.documents)
    
    for idx, doc in enumerate(dataset.documents):
        yield {
            "type": "progress",
            "current": idx + 1,
            "total": total_docs,
            "document_id": doc.id,
            "document_name": doc.name,
        }
        
        doc_result = await runner._evaluate_document(
            engine=engine,
            document=doc,
            check_item_ids=config.check_item_ids,
            parallel=config.parallel,
        )
        
        yield {
            "type": "document_completed",
            "document_id": doc.id,
            "accuracy": doc_result.accuracy,
            "total_checks": doc_result.total_checks,
            "correct_checks": doc_result.correct_checks,
        }
    
    yield {
        "type": "completed",
        "evaluation_id": evaluation_id,
    }


def create_evaluation_runner(use_llm: bool = False) -> EvaluationRunner:
    """評価ランナーを作成"""
    return EvaluationRunner(use_llm=use_llm)
