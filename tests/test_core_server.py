"""
SmartReviewer Core Server Tests
===============================

smartreviewer-coreサーバーの単体テスト
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.servers.core.server import (
    app,
    DocumentMetadata,
    CheckItem,
    CheckResult,
    ReviewResult,
    _documents,
    _review_results,
)
from src.servers.core.document_parser import (
    DocumentParser,
    DocumentStructure,
    Section,
    parse_document,
    check_required_sections,
    REQUIRED_SECTIONS_BASIC_DESIGN,
    REQUIRED_SECTIONS_TEST_PLAN,
)


# =============================================================================
# Document Parser Tests
# =============================================================================

class TestDocumentParser:
    """DocumentParser単体テスト"""
    
    def test_parse_markdown_heading(self):
        """Markdown見出しのパース"""
        parser = DocumentParser()
        
        # H1
        result = parser._parse_heading("# タイトル")
        assert result is not None
        assert result['level'] == 1
        assert result['title'] == "タイトル"
        
        # H2
        result = parser._parse_heading("## セクション2")
        assert result is not None
        assert result['level'] == 2
        
        # H3 with number
        result = parser._parse_heading("### 1.2.3 詳細")
        assert result is not None
        assert result['level'] == 3
        assert result['number'] == "1.2.3"
        assert result['title'] == "詳細"
    
    def test_parse_japanese_heading(self):
        """日本語番号付き見出しのパース"""
        parser = DocumentParser()
        
        # 第X章
        result = parser._parse_heading("第1章 システム概要")
        assert result is not None
        assert result['level'] == 1
        assert result['number'] == "1"
        assert result['title'] == "システム概要"
        
        # 第X節
        result = parser._parse_heading("第2節 機能設計")
        assert result is not None
        assert result['level'] == 2
    
    def test_parse_document_structure(self):
        """文書構造パース"""
        content = """# テスト文書

## 1. 概要

システムの概要を説明します。

## 2. 機能設計

### 2.1 機能一覧

機能Aの説明。

### 2.2 機能B

機能Bの説明。

## 3. まとめ

まとめです。
"""
        structure = parse_document(content)
        
        assert structure.title == "テスト文書"
        assert len(structure.sections) >= 5
        assert structure.total_lines > 0
    
    def test_get_toc(self):
        """目次生成"""
        content = """# ドキュメント

## 第1章

### 1.1 セクション

## 第2章
"""
        structure = parse_document(content)
        toc = structure.get_toc()
        
        assert len(toc) >= 3
        assert all('id' in item for item in toc)
        assert all('level' in item for item in toc)
    
    def test_section_tree(self):
        """セクションツリー構築"""
        content = """# 親

## 子1

### 孫1

## 子2
"""
        structure = parse_document(content)
        
        assert "root" in structure.section_tree
        assert len(structure.section_tree["root"]) >= 1


class TestRequiredSections:
    """必須セクションチェックテスト"""
    
    def test_basic_design_full_coverage(self):
        """基本設計書の完全カバレッジ"""
        content = """# 基本設計書

## 1. システム概要

概要説明です。

## 2. システム構成

アーキテクチャの説明。

## 3. 機能設計

機能一覧。

## 4. データ設計

データモデル。

## 5. インターフェース設計

API仕様。

## 6. 非機能設計

性能要件。
"""
        structure = parse_document(content)
        result = check_required_sections(structure, "basic_design")
        
        assert result['coverage'] >= 0.8  # 80%以上
    
    def test_basic_design_missing_sections(self):
        """基本設計書の欠落セクション検出"""
        content = """# 基本設計書

## 1. 概要

概要のみ。
"""
        structure = parse_document(content)
        result = check_required_sections(structure, "basic_design")
        
        assert result['missing'] > 0
        assert result['coverage'] < 1.0
    
    def test_test_plan_sections(self):
        """テスト計画書のセクションチェック"""
        content = """# テスト計画書

## 1. テスト方針

テストの方針。

## 2. テストスコープ

対象範囲。

## 3. テストレベル

単体・結合・システムテスト。

## 4. スケジュール

