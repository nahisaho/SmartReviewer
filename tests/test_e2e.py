"""
End-to-End Tests for SmartReviewer
==================================

システム全体の統合テスト
- 文書レビューワークフロー
- MCP Server連携
- CLI操作
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


# ==============================================
# Sample Documents
# ==============================================

SAMPLE_BASIC_DESIGN = """
# 基本設計書

## システム概要

### システム名称
SmartReviewer - 文書レビュー支援AIシステム

### 目的
本システムは、設計文書のレビュープロセスを自動化・効率化することを目的とする。
デジタル庁ドキュメント標準ガイドラインに準拠したレビューを実現する。

### 背景
従来のレビュープロセスは人的リソースに依存しており、品質のばらつきが課題であった。

## システム構成

### アーキテクチャ概要
マイクロサービスアーキテクチャを採用し、以下のコンポーネントで構成する。

```
┌─────────────────┐    ┌─────────────────┐
│  MCP Host       │────│  MCP Servers    │
│  (CLI/API)      │    │  (Core/RAG/KG)  │
└─────────────────┘    └─────────────────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌─────────────────────┐
        │    Knowledge Base   │
        │  (Qdrant + Neo4j)   │
        └─────────────────────┘
```

### 構成要素
- MCP Host: クライアントアプリケーション
- MCP Servers: 機能提供サーバー群
- Knowledge Base: ベクトルDB + グラフDB

## 機能設計

### 機能一覧
| ID | 機能名 | 概要 |
|----|--------|------|
| F001 | 文書アップロード | レビュー対象文書を登録 |
| F002 | レビュー実行 | チェック項目に基づくレビュー |
| F003 | レポート生成 | レビュー結果をレポート化 |
| F004 | ガイドライン検索 | 関連ガイドラインを検索 |

### 機能詳細
各機能はMCP Toolとして実装し、プロトコルに準拠した呼び出しを可能とする。

## データ設計

### データモデル
```mermaid
erDiagram
    DOCUMENT ||--o{ SECTION : contains
    DOCUMENT ||--o{ REVIEW_RESULT : has
    CHECK_ITEM ||--o{ FINDING : generates
```

### データベース
- PostgreSQL: 文書メタデータ
- Qdrant: ベクトル埋め込み
- Neo4j: ナレッジグラフ

## インターフェース設計

### 外部インターフェース
- MCP Protocol: JSON-RPC 2.0 over stdio
- REST API: HTTP/JSON (将来拡張)

### 内部インターフェース
- サーバー間通信: MCP Protocol
- DB接続: 各DBネイティブプロトコル

## 非機能設計

### 性能要件
- レビュー応答時間: 30秒以内（1文書あたり）
- 同時処理: 10文書まで

### 可用性
- 稼働率: 99.5%以上

### セキュリティ
- 認証: OAuth 2.0対応（将来）
- 暗号化: TLS 1.3
"""

SAMPLE_INCOMPLETE_DESIGN = """
# 基本設計書

## システム概要
これはテストシステムです。

## システム構成
マイクロサービス構成です。
"""

SAMPLE_TEST_PLAN = """
# テスト計画書

## 概要

### 目的
本文書はSmartReviewerシステムのテスト計画を定義する。

### 対象システム
SmartReviewer v2.0

### テスト期間
2024年7月1日 - 2024年7月31日

## テストレベル

### 単体テスト
- 対象: 各モジュール
- 担当: 開発チーム
- 完了基準: カバレッジ80%以上

### 結合テスト
- 対象: コンポーネント間連携
- 担当: QAチーム
- 完了基準: 全シナリオ合格

### システムテスト
- 対象: システム全体
- 担当: QAチーム
- 完了基準: 全テストケース合格

## テスト種別

### 機能テスト
機能要件に基づくテストを実施する。

### 性能テスト
性能要件を満たすことを確認する。

### セキュリティテスト
脆弱性診断を実施する。

## テスト環境

### 環境構成
- 開発環境: ローカルDockerコンテナ
- テスト環境: クラウドインスタンス
- ステージング環境: 本番相当構成

### 環境準備
テスト実施前に環境構築手順書に従い準備する。

## テストスケジュール

| フェーズ | 開始日 | 終了日 |
|---------|--------|--------|
| 単体テスト | 7/1 | 7/10 |
| 結合テスト | 7/11 | 7/20 |
| システムテスト | 7/21 | 7/31 |

## 合格基準

