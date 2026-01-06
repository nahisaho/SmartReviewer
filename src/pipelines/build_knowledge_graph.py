"""
Knowledge Graph Builder
=======================

ガイドラインとチェック項目をナレッジグラフに登録するパイプライン
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import asdict

from neo4j import GraphDatabase

from src.shared.config.settings import settings
from src.shared.config.clients import get_neo4j_driver
from src.knowledge.schema import (
    CHECK_ITEMS_DATA,
    SCHEMA_CONSTRAINTS,
    SCHEMA_INDEXES,
    CREATE_CHECK_ITEM_QUERY,
    CREATE_GUIDELINE_SECTION_QUERY,
    CREATE_GUIDELINE_CHUNK_QUERY,
    LINK_CHECK_ITEM_TO_GUIDELINE_QUERY,
)


class KnowledgeGraphBuilder:
    """ナレッジグラフ構築クラス"""
    
    def __init__(self):
        self.driver = get_neo4j_driver()
        
    def close(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.close()
    
    def setup_schema(self):
        """スキーマ（制約・インデックス）を作成"""
        print("Setting up Knowledge Graph schema...")
        
        with self.driver.session(database=settings.neo4j.database) as session:
            # Execute constraints
            for statement in SCHEMA_CONSTRAINTS.strip().split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("//"):
                    try:
                        session.run(statement)
                        print(f"  Created constraint: {statement[:60]}...")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"  Constraint already exists: {statement[:40]}...")
                        else:
                            print(f"  Warning: {e}")
            
            # Execute indexes
            for statement in SCHEMA_INDEXES.strip().split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("//"):
                    try:
                        session.run(statement)
                        print(f"  Created index: {statement[:60]}...")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"  Index already exists: {statement[:40]}...")
                        else:
                            print(f"  Warning: {e}")
        
        print("Schema setup complete!")
    
    def load_check_items(self):
        """チェック項目をナレッジグラフに登録"""
        print("\nLoading check items...")
        
        with self.driver.session(database=settings.neo4j.database) as session:
            for item in CHECK_ITEMS_DATA:
                result = session.run(CREATE_CHECK_ITEM_QUERY, **item)
                record = result.single()
                if record:
                    print(f"  Created: {item['id']} - {item['name']}")
        
        print(f"Loaded {len(CHECK_ITEMS_DATA)} check items.")
    
    def create_check_categories(self):
        """チェックカテゴリノードを作成"""
        print("\nCreating check categories...")
        
        categories = [
            {"id": "structure", "name": "構成チェック", "description": "文書の構成・セクションに関するチェック"},
            {"id": "completeness", "name": "網羅性チェック", "description": "必要な内容が網羅されているかのチェック"},
            {"id": "traceability", "name": "追跡性チェック", "description": "要件との追跡性に関するチェック"},
            {"id": "quality", "name": "品質チェック", "description": "文書の品質に関するチェック"},
            {"id": "guideline", "name": "ガイドライン準拠チェック", "description": "ガイドラインへの準拠に関するチェック"},
        ]
        
        query = """
        MERGE (cc:CheckCategory {id: $id})
        SET cc.name = $name,
            cc.description = $description,
            cc.created_at = datetime()
        RETURN cc
        """
        
        with self.driver.session(database=settings.neo4j.database) as session:
            for cat in categories:
                session.run(query, **cat)
                print(f"  Created category: {cat['name']}")
        
        # Link check items to categories
        link_query = """
        MATCH (ci:CheckItem)
        MATCH (cc:CheckCategory {id: ci.category})
        MERGE (ci)-[:BELONGS_TO]->(cc)
        RETURN count(*) as linked
        """
        
        with self.driver.session(database=settings.neo4j.database) as session:
            result = session.run(link_query)
            record = result.single()
            print(f"  Linked {record['linked']} check items to categories.")
    
    def load_guideline_sections(self, guideline_metadata_path: Optional[Path] = None):
        """ガイドラインセクションをナレッジグラフに登録"""
        print("\nLoading guideline sections...")
        
        # DG推進標準ガイドラインのセクション定義
        guideline_sections = [
            {
                "id": "dg-3-2-1",
                "section_number": "第3編 3.2.1",
                "title": "要件定義工程",
                "source": "DG推進標準ガイドライン",
                "summary": "システムの目的、背景、業務要件を定義する工程に関する指針",
            },
            {
                "id": "dg-3-2-2",
                "section_number": "第3編 3.2.2",
                "title": "設計工程",
                "source": "DG推進標準ガイドライン",
                "summary": "基本設計・詳細設計に関する指針。必須セクション構成を定義",
            },
            {
                "id": "dg-3-2-3",
                "section_number": "第3編 3.2.3",
                "title": "機能設計",
                "source": "DG推進標準ガイドライン",
                "summary": "機能設計の記載要件と要件との対応付けに関する指針",
            },
            {
                "id": "dg-3-2-4",
                "section_number": "第3編 3.2.4",
                "title": "データ設計",
                "source": "DG推進標準ガイドライン",
                "summary": "データモデル設計に関する指針",
            },
            {
                "id": "dg-3-2-5",
                "section_number": "第3編 3.2.5",
                "title": "インターフェース設計",
                "source": "DG推進標準ガイドライン",
                "summary": "外部システム連携、API設計に関する指針",
            },
            {
                "id": "dg-3-2-6",
                "section_number": "第3編 3.2.6",
                "title": "非機能設計",
                "source": "DG推進標準ガイドライン",
                "summary": "性能、可用性、セキュリティ等の非機能要件設計に関する指針",
            },
            {
                "id": "dg-3-3-1",
                "section_number": "第3編 3.3.1",
                "title": "テスト方針",
                "source": "DG推進標準ガイドライン",
                "summary": "テスト計画の方針策定に関する指針",
            },
            {
                "id": "dg-3-3-2",
                "section_number": "第3編 3.3.2",
                "title": "テストレベル・種別",
                "source": "DG推進標準ガイドライン",
                "summary": "テストレベルとテスト種別の定義に関する指針",
            },
            {
                "id": "dg-3-3-3",
                "section_number": "第3編 3.3.3",
                "title": "テスト基準",
                "source": "DG推進標準ガイドライン",
                "summary": "開始・終了・合格基準の定義に関する指針",
            },
            {
                "id": "dg-3-3-4",
                "section_number": "第3編 3.3.4",
                "title": "テストスケジュール",
                "source": "DG推進標準ガイドライン",
                "summary": "テスト日程計画に関する指針",
            },
            {
                "id": "dg-3-3-5",
                "section_number": "第3編 3.3.5",
                "title": "テスト体制",
                "source": "DG推進標準ガイドライン",
                "summary": "テスト実施体制の構築に関する指針",
            },
            {
                "id": "dg-3-3-6",
                "section_number": "第3編 3.3.6",
                "title": "テスト環境",
                "source": "DG推進標準ガイドライン",
                "summary": "テスト環境の構築・管理に関する指針",
            },
            {
                "id": "dg-3-3-7",
                "section_number": "第3編 3.3.7",
                "title": "障害管理",
                "source": "DG推進標準ガイドライン",
                "summary": "テスト時の障害管理に関する指針",
            },
            {
                "id": "dg-4-5",
                "section_number": "第4編 第5章",
                "title": "セキュリティ",
                "source": "DG推進標準ガイドライン",
                "summary": "情報セキュリティ対策に関する指針",
            },
            {
                "id": "dg-3-1-1",
                "section_number": "第3編 3.1.1",
                "title": "文書品質",
                "source": "DG推進標準ガイドライン",
                "summary": "文書の品質管理に関する指針。用語の一貫性等",
            },
        ]
        
        with self.driver.session(database=settings.neo4j.database) as session:
            for section in guideline_sections:
                session.run(CREATE_GUIDELINE_SECTION_QUERY, **section)
                print(f"  Created: {section['section_number']} - {section['title']}")
        
        print(f"Loaded {len(guideline_sections)} guideline sections.")
    
    def link_check_items_to_guidelines(self):
        """チェック項目とガイドラインセクションをリンク"""
        print("\nLinking check items to guidelines...")
        
        with self.driver.session(database=settings.neo4j.database) as session:
            for item in CHECK_ITEMS_DATA:
                if item.get("guideline_section"):
                    try:
                        result = session.run(
                            LINK_CHECK_ITEM_TO_GUIDELINE_QUERY,
                            check_item_id=item["id"],
                            section_number=item["guideline_section"]
                        )
                        record = result.single()
                        if record:
                            print(f"  Linked: {item['id']} -> {item['guideline_section']}")
                    except Exception as e:
                        print(f"  Warning: Could not link {item['id']}: {e}")
        
        print("Linking complete!")
    
    def create_document_type_nodes(self):
        """文書タイプノードを作成"""
        print("\nCreating document type nodes...")
        
        query = """
        MERGE (dt:DocumentType {id: $id})
        SET dt.name = $name,
            dt.description = $description,
            dt.created_at = datetime()
        RETURN dt
        """
        
        document_types = [
            {
                "id": "basic_design",
                "name": "基本設計書",
                "description": "システムの基本設計を記述した文書"
            },
            {
                "id": "test_plan",
                "name": "全体テスト計画書",
                "description": "テスト全体の計画を記述した文書"
            },
        ]
        
        with self.driver.session(database=settings.neo4j.database) as session:
            for dt in document_types:
                session.run(query, **dt)
                print(f"  Created: {dt['name']}")
        
        # Link check items to document types
        link_query = """
        MATCH (ci:CheckItem)
        MATCH (dt:DocumentType {id: ci.document_type})
        MERGE (ci)-[:APPLIES_TO]->(dt)
        RETURN count(*) as linked
        """
        
        with self.driver.session(database=settings.neo4j.database) as session:
            result = session.run(link_query)
            record = result.single()
            print(f"  Linked {record['linked']} check items to document types.")
    
    def get_statistics(self) -> dict:
        """ナレッジグラフの統計情報を取得"""
        stats_query = """
        MATCH (n)
        WITH labels(n) as labels, count(*) as count
        RETURN labels, count
        ORDER BY count DESC
        """
        
        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) as type, count(*) as count
        RETURN type, count
        ORDER BY count DESC
        """
        
        stats = {"nodes": {}, "relationships": {}}
        
        with self.driver.session(database=settings.neo4j.database) as session:
            # Node counts
            result = session.run(stats_query)
            for record in result:
                label = record["labels"][0] if record["labels"] else "Unknown"
                stats["nodes"][label] = record["count"]
            
            # Relationship counts
            result = session.run(rel_query)
            for record in result:
                stats["relationships"][record["type"]] = record["count"]
        
        return stats
    
    def build_all(self):
        """全てのナレッジグラフデータを構築"""
        print("=" * 60)
        print("Building Knowledge Graph")
        print("=" * 60)
        
        try:
            self.setup_schema()
            self.load_check_items()
            self.create_check_categories()
            self.load_guideline_sections()
            self.link_check_items_to_guidelines()
            self.create_document_type_nodes()
            
            # Print statistics
            print("\n" + "=" * 60)
            print("Knowledge Graph Statistics")
            print("=" * 60)
            stats = self.get_statistics()
            
            print("\nNode counts:")
            for label, count in stats["nodes"].items():
                print(f"  {label}: {count}")
            
            print("\nRelationship counts:")
            for rel_type, count in stats["relationships"].items():
                print(f"  {rel_type}: {count}")
            
            print("\n" + "=" * 60)
            print("Knowledge Graph build complete!")
            print("=" * 60)
            
        finally:
            self.close()


def main():
    """メイン関数"""
    builder = KnowledgeGraphBuilder()
    builder.build_all()


if __name__ == "__main__":
    main()
