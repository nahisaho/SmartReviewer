"""
Tests for Review Engine
=======================

ReviewEngineとCheckExecutorのユニットテスト
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ==============================================
# Import Tests
# ==============================================

class TestImports:
    """インポートテスト"""
    
    def test_import_review_package(self):
        """reviewパッケージがインポートできること"""
        from src import review
        assert review is not None
    
    def test_import_review_engine(self):
        """ReviewEngineがインポートできること"""
        from src.review.engine import ReviewEngine
        assert ReviewEngine is not None
    
    def test_import_check_executor(self):
        """CheckExecutorがインポートできること"""
        from src.review.executor import CheckExecutor
        assert CheckExecutor is not None
    
    def test_import_models(self):
        """モデルがインポートできること"""
        from src.review.models import (
            ReviewRequest,
            ReviewResult,
            ReviewOptions,
            Finding,
            Suggestion,
            CheckResult,
            ReviewStatus,
            CheckResultStatus,
        )
        assert ReviewRequest is not None
        assert ReviewResult is not None
        assert Finding is not None


# ==============================================
# Model Tests
# ==============================================

class TestModels:
    """モデルテスト"""
    
    def test_review_options_defaults(self):
        """ReviewOptionsのデフォルト値"""
        from src.review.models import ReviewOptions
        
        options = ReviewOptions()
        
        assert options.parallel is True
        assert options.include_evidence is True
        assert options.max_findings == 100
        assert options.timeout_seconds == 300
        assert options.use_llm is True
    
    def test_review_request_model(self):
        """ReviewRequestモデル"""
        from src.review.models import ReviewRequest
        
        request = ReviewRequest(
            document_id="doc-123",
            document_content="Test content",
            document_type="basic_design",
        )
        
        assert request.document_id == "doc-123"
        assert request.document_type == "basic_design"
        assert request.check_item_ids is None
    
    def test_finding_model(self):
        """Findingモデル"""
        from src.review.models import Finding, FindingType, Severity
        
        finding = Finding(
            id="f-001",
            check_item_id="BD-001",
            type=FindingType.ERROR,
            severity=Severity.HIGH,
            title="Test Finding",
            description="Test description",
        )
        
        assert finding.id == "f-001"
        assert finding.type == FindingType.ERROR
        assert finding.severity == Severity.HIGH
    
    def test_suggestion_model(self):
        """Suggestionモデル"""
        from src.review.models import Suggestion
        
        suggestion = Suggestion(
            id="s-001",
            finding_id="f-001",
            title="Test Suggestion",
            description="Test description",
            priority=1,
        )
        
        assert suggestion.finding_id == "f-001"
        assert suggestion.priority == 1
    
    def test_check_result_model(self):
        """CheckResultモデル"""
        from src.review.models import CheckResult, CheckResultStatus
        
        result = CheckResult(
            check_item_id="BD-001",
            check_item_name="Test Check",
            status=CheckResultStatus.PASS,
            confidence=0.95,
        )
        
        assert result.status == CheckResultStatus.PASS
        assert result.confidence == 0.95
        assert len(result.findings) == 0


# ==============================================
# CheckExecutor Tests
# ==============================================

class TestCheckExecutor:
    """CheckExecutorテスト"""
    
    def test_create_executor(self):
        """エグゼキュータを作成できること"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        assert executor is not None
        assert executor.use_llm is False
    
    @pytest.mark.asyncio
    async def test_execute_check_unknown_item(self):
        """存在しないチェック項目の実行"""
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        executor = CheckExecutor(use_llm=False)
        
        result = await executor.execute_check(
            check_item_id="UNKNOWN-999",
            document_content="Test content",
            document_type="basic_design",
        )
        
        assert result.status == CheckResultStatus.SKIP
        assert "not found" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_execute_check_wrong_document_type(self):
        """文書タイプ不一致の場合はスキップ"""
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        executor = CheckExecutor(use_llm=False)
        
        # BD-001は basic_design 用なので test_plan ではスキップ
        result = await executor.execute_check(
            check_item_id="BD-001",
            document_content="Test content",
            document_type="test_plan",
        )
        
        assert result.status == CheckResultStatus.SKIP
    
    @pytest.mark.asyncio
    async def test_execute_check_bd_001_pass(self):
        """BD-001: 全必須セクションがある場合はPASS"""
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        executor = CheckExecutor(use_llm=False)
        
        document_content = """
        # 基本設計書
        
        ## システム概要
        このシステムは...
        
        ## システム構成
        アーキテクチャ構成...
        
        ## 機能設計
        機能一覧...
        
        ## データ設計
        データモデル...
        
        ## インターフェース設計
        API設計...
        """
        
        result = await executor.execute_check(
            check_item_id="BD-001",
            document_content=document_content,
            document_type="basic_design",
        )
        
        assert result.status == CheckResultStatus.PASS
        assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_execute_check_bd_001_fail(self):
        """BD-001: システム概要がない場合はFAIL"""
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        executor = CheckExecutor(use_llm=False)
        
        document_content = """
        # 基本設計書
        
        ## 機能設計
        ...
        """
        
        result = await executor.execute_check(
            check_item_id="BD-001",
            document_content=document_content,
            document_type="basic_design",
        )
        
        assert result.status == CheckResultStatus.FAIL
        assert len(result.findings) > 0
        assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_execute_check_tp_001_pass(self):
        """TP-001: 全必須セクションがある場合はPASS"""
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        executor = CheckExecutor(use_llm=False)
        
        document_content = """
        # テスト計画書
        
        ## 概要
        本テスト計画は...
        
        ## テスト範囲
        本テストでは...
        
        ## テスト環境
        環境構成...
        
        ## テストスケジュール
        日程...
        """
        
        result = await executor.execute_check(
            check_item_id="TP-001",
            document_content=document_content,
            document_type="test_plan",
        )
        
        assert result.status == CheckResultStatus.PASS
    
    @pytest.mark.asyncio
    async def test_execute_checks_parallel(self):
        """並列実行テスト"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        document_content = """
        # 基本設計書
        
        ## システム概要
        ...
        """
        
        # BD-001とBD-002を並列実行
        results = await executor.execute_checks_parallel(
            check_item_ids=["BD-001", "BD-002"],
            document_content=document_content,
            document_type="basic_design",
            max_concurrency=2,
        )
        
        assert len(results) == 2


# ==============================================
# ReviewEngine Tests
# ==============================================

class TestReviewEngine:
    """ReviewEngineテスト"""
    
    def test_create_engine(self):
        """エンジンを作成できること"""
        from src.review.engine import ReviewEngine
        
        engine = ReviewEngine(use_llm=False)
        
        assert engine is not None
    
    def test_create_engine_factory(self):
        """ファクトリ関数でエンジンを作成"""
        from src.review.engine import create_review_engine
        
        engine = create_review_engine(use_llm=False)
        
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_review_document_basic_design(self):
        """基本設計書のレビュー"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-001",
            document_content="""
            # 基本設計書
            
            ## システム概要
            本システムは文書レビュー支援AIです。
            
            ## システム構成
            ...
            
            ## 機能設計
            ...
            """,
            document_type="basic_design",
        )
        
        result = await engine.review_document(request)
        
        assert result.review_id.startswith("review-")
        assert result.status == ReviewStatus.COMPLETED
        assert result.metadata.checks_executed > 0
    
    @pytest.mark.asyncio
    async def test_review_document_test_plan(self):
        """テスト計画書のレビュー"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-002",
            document_content="""
            # テスト計画書
            
            ## テスト範囲
            本テストでは以下を対象とします。
            
            ## テスト環境
            ...
            """,
            document_type="test_plan",
        )
        
        result = await engine.review_document(request)
        
        assert result.status == ReviewStatus.COMPLETED
        assert result.document_type == "test_plan"
    
    @pytest.mark.asyncio
    async def test_review_document_with_specific_checks(self):
        """特定チェック項目のみ実行"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-003",
            document_content="# 基本設計書",
            document_type="basic_design",
            check_item_ids=["BD-001"],
        )
        
        result = await engine.review_document(request)
        
        # BD-001のみ実行されていること
        assert result.metadata.checks_executed == 1
    
    @pytest.mark.asyncio
    async def test_review_document_no_check_items(self):
        """該当チェック項目なしの場合"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-004",
            document_content="# Unknown Document",
            document_type="basic_design",
            check_item_ids=["NONEXISTENT-999"],
        )
        
        result = await engine.review_document(request)
        
        assert result.status == ReviewStatus.FAILED
        assert result.metadata.checks_executed == 0
    
    @pytest.mark.asyncio
    async def test_review_document_sequential(self):
        """順次実行モード"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewOptions
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-005",
            document_content="# 基本設計書\n\n## システム概要\n...",
            document_type="basic_design",
            options=ReviewOptions(parallel=False),
        )
        
        result = await engine.review_document(request)
        
        assert result.metadata.checks_executed > 0
    
    @pytest.mark.asyncio
    async def test_review_document_streaming(self):
        """ストリーミングレビュー"""
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewProgress, ReviewResult
        
        engine = ReviewEngine(use_llm=False)
        
        request = ReviewRequest(
            document_id="doc-test-006",
            document_content="# 基本設計書\n\n## システム概要\n...",
            document_type="basic_design",
            check_item_ids=["BD-001", "BD-002"],
        )
        
        progress_updates = []
        final_result = None
        
        async for update in engine.review_document_streaming(request):
            if isinstance(update, ReviewProgress):
                progress_updates.append(update)
            elif isinstance(update, ReviewResult):
                final_result = update
        
        # 進捗更新があること
        assert len(progress_updates) >= 1
        
        # 最終結果があること
        assert final_result is not None
        assert final_result.review_id.startswith("review-")


