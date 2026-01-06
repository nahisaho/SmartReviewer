"""
SmartReviewer RAG Server
========================

RAG（Retrieval-Augmented Generation）サーバー
- ベクトル検索（Qdrant）
- ハイブリッド検索
- 埋め込み生成
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, UTC
import hashlib

from src.shared.config.settings import settings
from src.shared.config.clients import get_qdrant_client
from src.knowledge.schema import CHECK_ITEMS_DATA


# ==============================================
# Pydantic Models
# ==============================================

class EmbeddingResult(BaseModel):
    """埋め込みベクトル生成結果"""
    text: str = Field(description="入力テキスト")
    vector_id: str = Field(description="ベクトルID")
    collection: str = Field(description="保存先コレクション")
    dimensions: int = Field(description="ベクトル次元数")
    model: str = Field(description="使用モデル")


class SearchResult(BaseModel):
    """検索結果"""
    id: str = Field(description="ドキュメントID")
    score: float = Field(description="類似度スコア")
    text: str = Field(description="テキスト内容")
    metadata: dict = Field(default_factory=dict, description="メタデータ")


class HybridResult(BaseModel):
    """ハイブリッド検索結果"""
    id: str = Field(description="ドキュメントID")
    score: float = Field(description="統合スコア")
    vector_score: float = Field(description="ベクトル検索スコア")
    keyword_score: float = Field(description="キーワード検索スコア")
    text: str = Field(description="テキスト内容")
    metadata: dict = Field(default_factory=dict, description="メタデータ")


# ==============================================
# Embedding Cache (In-memory for PoC)
# ==============================================

_embedding_cache: dict[str, list[float]] = {}
_embedding_model = None


def get_embedding_model():
    """埋め込みモデルを取得（遅延ロード）"""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(settings.embedding.model_name)
        except ImportError:
            raise RuntimeError("sentence-transformers is not installed")
    return _embedding_model


def compute_embedding(text: str, use_cache: bool = True) -> list[float]:
    """テキストの埋め込みベクトルを計算"""
    cache_key = hashlib.md5(text.encode()).hexdigest()
    
    if use_cache and cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    model = get_embedding_model()
    
    # E5モデル用プレフィックス
    if "e5" in settings.embedding.model_name.lower():
        text = f"query: {text}"
    
    vector = model.encode(text, normalize_embeddings=True).tolist()
    
    if use_cache:
        _embedding_cache[cache_key] = vector
    
    return vector


# ==============================================
# FastMCP Server
# ==============================================

app = FastMCP("smartreviewer-rag")


# ==============================================
# Tools
# ==============================================

@app.tool()
async def embed_document(
    document_id: str,
    chunks: list[dict],
    collection: str = "guidelines",
) -> dict:
    """
    文書チャンクを埋め込みベクトル化してQdrantに保存
    
    Args:
        document_id: 文書ID
        chunks: チャンクのリスト（各チャンクは text, metadata を含む）
        collection: 保存先コレクション名
    
    Returns:
        埋め込み結果のサマリー
    """
    try:
        client = get_qdrant_client()
        
        # コレクション存在確認
        collections = [c.name for c in client.get_collections().collections]
        if collection not in collections:
            return {
                "success": False,
                "error": f"Collection not found: {collection}",
            }
        
        points = []
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {})
            
            # 埋め込み計算
            vector = compute_embedding(text)
            
            # ポイントID生成
            point_id = hashlib.md5(f"{document_id}:{i}".encode()).hexdigest()[:16]
            
            from qdrant_client.models import PointStruct
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": text,
                    **metadata,
                },
            ))
        
        # バッチアップロード
        if points:
            client.upsert(
                collection_name=collection,
                points=points,
            )
        
        return {
            "success": True,
            "document_id": document_id,
            "collection": collection,
            "chunks_embedded": len(points),
            "model": settings.embedding.model_name,
            "dimensions": settings.embedding.vector_size,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def vector_search(
    query: str,
    collection: str = "guidelines",
    top_k: int = 10,
    score_threshold: float = 0.5,
    filters: Optional[dict] = None,
) -> dict:
    """
    ベクトル類似検索を実行
    
    Args:
        query: 検索クエリ
        collection: 検索対象コレクション
        top_k: 取得件数
        score_threshold: 最低スコア閾値
        filters: フィルタ条件（Qdrant filter形式）
    
    Returns:
        検索結果リスト
    """
    try:
        client = get_qdrant_client()
        
        # クエリの埋め込み
        query_vector = compute_embedding(query)
        
        # フィルタ構築
        search_filter = None
        if filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            conditions = []
            for key, value in filters.items():
                conditions.append(FieldCondition(
                    key=key,
                    match=MatchValue(value=value),
                ))
            search_filter = Filter(must=conditions)
        
        # 検索実行
        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )
        
        # 結果整形
        search_results = []
        for hit in results:
            search_results.append({
                "id": str(hit.id),
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "metadata": {
                    k: v for k, v in hit.payload.items() if k != "text"
                },
            })
        
        return {
            "success": True,
            "query": query,
            "collection": collection,
            "total": len(search_results),
            "results": search_results,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def hybrid_retrieve(
    query: str,
    collection: str = "guidelines",
    top_k: int = 10,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    filters: Optional[dict] = None,
) -> dict:
    """
    ハイブリッド検索（ベクトル + キーワード）を実行
    
    Args:
        query: 検索クエリ
        collection: 検索対象コレクション
        top_k: 取得件数
        vector_weight: ベクトル検索の重み
        keyword_weight: キーワード検索の重み
        filters: フィルタ条件
    
    Returns:
        ハイブリッド検索結果
    """
    try:
        client = get_qdrant_client()
        
        # 1. ベクトル検索
        vector_results = await vector_search(
            query=query,
            collection=collection,
            top_k=top_k * 2,  # より多く取得して後でマージ
            score_threshold=0.3,
            filters=filters,
        )
        
        if not vector_results.get("success"):
            return vector_results
        
        # 2. キーワードスコアリング（シンプルなBM25代替）
        query_terms = set(query.lower().split())
        
        hybrid_results = []
        for result in vector_results.get("results", []):
            text = result.get("text", "").lower()
            text_terms = set(text.split())
            
            # キーワードスコア計算（Jaccard類似度ベース）
            if text_terms:
                intersection = len(query_terms & text_terms)
                keyword_score = intersection / len(query_terms) if query_terms else 0
            else:
                keyword_score = 0
            
            # ハイブリッドスコア計算
            vector_score = result.get("score", 0)
            hybrid_score = (
                vector_weight * vector_score + 
                keyword_weight * keyword_score
            )
            
            hybrid_results.append({
                "id": result["id"],
                "score": hybrid_score,
                "vector_score": vector_score,
                "keyword_score": keyword_score,
                "text": result.get("text", ""),
                "metadata": result.get("metadata", {}),
            })
        
        # スコアでソートして上位k件
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        hybrid_results = hybrid_results[:top_k]
        
        return {
            "success": True,
            "query": query,
            "collection": collection,
            "weights": {
                "vector": vector_weight,
                "keyword": keyword_weight,
            },
            "total": len(hybrid_results),
            "results": hybrid_results,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def get_related_guidelines(
    check_item_id: str,
    top_k: int = 5,
) -> dict:
    """
    チェック項目に関連するガイドラインを取得
    
    Args:
        check_item_id: チェック項目ID
        top_k: 取得件数
    
    Returns:
        関連ガイドラインリスト
    """
    try:
        # チェック項目情報を取得
        check_item = None
        for item in CHECK_ITEMS_DATA:
            if item["id"] == check_item_id:
                check_item = item
                break
        
        if not check_item:
            return {
                "success": False,
                "error": f"Check item not found: {check_item_id}",
            }
        
        # 検索クエリ構築
        query = f"{check_item['name']} {check_item['description']}"
        
        # ガイドラインコレクションを検索
        results = await hybrid_retrieve(
            query=query,
            collection="guidelines",
            top_k=top_k,
        )
        
        if not results.get("success"):
            return results
        
        return {
            "success": True,
            "check_item_id": check_item_id,
            "check_item_name": check_item["name"],
            "guideline_section": check_item.get("guideline_section", ""),
            "related_guidelines": results.get("results", []),
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def find_similar_documents(
    document_id: str,
    collection: str = "documents",
    top_k: int = 5,
) -> dict:
    """
    類似文書を検索
    
    Args:
        document_id: 基準文書ID
        collection: 検索対象コレクション
        top_k: 取得件数
    
    Returns:
        類似文書リスト
    """
    try:
        client = get_qdrant_client()
        
        # 対象文書のベクトルを取得
        doc_points = client.scroll(
            collection_name=collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
            limit=1,
            with_vectors=True,
        )
        
        if not doc_points[0]:
            return {
                "success": False,
                "error": f"Document not found in collection: {document_id}",
            }
        
        source_vector = doc_points[0][0].vector
        
        # 類似検索（自分自身を除外）
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        results = client.search(
            collection_name=collection,
            query_vector=source_vector,
            limit=top_k + 1,  # 自分自身を除外するため+1
            query_filter=Filter(
                must_not=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        
        similar_docs = []
        for hit in results[:top_k]:
            similar_docs.append({
                "id": str(hit.id),
                "document_id": hit.payload.get("document_id", ""),
                "score": hit.score,
                "title": hit.payload.get("title", ""),
                "metadata": hit.payload,
            })
        
        return {
            "success": True,
            "source_document_id": document_id,
            "collection": collection,
            "similar_documents": similar_docs,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ==============================================
# Resources
# ==============================================

@app.resource("rag://collections")
async def list_collections() -> str:
    """利用可能なコレクション一覧"""
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        
        result = "# Available Collections\n\n"
        for col in collections:
            info = client.get_collection(col.name)
            result += f"## {col.name}\n"
            result += f"- Points: {info.points_count}\n"
            result += f"- Vectors: {info.vectors_count}\n"
            result += "\n"
        
        return result
    
    except Exception as e:
        return f"Error: {str(e)}"


@app.resource("rag://collections/{collection_name}")
async def get_collection_info(collection_name: str) -> str:
    """コレクション詳細情報"""
    try:
        client = get_qdrant_client()
        info = client.get_collection(collection_name)
        
        result = f"# Collection: {collection_name}\n\n"
        result += f"- Status: {info.status}\n"
        result += f"- Points Count: {info.points_count}\n"
        result += f"- Vectors Count: {info.vectors_count}\n"
        result += f"- Indexed Vectors: {info.indexed_vectors_count}\n"
        result += f"\n## Config\n"
        result += f"- Vector Size: {info.config.params.vectors.size}\n"
        result += f"- Distance: {info.config.params.vectors.distance}\n"
        
        return result
    
    except Exception as e:
        return f"Error: {str(e)}"


@app.resource("rag://embedding-model")
async def get_embedding_model_info() -> str:
    """埋め込みモデル情報"""
    return f"""# Embedding Model

- Model: {settings.embedding.model_name}
- Dimensions: {settings.embedding.vector_size}
- Cache Size: {len(_embedding_cache)} entries
"""


# ==============================================
# Server Entry Point
# ==============================================

def create_server():
    """サーバーインスタンスを作成"""
    return app


if __name__ == "__main__":
    app.run()
