"""
Review Engine
=============

文書レビューのメインオーケストレーター
"""

import uuid
import asyncio
import time
from datetime import datetime, UTC
from typing import Optional, AsyncIterator

from src.knowledge.schema import CHECK_ITEMS_DATA
from src.review.models import (
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
    ReviewMetadata,
    ReviewProgress,
    CheckResult,
    CheckResultStatus,
    Finding,
    Suggestion,
)
from src.review.executor import CheckExecutor


class ReviewEngine:
    """
    文書レビューエンジン
    
    MCP Server間の連携を行い、文書レビューを実行する。
    - smartreviewer-core: 文書管理
    - smartreviewer-rag: 関連情報検索
    - smartreviewer-knowledge: 知識グラフ参照
    """
    
    def __init__(
        self,
        use_llm: bool = True,
        rag_client: Optional[object] = None,
        knowledge_client: Optional[object] = None,
    ):
        """
        Args:
            use_llm: LLM推論を使用するか
            rag_client: RAGサーバークライアント
            knowledge_client: Knowledgeサーバークライアント
        """
        self.use_llm = use_llm
        self.rag_client = rag_client
        self.knowledge_client = knowledge_client
        self.executor = CheckExecutor(use_llm=use_llm)
        
        # 進行中レビューのストレージ
        self._active_reviews: dict[str, ReviewProgress] = {}
    
    async def review_document(
        self,
        request: ReviewRequest,
    ) -> ReviewResult:
        """
        文書レビューを実行
        
        Args:
            request: レビューリクエスト
        
        Returns:
            ReviewResult
        """
        review_id = f"review-{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        created_at = datetime.now(UTC).isoformat()
        
        # チェック項目の取得
        check_items = self._get_check_items(
            document_type=request.document_type,
            check_item_ids=request.check_item_ids,
        )
        
        if not check_items:
            return ReviewResult(
                review_id=review_id,
                document_id=request.document_id,
                document_type=request.document_type,
                status=ReviewStatus.FAILED,
                overall_result=CheckResultStatus.SKIP,
                created_at=created_at,
                total_findings=0,
                critical_findings=0,
                metadata=ReviewMetadata(
                    checks_executed=0,
                    checks_passed=0,
                    checks_failed=0,
                    checks_warning=0,
                    checks_skipped=0,
                ),
            )
        
        # 進捗を初期化
        self._active_reviews[review_id] = ReviewProgress(
            review_id=review_id,
            current_check=0,
            total_checks=len(check_items),
            current_check_name="",
            percent_complete=0.0,
            findings_so_far=0,
        )
        
        try:
            # RAGコンテキストを取得（オプション）
            context = None
            if self.rag_client:
                context = await self._get_rag_context(request.document_content)
            
            # チェック実行
            if request.options.parallel:
                check_results = await self._execute_parallel(
                    review_id=review_id,
                    check_items=check_items,
                    document_content=request.document_content,
                    document_type=request.document_type,
                    context=context,
                )
            else:
                check_results = await self._execute_sequential(
                    review_id=review_id,
                    check_items=check_items,
                    document_content=request.document_content,
                    document_type=request.document_type,
                    context=context,
                )
            
            # 結果を集計
            execution_time = int((time.time() - start_time) * 1000)
            completed_at = datetime.now(UTC).isoformat()
            
            # 統計計算
            total_findings = sum(len(r.findings) for r in check_results)
            critical_findings = sum(
                len([f for f in r.findings if f.severity.value == "critical"])
                for r in check_results
            )
            
            passed = sum(1 for r in check_results if r.status == CheckResultStatus.PASS)
            failed = sum(1 for r in check_results if r.status == CheckResultStatus.FAIL)
            warnings = sum(1 for r in check_results if r.status == CheckResultStatus.WARNING)
            skipped = sum(1 for r in check_results if r.status == CheckResultStatus.SKIP)
            
            # 総合結果の判定
            if failed > 0:
                overall_result = CheckResultStatus.FAIL
            elif warnings > 0:
                overall_result = CheckResultStatus.WARNING
            elif skipped == len(check_results):
                overall_result = CheckResultStatus.SKIP
            else:
                overall_result = CheckResultStatus.PASS
            
            return ReviewResult(
                review_id=review_id,
                document_id=request.document_id,
                document_type=request.document_type,
                status=ReviewStatus.COMPLETED,
                overall_result=overall_result,
                created_at=created_at,
                completed_at=completed_at,
                execution_time_ms=execution_time,
                total_findings=total_findings,
                critical_findings=critical_findings,
                check_results=check_results,
                metadata=ReviewMetadata(
                    checks_executed=len(check_results),
                    checks_passed=passed,
                    checks_failed=failed,
                    checks_warning=warnings,
                    checks_skipped=skipped,
                ),
            )
        
        finally:
            # 進捗をクリーンアップ
            self._active_reviews.pop(review_id, None)
    
    async def review_document_streaming(
        self,
        request: ReviewRequest,
    ) -> AsyncIterator[ReviewProgress | ReviewResult]:
        """
        文書レビューをストリーミング実行
        
        Args:
            request: レビューリクエスト
        
        Yields:
            ReviewProgress (進捗) または ReviewResult (最終結果)
        """
        review_id = f"review-{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        created_at = datetime.now(UTC).isoformat()
        
        # チェック項目の取得
        check_items = self._get_check_items(
            document_type=request.document_type,
            check_item_ids=request.check_item_ids,
        )
        
        total_checks = len(check_items)
        check_results: list[CheckResult] = []
        findings_count = 0
        
        # RAGコンテキストを取得
        context = None
        if self.rag_client:
            context = await self._get_rag_context(request.document_content)
        
        # 順次実行（ストリーミング時は並列実行しない）
        for i, check_item in enumerate(check_items):
            progress = ReviewProgress(
                review_id=review_id,
                current_check=i + 1,
                total_checks=total_checks,
                current_check_name=check_item["name"],
                percent_complete=((i + 1) / total_checks) * 100,
                findings_so_far=findings_count,
            )
            yield progress
            
            # チェック実行
            result = await self.executor.execute_check(
                check_item_id=check_item["id"],
                document_content=request.document_content,
                document_type=request.document_type,
                context=context,
            )
            
            check_results.append(result)
            findings_count += len(result.findings)
        
        # 結果を集計
        execution_time = int((time.time() - start_time) * 1000)
        completed_at = datetime.now(UTC).isoformat()
        
        total_findings = sum(len(r.findings) for r in check_results)
        critical_findings = sum(
            len([f for f in r.findings if f.severity.value == "critical"])
            for r in check_results
        )
        
        passed = sum(1 for r in check_results if r.status == CheckResultStatus.PASS)
        failed = sum(1 for r in check_results if r.status == CheckResultStatus.FAIL)
        warnings = sum(1 for r in check_results if r.status == CheckResultStatus.WARNING)
        skipped = sum(1 for r in check_results if r.status == CheckResultStatus.SKIP)
        
        if failed > 0:
            overall_result = CheckResultStatus.FAIL
        elif warnings > 0:
            overall_result = CheckResultStatus.WARNING
        elif skipped == len(check_results):
            overall_result = CheckResultStatus.SKIP
        else:
            overall_result = CheckResultStatus.PASS
        
        yield ReviewResult(
            review_id=review_id,
            document_id=request.document_id,
            document_type=request.document_type,
            status=ReviewStatus.COMPLETED,
            overall_result=overall_result,
            created_at=created_at,
            completed_at=completed_at,
            execution_time_ms=execution_time,
            total_findings=total_findings,
            critical_findings=critical_findings,
            check_results=check_results,
            metadata=ReviewMetadata(
                checks_executed=len(check_results),
                checks_passed=passed,
                checks_failed=failed,
                checks_warning=warnings,
                checks_skipped=skipped,
            ),
        )
    
    def get_progress(self, review_id: str) -> Optional[ReviewProgress]:
        """
        レビュー進捗を取得
        
        Args:
            review_id: レビューID
        
        Returns:
            ReviewProgress または None
        """
        return self._active_reviews.get(review_id)
    
    def _get_check_items(
        self,
        document_type: str,
        check_item_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """チェック項目を取得"""
        items = [
            item for item in CHECK_ITEMS_DATA
            if item["document_type"] == document_type
        ]
        
        if check_item_ids:
            items = [item for item in items if item["id"] in check_item_ids]
        
        return items
    
    async def _execute_parallel(
        self,
        review_id: str,
        check_items: list[dict],
        document_content: str,
        document_type: str,
        context: Optional[dict] = None,
    ) -> list[CheckResult]:
        """並列実行"""
        check_ids = [item["id"] for item in check_items]
        return await self.executor.execute_checks_parallel(
            check_item_ids=check_ids,
            document_content=document_content,
            document_type=document_type,
            context=context,
        )
    
    async def _execute_sequential(
        self,
        review_id: str,
        check_items: list[dict],
        document_content: str,
        document_type: str,
        context: Optional[dict] = None,
    ) -> list[CheckResult]:
        """順次実行"""
        results = []
        total = len(check_items)
        findings_count = 0
        
        for i, check_item in enumerate(check_items):
            # 進捗更新
            self._active_reviews[review_id] = ReviewProgress(
                review_id=review_id,
                current_check=i + 1,
                total_checks=total,
                current_check_name=check_item["name"],
                percent_complete=((i + 1) / total) * 100,
                findings_so_far=findings_count,
            )
            
            result = await self.executor.execute_check(
                check_item_id=check_item["id"],
                document_content=document_content,
                document_type=document_type,
                context=context,
            )
            
            results.append(result)
            findings_count += len(result.findings)
        
        return results
    
    async def _get_rag_context(self, document_content: str) -> Optional[dict]:
        """RAGコンテキストを取得"""
        if not self.rag_client:
            return None
        
        # RAGサーバーから関連情報を取得
        # TODO: MCP Client経由でsmartreviewer-ragを呼び出す
        return None


# ==============================================
# Factory Function
# ==============================================

def create_review_engine(
    use_llm: bool = True,
    rag_client: Optional[object] = None,
    knowledge_client: Optional[object] = None,
) -> ReviewEngine:
    """
    ReviewEngineインスタンスを作成
    
    Args:
        use_llm: LLM推論を使用するか
        rag_client: RAGサーバークライアント
        knowledge_client: Knowledgeサーバークライアント
    
    Returns:
        ReviewEngine
    """
    return ReviewEngine(
        use_llm=use_llm,
        rag_client=rag_client,
        knowledge_client=knowledge_client,
    )