### 全体合格基準
- 致命的バグ: 0件
- 重大バグ: 未解決0件
- テストカバレッジ: 80%以上

### リリース判定
合格基準を満たした場合、リリース判定会議にてリリース可否を決定する。
"""


# ==============================================
# End-to-End Workflow Tests
# ==============================================

class TestEndToEndWorkflow:
    """End-to-Endワークフローテスト"""
    
    def test_complete_review_workflow(self):
        """完全なレビューワークフロー"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus, ReviewResult
        
        async def run_workflow():
            # 1. エンジン初期化
            engine = ReviewEngine(use_llm=False)
            
            # 2. レビューリクエスト作成
            request = ReviewRequest(
                document_id="e2e-test-doc",
                document_content=SAMPLE_BASIC_DESIGN,
                document_type="basic_design",
            )
            
            # 3. レビュー実行
            result = await engine.review_document(request)
            
            # 4. 結果検証
            assert isinstance(result, ReviewResult)
            assert result.status == ReviewStatus.COMPLETED
            assert result.document_id == "e2e-test-doc"
            assert result.document_type == "basic_design"
            assert result.check_results is not None
            assert len(result.check_results) > 0
            
            return result
        
        result = asyncio.run(run_workflow())
        
        # 詳細検証
        assert result.metadata.checks_executed > 0
        # execution_time_msは高速すぎて0になる場合がある
    
    def test_incomplete_document_detection(self):
        """不完全な文書の検出"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, CheckResultStatus
        
        async def run_review():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="incomplete-doc",
                document_content=SAMPLE_INCOMPLETE_DESIGN,
                document_type="basic_design",
            )
            
            return await engine.review_document(request)
        
        result = asyncio.run(run_review())
        
        # 不完全な文書では失敗するチェックがあるはず
        failed_checks = [
            r for r in result.check_results
            if r.status == CheckResultStatus.FAIL
        ]
        
        # 必須セクション不足で失敗しているはず
        assert len(failed_checks) > 0 or result.metadata.checks_warning > 0
    
    def test_test_plan_review(self):
        """テスト計画書レビュー"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus
        
        async def run_review():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="test-plan-doc",
                document_content=SAMPLE_TEST_PLAN,
                document_type="test_plan",
            )
            
            return await engine.review_document(request)
        
        result = asyncio.run(run_review())
        
        assert result.status == ReviewStatus.COMPLETED
        assert result.document_type == "test_plan"
    
    def test_streaming_review(self):
        """ストリーミングレビュー"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewProgress, ReviewResult
        
        async def run_streaming():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="stream-doc",
                document_content=SAMPLE_BASIC_DESIGN,
                document_type="basic_design",
            )
            
            progress_updates = []
            
            async for progress in engine.review_document_streaming(request):
                progress_updates.append(progress)
            
            return progress_updates
        
        updates = asyncio.run(run_streaming())
        
        # 最低1つは進捗更新がある
        assert len(updates) >= 1
        
        # 最後は完了状態（ReviewProgressまたはReviewResult）
        final_progress = updates[-1]
        if isinstance(final_progress, ReviewProgress):
            assert final_progress.is_final
        else:
            # ReviewResultの場合は成功を確認
            assert isinstance(final_progress, ReviewResult)


# ==============================================
# MCP Server Integration Tests
# ==============================================

class TestMCPServerIntegration:
    """MCP Server統合テスト"""
    
    def test_core_server_tools(self):
        """Core Serverのツール確認"""
        from src.servers.core import server
        
        # 必須関数が存在すること
        assert hasattr(server, 'upload_document')
        assert hasattr(server, 'review_document')
        assert hasattr(server, 'get_check_items')
    
    def test_rag_server_tools(self):
        """RAG Serverのツール確認"""
        from src.servers.rag import server
        
        assert hasattr(server, 'vector_search')
        assert hasattr(server, 'hybrid_retrieve')
        assert hasattr(server, 'embed_document')
    
    def test_knowledge_server_tools(self):
        """Knowledge Serverのツール確認"""
        from src.servers.knowledge import server
        
        assert hasattr(server, 'get_check_item_detail')
        assert hasattr(server, 'get_schema')
        assert hasattr(server, 'traverse_graph')
    
    def test_all_servers_importable(self):
        """全サーバーがインポートできること"""
        from src.servers.core import server as core_server
        from src.servers.rag import server as rag_server
        from src.servers.knowledge import server as knowledge_server
        
        # 各サーバーがFastMCPアプリを持つこと
        assert hasattr(core_server, 'app')
        assert hasattr(rag_server, 'app')
        assert hasattr(knowledge_server, 'app')


# ==============================================
# CLI Integration Tests
# ==============================================

class TestCLIIntegration:
    """CLI統合テスト"""
    
    def test_cli_review_complete_document(self, tmp_path):
        """CLIで完全な文書をレビュー"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        # テスト文書作成
        doc_file = tmp_path / "basic_design.md"
        doc_file.write_text(SAMPLE_BASIC_DESIGN)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "review", str(doc_file),
            "--type", "basic_design",
            "--format", "markdown",
        ])
        
        # レビューが完了すること
        assert "レビュー結果" in result.stdout
    
    def test_cli_review_test_plan(self, tmp_path):
        """CLIでテスト計画書をレビュー"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        doc_file = tmp_path / "test_plan.md"
        doc_file.write_text(SAMPLE_TEST_PLAN)
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "review", str(doc_file),
            "--type", "test_plan",
        ])
        
        assert "レビュー結果" in result.stdout
    
    def test_cli_review_json_output(self, tmp_path):
        """CLIでJSONレポート出力"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        doc_file = tmp_path / "design.md"
        doc_file.write_text(SAMPLE_BASIC_DESIGN)
        
        output_file = tmp_path / "report.json"
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "review", str(doc_file),
            "--type", "basic_design",
            "--format", "json",
            "--output", str(output_file),
        ])
        
        # JSONファイルが作成されていること
        assert output_file.exists()
        
        # 有効なJSONであること
        report = json.loads(output_file.read_text())
        assert "review_id" in report
        assert "status" in report


