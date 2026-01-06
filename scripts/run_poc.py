#!/usr/bin/env python
"""
PoC実施スクリプト
================

P3-2: PoC実施
- P3-2-1: 基本設計書チェック実行（10件）
- P3-2-2: テスト計画書チェック実行（10件）
- P3-2-3: チェック合致率計測
- P3-2-4: 処理時間・コスト計測
- P3-2-5: 再現性検証（同一入力複数回実行）
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# プロジェクトルートをパスに追加
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import (
    EvaluationRunner,
    EvaluationConfig,
    EvaluationResult,
    EvaluationStatus,
    create_basic_design_dataset,
    create_test_plan_dataset,
    run_evaluation_streaming,
)


def create_poc_config(
    name: str,
    dataset_id: str,
    repeat_count: int = 3,
) -> EvaluationConfig:
    """PoC用評価設定を作成"""
    return EvaluationConfig(
        name=name,
        dataset_id=dataset_id,
        repeat_count=repeat_count,
        timeout_seconds=300,
        use_llm=False,  # PoC Phase 1はルールベースのみ
    )


async def run_basic_design_evaluation(
    runner: EvaluationRunner,
    repeat_count: int = 3,
) -> EvaluationResult:
    """基本設計書チェック実行"""
    dataset = create_basic_design_dataset()
    runner.register_dataset(dataset)
    
    config = create_poc_config(
        name="PoC-基本設計書評価",
        dataset_id=dataset.id,
        repeat_count=repeat_count,
    )
    
    print(f"\n{'='*60}")
    print(f"📋 基本設計書チェック実行")
    print(f"   - データセット: {dataset.name}")
    print(f"   - ドキュメント数: {len(dataset.documents)}")
    print(f"   - 繰り返し回数: {repeat_count}")
    print(f"{'='*60}")
    
    result = await runner.run_evaluation(config)
    return result


async def run_test_plan_evaluation(
    runner: EvaluationRunner,
    repeat_count: int = 3,
) -> EvaluationResult:
    """テスト計画書チェック実行"""
    dataset = create_test_plan_dataset()
    runner.register_dataset(dataset)
    
    config = create_poc_config(
        name="PoC-テスト計画書評価",
        dataset_id=dataset.id,
        repeat_count=repeat_count,
    )
    
    print(f"\n{'='*60}")
    print(f"📋 テスト計画書チェック実行")
    print(f"   - データセット: {dataset.name}")
    print(f"   - ドキュメント数: {len(dataset.documents)}")
    print(f"   - 繰り返し回数: {repeat_count}")
    print(f"{'='*60}")
    
    result = await runner.run_evaluation(config)
    return result


def print_result_summary(result: EvaluationResult, title: str):
    """評価結果サマリーを表示"""
    summary = result.summary
    
    print(f"\n{'='*60}")
    print(f"📊 {title} - 結果サマリー")
    print(f"{'='*60}")
    print(f"ステータス: {result.status.value}")
    print(f"処理時間: {summary.total_processing_time_ms / 1000:.2f}秒")
    print(f"ドキュメント数: {summary.total_documents}")
    print(f"チェック項目数: {summary.total_checks}")
    
    print(f"\n📈 メトリクス:")
    print(f"   - Accuracy: {summary.accuracy:.1%}")
    print(f"   - Precision: {summary.precision:.1%}")
    print(f"   - Recall: {summary.recall:.1%}")
    print(f"   - F1 Score: {summary.f1_score:.1%}")
    
    print(f"\n📊 混同行列:")
    print(f"   - True Positive (TP): {summary.true_positives}")
    print(f"   - True Negative (TN): {summary.true_negatives}")
    print(f"   - False Positive (FP): {summary.false_positives}")
    print(f"   - False Negative (FN): {summary.false_negatives}")
    
    if result.repeat_results:
        print(f"\n🔄 再現性検証:")
        print(f"   - 繰り返し回数: {len(result.repeat_results)}")
        
        # 結果のハッシュで一貫性を確認
        hashes = [r.results_hash for r in result.repeat_results]
        unique_hashes = set(hashes)
        consistency_count = sum(1 for h in hashes if hashes.count(h) == len(hashes))
        
        if len(unique_hashes) == 1:
            print(f"   - 結果一貫性: 100% (全実行で同一結果)")
        else:
            print(f"   - 結果一貫性: {len(unique_hashes)}種類の異なる結果")
        
        # 各実行のAccuracy
        avg_accuracy = sum(r.accuracy for r in result.repeat_results) / len(result.repeat_results)
        print(f"   - 平均Accuracy: {avg_accuracy:.1%}")


def print_detailed_results(result: EvaluationResult):
    """詳細結果を表示"""
    print(f"\n{'='*60}")
    print(f"📝 詳細結果")
    print(f"{'='*60}")
    
    for doc_result in result.document_results:
        print(f"\n📄 {doc_result.document_id}")
        print(f"   処理時間: {doc_result.processing_time:.2f}秒")
        
        for check_result in doc_result.check_results:
            status_icon = "✅" if check_result.is_correct else "❌"
            print(f"   {status_icon} {check_result.check_id}")
            print(f"      予測: {check_result.predicted} / 正解: {check_result.expected}")


async def run_poc_evaluation(
    repeat_count: int = 3,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
):
    """PoC評価を実行"""
    print(f"\n{'='*60}")
    print(f"🚀 SmartReviewer PoC評価開始")
    print(f"   実行日時: {datetime.now().isoformat()}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # ランナー作成
    runner = EvaluationRunner(use_llm=False)
    
    # 基本設計書チェック
    bd_result = await run_basic_design_evaluation(runner, repeat_count)
    print_result_summary(bd_result, "基本設計書")
    if verbose:
        print_detailed_results(bd_result)
    
    # テスト計画書チェック
    tp_result = await run_test_plan_evaluation(runner, repeat_count)
    print_result_summary(tp_result, "テスト計画書")
    if verbose:
        print_detailed_results(tp_result)
    
    # 総合結果
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"📊 PoC評価 総合結果")
    print(f"{'='*60}")
    print(f"総処理時間: {total_time:.2f}秒")
    
    # 総合メトリクス計算
    total_tp = bd_result.summary.true_positives + tp_result.summary.true_positives
    total_tn = bd_result.summary.true_negatives + tp_result.summary.true_negatives
    total_fp = bd_result.summary.false_positives + tp_result.summary.false_positives
    total_fn = bd_result.summary.false_negatives + tp_result.summary.false_negatives
    total_all = total_tp + total_tn + total_fp + total_fn
    
    if total_all > 0:
        accuracy = (total_tp + total_tn) / total_all
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\n📈 総合メトリクス:")
        print(f"   - Accuracy: {accuracy:.1%}")
        print(f"   - Precision: {precision:.1%}")
        print(f"   - Recall: {recall:.1%}")
        print(f"   - F1 Score: {f1:.1%}")
    
    # 結果保存
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 基本設計書結果
        bd_file = output_dir / f"poc_basic_design_{timestamp}.json"
        with open(bd_file, "w", encoding="utf-8") as f:
            json.dump(bd_result.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        print(f"\n📁 基本設計書結果保存: {bd_file}")
        
        # テスト計画書結果
        tp_file = output_dir / f"poc_test_plan_{timestamp}.json"
        with open(tp_file, "w", encoding="utf-8") as f:
            json.dump(tp_result.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        print(f"📁 テスト計画書結果保存: {tp_file}")
        
        # 総合サマリー
        summary_file = output_dir / f"poc_summary_{timestamp}.json"
        summary_data = {
            "execution_time": datetime.now().isoformat(),
            "total_processing_time": total_time,
            "basic_design": {
                "status": bd_result.status.value,
                "accuracy": bd_result.summary.accuracy,
                "precision": bd_result.summary.precision,
                "recall": bd_result.summary.recall,
                "f1_score": bd_result.summary.f1_score,
            },
            "test_plan": {
                "status": tp_result.status.value,
                "accuracy": tp_result.summary.accuracy,
                "precision": tp_result.summary.precision,
                "recall": tp_result.summary.recall,
                "f1_score": tp_result.summary.f1_score,
            },
            "total": {
                "accuracy": accuracy if total_all > 0 else 0,
                "precision": precision if total_all > 0 else 0,
                "recall": recall if total_all > 0 else 0,
                "f1_score": f1 if total_all > 0 else 0,
            },
        }
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        print(f"📁 総合サマリー保存: {summary_file}")
    
    print(f"\n{'='*60}")
    print(f"✅ PoC評価完了")
    print(f"{'='*60}")
    
    return bd_result, tp_result


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartReviewer PoC評価スクリプト")
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="再現性検証の繰り返し回数 (default: 3)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="storage/poc_results",
        help="結果出力ディレクトリ (default: storage/poc_results)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細結果を表示",
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_poc_evaluation(
        repeat_count=args.repeat,
        output_dir=Path(args.output) if args.output else None,
        verbose=args.verbose,
    ))


if __name__ == "__main__":
    main()
