"""
Guideline to Knowledge Graph Transformer
=========================================

ガイドラインチャンクをナレッジグラフに変換・登録するパイプライン
Qdrant に格納されたチャンクを Neo4j ナレッジグラフにリンク
"""

import hashlib
from typing import Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from neo4j import GraphDatabase

from src.shared.config.settings import settings
from src.shared.config.clients import get_qdrant_client, get_neo4j_driver


@dataclass
class GuidelineChunkLink:
    """ガイドラインチャンクとナレッジグラフノードのリンク情報"""
    chunk_id: str
    qdrant_point_id: str
    neo4j_node_id: str
    section_number: str
    content_hash: str


class GuidelineKGTransformer:
    """ガイドラインをナレッジグラフに変換するクラス"""
    
    def __init__(self):
        self.qdrant_client = get_qdrant_client()
        self.neo4j_driver = get_neo4j_driver()
        self.collection_name = "guidelines"
    
    def close(self):
        """リソースを閉じる"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
    
    def _generate_chunk_id(self, content: str, section: str) -> str:
        """チャンクIDを生成"""
        hash_input = f"{section}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def transform_chunks_to_kg(self, batch_size: int = 100) -> int:
        """
        Qdrant のガイドラインチャンクを Neo4j ナレッジグラフに登録
        
        Args:
            batch_size: バッチサイズ
            
        Returns:
            処理されたチャンク数
        """
        print("Transforming guideline chunks to Knowledge Graph...")
        
        # Qdrant からチャンクを取得
        offset = None
        total_processed = 0
        
        while True:
            # スクロールでチャンクを取得
            points, offset = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            
            if not points:
                break
            
            # Neo4j にバッチ登録
            with self.neo4j_driver.session(database=settings.neo4j.database) as session:
                for point in points:
                    payload = point.payload
                    
                    chunk_id = self._generate_chunk_id(
                        payload.get("content", ""),
                        payload.get("section", "")
                    )
                    
                    # GuidelineChunk ノードを作成
                    create_query = """
                    MERGE (gc:GuidelineChunk {id: $id})
                    SET gc.qdrant_point_id = $qdrant_point_id,
                        gc.chunk_index = $chunk_index,
                        gc.section = $section,
                        gc.source = $source,
                        gc.content_preview = $content_preview,
                        gc.created_at = datetime()
                    RETURN gc
                    """
                    
                    session.run(
                        create_query,
                        id=chunk_id,
                        qdrant_point_id=str(point.id),
                        chunk_index=payload.get("chunk_index", 0),
                        section=payload.get("section", ""),
                        source=payload.get("source", ""),
                        content_preview=payload.get("content", "")[:200],
                    )
                    
                    # GuidelineSection にリンク
                    section_number = payload.get("section", "")
                    if section_number:
                        link_query = """
                        MATCH (gc:GuidelineChunk {id: $chunk_id})
                        MATCH (gs:GuidelineSection)
                        WHERE gs.section_number CONTAINS $section_pattern
                        MERGE (gs)-[:CONTAINS]->(gc)
                        RETURN gs.id as section_id
                        """
                        
                        # セクション番号のパターンマッチ
                        section_pattern = section_number.split(" ")[0] if " " in section_number else section_number
                        
                        result = session.run(
                            link_query,
                            chunk_id=chunk_id,
                            section_pattern=section_pattern
                        )
                        
                        # デバッグ出力
                        record = result.single()
                        if record:
                            print(f"  Linked chunk {chunk_id} to section {record['section_id']}")
                    
                    total_processed += 1
            
            print(f"  Processed {total_processed} chunks...")
            
            if offset is None:
                break
        
        print(f"Total chunks transformed: {total_processed}")
        return total_processed
    
    def link_chunks_to_check_items(self):
        """
        ガイドラインチャンクを関連するチェック項目にリンク
        セマンティック検索で関連度の高いチャンクを特定
        """
        print("\nLinking chunks to check items...")
        
        # チェック項目を取得
        with self.neo4j_driver.session(database=settings.neo4j.database) as session:
            result = session.run("""
                MATCH (ci:CheckItem)
                RETURN ci.id as id, ci.name as name, ci.description as description,
                       ci.guideline_section as guideline_section
            """)
            check_items = [dict(record) for record in result]
        
        linked_count = 0
        
        for item in check_items:
            # ガイドラインセクション経由でチャンクを取得
            guideline_section = item.get("guideline_section")
            if not guideline_section:
                continue
            
            with self.neo4j_driver.session(database=settings.neo4j.database) as session:
                # 既存のリンクを作成（セクション経由）
                link_query = """
                MATCH (ci:CheckItem {id: $check_item_id})
                MATCH (ci)-[:DERIVED_FROM]->(gs:GuidelineSection)-[:CONTAINS]->(gc:GuidelineChunk)
                MERGE (ci)-[:RELATED_TO]->(gc)
                RETURN count(*) as linked
                """
                
                result = session.run(link_query, check_item_id=item["id"])
                record = result.single()
                
                if record and record["linked"] > 0:
                    linked_count += record["linked"]
                    print(f"  Linked {record['linked']} chunks to {item['id']}")
        
        print(f"Total links created: {linked_count}")
        return linked_count
    
    def get_related_chunks(self, check_item_id: str) -> list:
        """
        チェック項目に関連するガイドラインチャンクを取得
        
        Args:
            check_item_id: チェック項目ID
            
        Returns:
            関連チャンクのリスト
        """
        query = """
        MATCH (ci:CheckItem {id: $check_item_id})-[:RELATED_TO|DERIVED_FROM*1..2]->(gc:GuidelineChunk)
        RETURN gc.id as id, gc.content_preview as content, gc.section as section,
               gc.qdrant_point_id as qdrant_id
        """
        
        with self.neo4j_driver.session(database=settings.neo4j.database) as session:
            result = session.run(query, check_item_id=check_item_id)
            return [dict(record) for record in result]
    
    def get_statistics(self) -> dict:
        """変換統計を取得"""
        stats = {}
        
        with self.neo4j_driver.session(database=settings.neo4j.database) as session:
            # チャンク数
            result = session.run("MATCH (gc:GuidelineChunk) RETURN count(*) as count")
            stats["total_chunks"] = result.single()["count"]
            
            # リンク数
            result = session.run("MATCH (:CheckItem)-[:RELATED_TO]->(gc:GuidelineChunk) RETURN count(*) as count")
            stats["check_item_links"] = result.single()["count"]
            
            # セクションリンク数
            result = session.run("MATCH (:GuidelineSection)-[:CONTAINS]->(gc:GuidelineChunk) RETURN count(*) as count")
            stats["section_links"] = result.single()["count"]
        
        return stats


def main():
    """メイン関数"""
    transformer = GuidelineKGTransformer()
    
    try:
        # チャンクを KG に変換
        transformer.transform_chunks_to_kg()
        
        # チェック項目にリンク
        transformer.link_chunks_to_check_items()
        
        # 統計を表示
        print("\n" + "=" * 50)
        print("Transformation Statistics")
        print("=" * 50)
        stats = transformer.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    finally:
        transformer.close()


if __name__ == "__main__":
    main()