# ==============================================
# Check Items Integration Tests
# ==============================================

class TestCheckItemsIntegration:
    """チェック項目統合テスト"""
    
    def test_all_check_items_have_required_fields(self):
        """全チェック項目が必須フィールドを持つこと"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        required_fields = ["id", "name", "description", "category", "severity", "document_type"]
        
        for item in CHECK_ITEMS_DATA:
            for field in required_fields:
                assert field in item, f"Item {item.get('id', 'unknown')} missing field: {field}"
    
    def test_check_items_have_valid_document_types(self):
        """チェック項目が有効な文書タイプを持つこと"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        valid_types = ["basic_design", "test_plan"]
        
        for item in CHECK_ITEMS_DATA:
            assert item["document_type"] in valid_types, \
                f"Item {item['id']} has invalid document_type: {item['document_type']}"
    
    def test_check_items_have_valid_severities(self):
        """チェック項目が有効な重要度を持つこと"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        valid_severities = ["critical", "high", "medium", "low"]
        
        for item in CHECK_ITEMS_DATA:
            assert item["severity"] in valid_severities, \
                f"Item {item['id']} has invalid severity: {item['severity']}"
    
    def test_check_items_ids_unique(self):
        """チェック項目IDが一意であること"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        ids = [item["id"] for item in CHECK_ITEMS_DATA]
        assert len(ids) == len(set(ids)), "Duplicate check item IDs found"


# ==============================================
# Knowledge Schema Integration Tests
# ==============================================

class TestKnowledgeSchemaIntegration:
    """ナレッジスキーマ統合テスト"""
    
    def test_neo4j_schema_complete(self):
        """Neo4jスキーマが完全であること"""
        from src.knowledge.schema import Neo4jSchema
        
        assert "node_labels" in Neo4jSchema
        assert "relationship_types" in Neo4jSchema
        assert "constraints" in Neo4jSchema
        
        assert len(Neo4jSchema["node_labels"]) > 0
        assert len(Neo4jSchema["relationship_types"]) > 0
    
    def test_node_labels_defined(self):
        """ノードラベルが定義されていること"""
        from src.knowledge.schema import NodeLabel
        
        expected_labels = [
            "Document", "Section", "CheckItem", "Guideline",
        ]
        
        actual_labels = [label.value for label in NodeLabel]
        
        for label in expected_labels:
            assert label in actual_labels, f"Missing node label: {label}"
    
    def test_relationship_types_defined(self):
        """リレーションシップタイプが定義されていること"""
        from src.knowledge.schema import RelationType
        
        expected_types = [
            "HAS_SECTION", "CONTAINS", "APPLIES_TO", "BELONGS_TO",
        ]
        
        actual_types = [rel.value for rel in RelationType]
        
        for rel_type in expected_types:
            assert rel_type in actual_types, f"Missing relationship type: {rel_type}"