日程計画。
"""
        structure = parse_document(content)
        result = check_required_sections(structure, "test_plan")
        
        assert result['found'] >= 4
    
    def test_unknown_document_type(self):
        """未知の文書タイプ"""
        structure = parse_document("# Test")
        result = check_required_sections(structure, "unknown_type")
        
        assert 'error' in result


# =============================================================================
# Pydantic Model Tests
# =============================================================================

class TestPydanticModels:
    """Pydanticモデルテスト"""
    
    def test_document_metadata(self):
        """DocumentMetadata"""
        doc = DocumentMetadata(
            id="doc-001",
            filename="test.md",
            document_type="basic_design",
            uploaded_at="2024-01-01T00:00:00",
            file_size=100,
            content_hash="abc123",
            status="uploaded",
        )
        
        assert doc.id == "doc-001"
        assert doc.document_type == "basic_design"
        assert doc.file_size == 100
    
    def test_check_item(self):
        """CheckItem"""
        item = CheckItem(
            id="BD-001",
            name="概要確認",
            document_type="basic_design",
            category="completeness",
            description="概要セクションの存在確認",
            severity="error",
        )
        
        assert item.id == "BD-001"
        assert item.severity == "error"
    
    def test_check_result(self):
        """CheckResult"""
        result = CheckResult(
            check_item_id="BD-001",
            result="fail",
            confidence=0.95,
            evidence="概要セクションが見つかりません",
        )
        
        assert result.result == "fail"
        assert result.confidence == 0.95
    
    def test_review_result(self):
        """ReviewResult"""
        review = ReviewResult(
            id="review-001",
            document_id="doc-001",
            document_type="basic_design",
            status="completed",
            created_at="2024-01-01T00:00:00",
            total_checks=10,
            passed=8,
            failed=1,
            warnings=1,
            skipped=0,
            check_results=[
                CheckResult(
                    check_item_id="BD-001",
                    result="pass",
                    confidence=0.99,
                ),
                CheckResult(
                    check_item_id="BD-002",
                    result="fail",
                    confidence=0.85,
                ),
            ],
        )
        
        assert len(review.check_results) == 2
        assert review.passed == 8
        assert review.failed == 1


# =============================================================================
# Server Tool Tests (Mocked)
# =============================================================================

class TestServerTools:
    """サーバーツールのテスト（モック使用）"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト前のセットアップ"""
        _documents.clear()
        _review_results.clear()
    
    @pytest.mark.asyncio
    async def test_upload_document_basic(self):
        """upload_document基本テスト"""
        from src.servers.core.server import upload_document
        
        content = """# テスト基本設計書

## 1. 概要

テストです。
"""
        
        result = await upload_document(
            filename="test.md",
            content=content,
            document_type="basic_design",
        )
        
        assert "document_id" in result
        assert result["success"] is True
        assert len(_documents) == 1
    
    @pytest.mark.asyncio
    async def test_get_check_items_basic_design(self):
        """get_check_items (basic_design)"""
        from src.servers.core.server import get_check_items
        
        result = await get_check_items(document_type="basic_design")
        
        assert "items" in result
        assert len(result["items"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_check_items_test_plan(self):
        """get_check_items (test_plan)"""
        from src.servers.core.server import get_check_items
        
        result = await get_check_items(document_type="test_plan")
        
        assert "items" in result
        assert len(result["items"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self):
        """list_documents（空）"""
        from src.servers.core.server import list_documents
        
        result = await list_documents()
        
        assert result["total"] == 0
        assert result["documents"] == []
    
    @pytest.mark.asyncio
    async def test_list_documents_with_data(self):
        """list_documents（データあり）"""
        from src.servers.core.server import upload_document, list_documents
        
        await upload_document(
            filename="doc1.md",
            content="# Doc1",
            document_type="basic_design",
        )
        await upload_document(
            filename="doc2.md",
            content="# Doc2",
            document_type="test_plan",
        )
        
        result = await list_documents()
        assert result["total"] == 2
        
        # フィルタリング
        result = await list_documents(document_type="basic_design")
        assert result["total"] == 1
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """get_document（存在しない場合はValueError）"""
        from src.servers.core.server import get_document
        
        with pytest.raises(ValueError):
            await get_document(document_id="nonexistent")
    
    @pytest.mark.asyncio
    async def test_get_document_found(self):
        """get_document（存在する）"""
        from src.servers.core.server import upload_document, get_document
        
        upload_result = await upload_document(
            filename="test.md",
            content="# Test",
            document_type="basic_design",
        )
        
        result = await get_document(document_id=upload_result["document_id"])
        
        assert result["filename"] == "test.md"
        assert result["document_type"] == "basic_design"
    
    @pytest.mark.asyncio
    async def test_create_report(self):
        """create_reportテスト"""
        from src.servers.core.server import upload_document, create_report
        
        upload_result = await upload_document(
            filename="report_test.md",
            content="""# 基本設計書

## 1. 概要

システムの概要。

## 2. システム構成

構成図。
""",
            document_type="basic_design",
        )
        
        check_results = [
            {
                "check_item_id": "BD-001",
                "result": "pass",
                "confidence": 0.95,
                "evidence": "概要セクションあり",
            }
        ]
        
        result = await create_report(
            document_id=upload_result["document_id"],
            check_results=check_results,
        )
        
        assert "review_id" in result
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_review_result_not_found(self):
        """get_review_result（存在しない場合はValueError）"""
        from src.servers.core.server import get_review_result
        
        with pytest.raises(ValueError):
            await get_review_result(review_id="nonexistent")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
