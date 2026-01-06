"""
SmartReviewer - Neo4j Setup Script
Graph Database initialization and schema management

Usage:
    python -m src.setup.neo4j_setup
"""

import os
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "smartreviewer_dev")


# Node labels and relationships schema
SCHEMA = {
    "node_labels": [
        "Document",          # レビュー対象文書
        "DocumentType",      # 文書種別（基本設計書、テスト計画書等）
        "Section",           # 文書内セクション
        "CheckItem",         # チェック項目
        "CheckCategory",     # チェックカテゴリ
        "Guideline",         # ガイドライン
        "GuidelineSection",  # ガイドラインセクション
        "Requirement",       # 要件（機能要件、非機能要件）
        "OntologyConcept",   # オントロジー概念
        "ReviewResult",      # レビュー結果
    ],
    "relationships": [
        ("Document", "HAS_TYPE", "DocumentType"),
        ("Document", "CONTAINS", "Section"),
        ("Section", "FOLLOWS", "Section"),
        ("Section", "REFERENCES", "Section"),
        ("CheckItem", "BELONGS_TO", "CheckCategory"),
        ("CheckItem", "APPLIES_TO", "DocumentType"),
        ("CheckItem", "REFERENCES", "GuidelineSection"),
        ("Guideline", "CONTAINS", "GuidelineSection"),
        ("GuidelineSection", "FOLLOWS", "GuidelineSection"),
        ("Section", "MAPS_TO", "Requirement"),
        ("Requirement", "DEFINED_IN", "GuidelineSection"),
        ("OntologyConcept", "SUBCLASS_OF", "OntologyConcept"),
        ("OntologyConcept", "RELATED_TO", "OntologyConcept"),
        ("Section", "INSTANCE_OF", "OntologyConcept"),
        ("ReviewResult", "FOR_DOCUMENT", "Document"),
        ("ReviewResult", "CHECKS", "CheckItem"),
    ],
    "indexes": [
        ("Document", "document_id"),
        ("Document", "name"),
        ("DocumentType", "type_id"),
        ("Section", "section_id"),
        ("CheckItem", "item_id"),
        ("CheckCategory", "category_id"),
        ("Guideline", "guideline_id"),
        ("GuidelineSection", "section_id"),
        ("OntologyConcept", "concept_id"),
        ("ReviewResult", "result_id"),
    ],
    "constraints": [
        ("Document", "document_id"),
        ("CheckItem", "item_id"),
        ("Guideline", "guideline_id"),
        ("OntologyConcept", "concept_id"),
    ],
}


def get_driver():
    """Create Neo4j driver instance."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def check_health(driver) -> bool:
    """Check Neo4j server health."""
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS health")
            record = result.single()
            if record and record["health"] == 1:
                print("✅ Neo4j is healthy")
                return True
    except ServiceUnavailable as e:
        print(f"❌ Neo4j health check failed: {e}")
    except Exception as e:
        print(f"❌ Neo4j connection error: {e}")
    return False


def create_constraints(driver) -> bool:
    """Create uniqueness constraints."""
    print("\n  Creating constraints...")
    
    with driver.session() as session:
        for label, property_name in SCHEMA["constraints"]:
            try:
                constraint_name = f"unique_{label.lower()}_{property_name}"
                query = f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{label})
                REQUIRE n.{property_name} IS UNIQUE
                """
                session.run(query)
                print(f"    ✅ Constraint: {constraint_name}")
            except Exception as e:
                print(f"    ⚠️  Constraint {label}.{property_name}: {e}")
    
    return True


def create_indexes(driver) -> bool:
    """Create indexes for better query performance."""
    print("\n  Creating indexes...")
    
    with driver.session() as session:
        for label, property_name in SCHEMA["indexes"]:
            try:
                index_name = f"idx_{label.lower()}_{property_name}"
                query = f"""
                CREATE INDEX {index_name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.{property_name})
                """
                session.run(query)
                print(f"    ✅ Index: {index_name}")
            except Exception as e:
                print(f"    ⚠️  Index {label}.{property_name}: {e}")
    
    return True