# ==============================================
# Review Engine Integration Tests
# ==============================================

class TestReviewEngineIntegration:
    """レビューエンジン統合テスト"""
    
    def test_executor_check_logic(self):
        """Executorのチェックロジック"""
        import asyncio
        from src.review.executor import CheckExecutor
        from src.review.models import CheckResultStatus
        
        async def run_check():
            executor = CheckExecutor(use_llm=False)
            
            document_content = SAMPLE_BASIC_DESIGN
            
            result = await executor.execute_check(
                check_item_id="BD-001",
                document_content=document_content,
                document_type="basic_design",
            )
            
            return result
        
        result = asyncio.run(run_check())
        
        assert result.check_item_id == "BD-001"
        assert result.status in [CheckResultStatus.PASS, CheckResultStatus.FAIL, CheckResultStatus.WARNING]
    
    def test_executor_parallel_execution(self):
        """Executor並列実行"""
        import asyncio
        from src.review.executor import CheckExecutor
        
        async def run_parallel():
            executor = CheckExecutor(use_llm=False)
            
            results = await executor.execute_checks_parallel(
                check_item_ids=["BD-001", "BD-002", "BD-003"],
                document_content=SAMPLE_BASIC_DESIGN,
                document_type="basic_design",
            )
            
            return results
        
        results = asyncio.run(run_parallel())
        
        assert len(results) == 3
        
        # 各結果が正しいチェック項目に対応していること
        result_ids = {r.check_item_id for r in results}
        assert result_ids == {"BD-001", "BD-002", "BD-003"}


# ==============================================
# Error Handling Tests
# ==============================================

class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    def test_invalid_document_type(self):
        """無効な文書タイプでエラー"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest
        
        async def run_with_invalid_type():
            engine = ReviewEngine(use_llm=False)
            
            # 無効な文書タイプを指定
            request = ReviewRequest(
                document_id="invalid-type-doc",
                document_content="Test content",
                document_type="invalid_type",
            )
            
            # エラーになるか、スキップされるかの動作
            return await engine.review_document(request)
        
        # エラーが発生するか、適切に処理されることを確認
        result = asyncio.run(run_with_invalid_type())
        
        # 結果が返されること（エラーでクラッシュしないこと）
        assert result is not None
    
    def test_empty_document(self):
        """空の文書でエラー"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest
        
        async def run_with_empty():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="empty-doc",
                document_content="",
                document_type="basic_design",
            )
            
            return await engine.review_document(request)
        
        result = asyncio.run(run_with_empty())
        
        # エラーでクラッシュしないこと
        assert result is not None


# ==============================================
# Configuration Integration Tests
# ==============================================

class TestConfigurationIntegration:
    """設定統合テスト"""
    
    def test_settings_structure(self):
        """設定構造の確認"""
        from src.shared.config.settings import get_settings
        
        settings = get_settings()
        
        # 必須設定の存在確認
        assert hasattr(settings, 'embedding')
        assert hasattr(settings, 'qdrant')  # vector_storeはqdrant設定
        assert hasattr(settings, 'llm')
        assert hasattr(settings, 'neo4j')
    
    def test_mcp_config_integration(self):
        """MCP設定の統合確認"""
        from src.host.config import load_mcp_config, get_default_config
        
        default_config = get_default_config()
        
        # デフォルト設定に3つのサーバーがあること
        assert len(default_config.servers) >= 3
        
        # 各サーバーが有効であること
        for name, server in default_config.servers.items():
            assert server.enabled
            assert server.command


# ==============================================
# Performance Tests
# ==============================================

class TestPerformance:
    """パフォーマンステスト"""
    
    def test_review_completes_in_time(self):
        """レビューが制限時間内に完了すること"""
        import asyncio
        import time
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest
        
        async def run_timed_review():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="perf-test-doc",
                document_content=SAMPLE_BASIC_DESIGN,
                document_type="basic_design",
            )
            
            start_time = time.time()
            result = await engine.review_document(request)
            elapsed = time.time() - start_time
            
            return result, elapsed
        
        result, elapsed = asyncio.run(run_timed_review())
        
        # 5秒以内に完了すること（ルールベースのみなので高速）
        assert elapsed < 5.0, f"Review took too long: {elapsed:.2f}s"
        
        # 結果も正常であること
        assert result is not None