# ==============================================
# Integration with Core Server Tests
# ==============================================

class TestCoreServerIntegration:
    """Core Server統合テスト"""
    
    @pytest.mark.asyncio
    async def test_review_document_tool_exists(self):
        """review_document toolが存在すること"""
        from src.servers.core.server import review_document
        
        assert review_document is not None
    
    @pytest.mark.asyncio
    async def test_review_document_tool_no_document(self):
        """存在しない文書のレビュー"""
        from src.servers.core.server import review_document
        
        with pytest.raises(ValueError, match="Document not found"):
            await review_document(
                document_id="nonexistent-doc",
            )


# ==============================================
# Rule-based Check Tests
# ==============================================

class TestRuleBasedChecks:
    """ルールベースチェックのテスト"""
    
    @pytest.mark.asyncio
    async def test_completeness_check(self):
        """完全性チェック"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        # 必須セクションがない文書
        document_content = """
        # 基本設計書
        
        ## 概要
        これはテストです。
        """
        
        result = await executor._default_check(
            document_content=document_content,
            check_item={
                "id": "TEST-001",
                "name": "Test Check",
                "category": "completeness",
                "severity": "high",
                "document_type": "basic_design",
            },
        )
        
        # 必須セクションがないのでFAIL
        assert result.status.value == "fail"
    
    @pytest.mark.asyncio
    async def test_consistency_check(self):
        """一貫性チェック"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        # 用語が不統一な文書
        document_content = """
        # 設計書
        
        ユーザは操作できます。
        ユーザーが確認します。
        """
        
        result = await executor._default_check(
            document_content=document_content,
            check_item={
                "id": "TEST-002",
                "name": "Consistency Check",
                "category": "consistency",
                "severity": "medium",
                "document_type": "basic_design",
            },
        )
        
        # 用語不統一があるのでWARNING
        assert result.status.value == "warning"
        assert len(result.findings) > 0
    
    @pytest.mark.asyncio
    async def test_terminology_check(self):
        """用語チェック"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        # 非推奨用語を含む文書
        document_content = """
        # 設計書
        
        パスワードを入力してください。
        """
        
        result = await executor._default_check(
            document_content=document_content,
            check_item={
                "id": "TEST-003",
                "name": "Terminology Check",
                "category": "terminology",
                "severity": "low",
                "document_type": "basic_design",
            },
        )
        
        # 非推奨用語があるのでWARNING
        assert result.status.value == "warning"
    
    @pytest.mark.asyncio
    async def test_structure_check_no_h1(self):
        """構造チェック（H1なし）"""
        from src.review.executor import CheckExecutor
        
        executor = CheckExecutor(use_llm=False)
        
        # H1見出しがない文書
        document_content = """
        ## セクション1
        内容
        
        ## セクション2
        内容
        """
        
        result = await executor._default_check(
            document_content=document_content,
            check_item={
                "id": "TEST-004",
                "name": "Structure Check",
                "category": "structure",
                "severity": "medium",
                "document_type": "basic_design",
            },
        )
        
        # H1がないのでFAIL
        assert result.status.value == "fail"