def create_initial_data(driver) -> bool:
    """Create initial master data."""
    print("\n  Creating initial data...")
    
    with driver.session() as session:
        # Document Types
        doc_types = [
            {"type_id": "basic_design", "name": "基本設計書", "description": "システムの基本設計を記述した文書"},
            {"type_id": "test_plan", "name": "全体テスト計画書", "description": "テスト全体の計画を記述した文書"},
        ]
        
        for dt in doc_types:
            session.run("""
                MERGE (d:DocumentType {type_id: $type_id})
                SET d.name = $name, d.description = $description
            """, dt)
        print("    ✅ Document types created")
        
        # Check Categories (from check-items.md)
        categories = [
            {"category_id": "bd_structure", "name": "文書構成・形式", "doc_type": "basic_design"},
            {"category_id": "bd_completeness", "name": "内容の完全性", "doc_type": "basic_design"},
            {"category_id": "bd_quality", "name": "記述品質", "doc_type": "basic_design"},
            {"category_id": "bd_guideline", "name": "ガイドライン準拠", "doc_type": "basic_design"},
            {"category_id": "tp_structure", "name": "文書構成・形式", "doc_type": "test_plan"},
            {"category_id": "tp_completeness", "name": "テスト計画の完全性", "doc_type": "test_plan"},
            {"category_id": "tp_organization", "name": "体制・環境", "doc_type": "test_plan"},
            {"category_id": "tp_schedule", "name": "スケジュール・進捗管理", "doc_type": "test_plan"},
            {"category_id": "tp_guideline", "name": "ガイドライン準拠", "doc_type": "test_plan"},
        ]
        
        for cat in categories:
            session.run("""
                MERGE (c:CheckCategory {category_id: $category_id})
                SET c.name = $name
                WITH c
                MATCH (dt:DocumentType {type_id: $doc_type})
                MERGE (c)-[:FOR_TYPE]->(dt)
            """, cat)
        print("    ✅ Check categories created")
        
        # Guideline master
        guidelines = [
            {
                "guideline_id": "dgps_main",
                "name": "デジタル・ガバメント推進標準ガイドライン",
                "version": "2023年度版",
            },
        ]
        
        for gl in guidelines:
            session.run("""
                MERGE (g:Guideline {guideline_id: $guideline_id})
                SET g.name = $name, g.version = $version
            """, gl)
        print("    ✅ Guidelines created")
    
    return True


def clear_database(driver) -> bool:
    """Clear all data (use with caution!)."""
    print("\n  ⚠️  Clearing database...")
    
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("    ✅ All data deleted")
    
    return True


def setup_database(clear: bool = False) -> bool:
    """Setup Neo4j database schema and initial data."""
    print("\n🔧 Setting up Neo4j database...")
    
    driver = get_driver()
    
    try:
        if not check_health(driver):
            return False
        
        if clear:
            clear_database(driver)
        
        create_constraints(driver)
        create_indexes(driver)
        create_initial_data(driver)
        
        return True
        
    finally:
        driver.close()


def show_status() -> None:
    """Show database status."""
    print("\n📊 Neo4j Database Status:")
    print("-" * 60)
    
    driver = get_driver()
    
    try:
        if not check_health(driver):
            return
        
        with driver.session() as session:
            # Node counts by label
            result = session.run("""
                CALL db.labels() YIELD label
                CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) AS count', {})
                YIELD value
                RETURN label, value.count AS count
                ORDER BY label
            """)
            
            print("\n  Node counts:")
            for record in result:
                print(f"    {record['label']}: {record['count']}")
            
            # Relationship counts
            result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                CALL apoc.cypher.run('MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) AS count', {})
                YIELD value
                RETURN relationshipType, value.count AS count
                ORDER BY relationshipType
            """)
            
            print("\n  Relationship counts:")
            for record in result:
                print(f"    {record['relationshipType']}: {record['count']}")
                
    except Exception as e:
        print(f"  ⚠️  Could not get detailed status: {e}")
        print("  (APOC plugin may not be installed)")
        
        # Fallback: simple count
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"\n  Total nodes: {count}")
    
    finally:
        driver.close()
    
    print("-" * 60)


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j Setup for SmartReviewer")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear database before setup",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show database status only",
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        success = setup_database(clear=args.clear)
        if success:
            print("\n✅ Neo4j setup completed successfully!")
            show_status()
        else:
            print("\n❌ Neo4j setup failed!")
            exit(1)


if __name__ == "__main__":
    main()
