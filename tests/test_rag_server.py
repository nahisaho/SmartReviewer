"""
SmartReviewer RAG Server Tests
==============================

smartreviewer-ragサーバーの単体テスト
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.servers.rag.server import (
    app,
    EmbeddingResult,
    SearchResult,
    HybridResult,
    compute_embedding,
    _embedding_cache,
)


# =============================================================================
# Pydantic Model Tests
# =============================================================================

class TestPydanticModels:
    """Pydanticモデルテスト"""
    
    def test_embedding_result(self):
        """EmbeddingResult"""
        result = EmbeddingResult(
            text="テスト文",
            vector_id="vec-001",
            collection="guidelines",
            dimensions=1024,
            model="e5-large",
        )
        
        assert result.text == "テスト文"
        assert result.dimensions == 1024
    
    def test_search_result(self):
        """SearchResult"""
        result = SearchResult(
            id="doc-001",
            score=0.95,
            text="検索結果テキスト",
            metadata={"source": "guideline"},
        )
        
        assert result.id == "doc-001"
        assert result.score == 0.95
    
    def test_hybrid_result(self):
        """HybridResult"""
        result = HybridResult(
            id="doc-001",
            score=0.85,
            vector_score=0.9,
            keyword_score=0.7,
            text="ハイブリッド検索結果",
            metadata={},
        )
        
        assert result.vector_score > result.keyword_score


# =============================================================================
# Embedding Tests
# =============================================================================

class TestEmbedding:
    """埋め込み機能テスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """テスト前のセットアップ"""
        _embedding_cache.clear()
    
    @patch('src.servers.rag.server.get_embedding_model')
    @patch('src.servers.rag.server.settings')
    def test_compute_embedding_cached(self, mock_settings, mock_get_model):
        """埋め込みキャッシュテスト"""
        mock_settings.embedding.model_name = "e5-large"
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.1] * 1024)
        mock_get_model.return_value = mock_model
        
        # 1回目の呼び出し
        result1 = compute_embedding("テスト", use_cache=True)
        assert len(result1) == 1024
        
        # 2回目の呼び出し（キャッシュから）
        result2 = compute_embedding("テスト", use_cache=True)
        
        # モデルは1回だけ呼ばれる
        assert mock_model.encode.call_count == 1
        assert result1 == result2
    
    @patch('src.servers.rag.server.get_embedding_model')
    @patch('src.servers.rag.server.settings')
    def test_compute_embedding_no_cache(self, mock_settings, mock_get_model):
        """キャッシュなし埋め込みテスト"""
        mock_settings.embedding.model_name = "e5-large"
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [0.2] * 1024)
        mock_get_model.return_value = mock_model
        
        # キャッシュ無効
        compute_embedding("テスト1", use_cache=False)
        compute_embedding("テスト2", use_cache=False)
        
        # 両方呼ばれる
        assert mock_model.encode.call_count == 2


# =============================================================================
# Tool Tests (Mocked)
# =============================================================================

class TestRAGTools:
    """RAGツールテスト（モック使用）"""
    
    @pytest.mark.asyncio
    async def test_embed_document(self):
        """embed_documentテスト（コレクションが存在しない場合のエラー確認）"""
        from src.servers.rag.server import embed_document
        
        with patch('src.servers.rag.server.get_qdrant_client') as mock_client:
            mock_qdrant = MagicMock()
            # コレクションが存在しない場合
            mock_qdrant.get_collections.return_value = MagicMock(collections=[])
            mock_client.return_value = mock_qdrant
            
            result = await embed_document(
                document_id="doc-001",
                chunks=[{"text": "テスト", "metadata": {}}],
                collection="nonexistent",
            )
            
            # コレクションが存在しないのでエラー
            assert result["success"] is False
            assert "not found" in result["error"]
    
    @pytest.mark.skipif(True, reason="Requires qdrant-client package")
    @pytest.mark.asyncio
    async def test_embed_document_success(self):
        """embed_documentテスト（成功ケース）- qdrant-client依存"""
        pass
    
    @pytest.mark.asyncio
    @patch('src.servers.rag.server.get_qdrant_client')
    @patch('src.servers.rag.server.compute_embedding')
    async def test_vector_search(self, mock_embed, mock_client):
        """vector_searchテスト"""
        from src.servers.rag.server import vector_search
        
        # モック設定
        mock_embed.return_value = [0.1] * 1024
        mock_qdrant = MagicMock()
        mock_qdrant.search.return_value = [
            MagicMock(
                id="hit-001",
                score=0.95,
                payload={"text": "結果1", "source": "guideline"},
            ),
            MagicMock(
                id="hit-002",
                score=0.85,
                payload={"text": "結果2", "source": "guideline"},
            ),
        ]
        mock_client.return_value = mock_qdrant
        
        result = await vector_search(
            query="テストクエリ",
            collection="guidelines",
            top_k=5,
        )
        
        assert result["success"] is True
        assert result["total"] == 2
        assert result["results"][0]["score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_hybrid_retrieve(self):
        """hybrid_retrieveテスト"""
        from src.servers.rag.server import hybrid_retrieve
        
        # vector_searchとget_qdrant_clientをモック
        with patch('src.servers.rag.server.vector_search', new_callable=AsyncMock) as mock_vector_search, \
             patch('src.servers.rag.server.get_qdrant_client') as mock_client:
            
            mock_client.return_value = MagicMock()
            mock_vector_search.return_value = {
                "success": True,
                "results": [
                    {
                        "id": "doc-001",
                        "score": 0.9,
                        "text": "テスト クエリ 関連文書",
                        "metadata": {},
                    },
                    {
                        "id": "doc-002",
                        "score": 0.8,
                        "text": "別の文書内容",
                        "metadata": {},
                    },
                ],
            }
            
            result = await hybrid_retrieve(
                query="テスト クエリ",
                collection="guidelines",
                top_k=5,
            )
            
            assert result["success"] is True
            # doc-001はキーワードマッチも高いのでスコアが高くなる
            assert result["results"][0]["vector_score"] == 0.9
    
    @pytest.mark.asyncio
    @patch('src.servers.rag.server.hybrid_retrieve')
    async def test_get_related_guidelines(self, mock_hybrid):
        """get_related_guidelinesテスト"""
        from src.servers.rag.server import get_related_guidelines
        
        # モック設定
        mock_hybrid.return_value = {
            "success": True,
            "results": [
                {
                    "id": "guide-001",
                    "score": 0.85,
                    "text": "関連ガイドライン",
                    "metadata": {},
                },
            ],
        }
        
        result = await get_related_guidelines(
            check_item_id="BD-001",
            top_k=5,
        )
        
        assert result["success"] is True
        assert result["check_item_id"] == "BD-001"
        assert len(result["related_guidelines"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_related_guidelines_not_found(self):
        """get_related_guidelines（存在しないチェック項目）"""
        from src.servers.rag.server import get_related_guidelines
        
        result = await get_related_guidelines(
            check_item_id="NONEXISTENT-001",
            top_k=5,
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
