"""
Neo4j Knowledge Graph Schema Definition
======================================

SmartReviewer ナレッジグラフスキーマ定義
- Node labels and properties
- Relationship types and properties
- Cypher queries for schema creation
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


# ==============================================
# Enums
# ==============================================

class NodeLabel(str, Enum):
    """ノードラベル定義"""
    # Document Types
    DOCUMENT = "Document"
    BASIC_DESIGN = "BasicDesign"
    TEST_PLAN = "TestPlan"
    SECTION = "Section"
    
    # Design Components
    DESIGN_COMPONENT = "DesignComponent"
    SYSTEM_ARCHITECTURE = "SystemArchitecture"
    FUNCTIONAL_DESIGN = "FunctionalDesign"
    DATA_DESIGN = "DataDesign"
    INTERFACE_DESIGN = "InterfaceDesign"
    NON_FUNCTIONAL = "NonFunctional"
    
    # Test Plan Components
    TEST_LEVEL = "TestLevel"
    TEST_TYPE = "TestType"
    TEST_CRITERIA = "TestCriteria"
    TEST_ENVIRONMENT = "TestEnvironment"
    TEST_SCHEDULE = "TestSchedule"
    
    # Guidelines
    GUIDELINE = "Guideline"
    GUIDELINE_SECTION = "GuidelineSection"
    GUIDELINE_CHUNK = "GuidelineChunk"
    
    # Check Items
    CHECK_ITEM = "CheckItem"
    CHECK_CATEGORY = "CheckCategory"
    
    # Requirements
    REQUIREMENT = "Requirement"
    FUNCTIONAL_REQ = "FunctionalRequirement"
    NON_FUNCTIONAL_REQ = "NonFunctionalRequirement"


class RelationType(str, Enum):
    """リレーションシップタイプ定義"""
    # Document structure
    HAS_SECTION = "HAS_SECTION"
    FOLLOWS = "FOLLOWS"
    CONTAINS = "CONTAINS"
    
    # Design relationships
    REALIZES = "REALIZES"
    DEPENDS_ON = "DEPENDS_ON"
    REFERENCES = "REFERENCES"
    
    # Check item relationships
    APPLIES_TO = "APPLIES_TO"
    BELONGS_TO = "BELONGS_TO"
    DERIVED_FROM = "DERIVED_FROM"
    
    # Guideline relationships
    BASED_ON = "BASED_ON"
    RELATED_TO = "RELATED_TO"
    
    # Test relationships
    HAS_TEST_LEVEL = "HAS_TEST_LEVEL"
    HAS_TEST_TYPE = "HAS_TEST_TYPE"
    HAS_CRITERIA = "HAS_CRITERIA"
    REQUIRES_ENV = "REQUIRES_ENV"
    PRECEDES = "PRECEDES"


# ==============================================
# Node Schemas
# ==============================================

@dataclass
class DocumentNode:
    """文書ノードスキーマ"""
    id: str
    title: str
    document_type: str  # basic_design | test_plan
    version: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    file_path: Optional[str] = None
    
    @property
    def label(self) -> str:
        if self.document_type == "basic_design":
            return NodeLabel.BASIC_DESIGN.value
        elif self.document_type == "test_plan":
            return NodeLabel.TEST_PLAN.value
        return NodeLabel.DOCUMENT.value


@dataclass
class SectionNode:
    """セクションノードスキーマ"""
    id: str
    section_number: str
    title: str
    is_required: bool = False
    level: int = 1
    content_summary: Optional[str] = None


@dataclass
class CheckItemNode:
    """チェック項目ノードスキーマ"""
    id: str  # e.g., BD-001, TP-001
    name: str
    description: str
    category: str
    severity: str  # critical | high | medium | low
    document_type: str  # basic_design | test_plan
    guideline_section: Optional[str] = None
    check_logic: Optional[str] = None


@dataclass
class GuidelineSectionNode:
    """ガイドラインセクションノードスキーマ"""
    id: str
    section_number: str
    title: str
    source: str  # DG推進標準ガイドライン等
    summary: Optional[str] = None


@dataclass
class GuidelineChunkNode:
    """ガイドラインチャンクノードスキーマ"""
    id: str
    chunk_index: int
    content: str
    embedding_id: Optional[str] = None
    metadata: Optional[dict] = None


# ==============================================
# Cypher Schema Queries
# ==============================================

SCHEMA_CONSTRAINTS = """
// ============================================
// Unique Constraints
// ============================================

// Documents
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT basic_design_id IF NOT EXISTS FOR (bd:BasicDesign) REQUIRE bd.id IS UNIQUE;
CREATE CONSTRAINT test_plan_id IF NOT EXISTS FOR (tp:TestPlan) REQUIRE tp.id IS UNIQUE;

// Sections
CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE;

// Check Items
CREATE CONSTRAINT check_item_id IF NOT EXISTS FOR (ci:CheckItem) REQUIRE ci.id IS UNIQUE;
CREATE CONSTRAINT check_category_id IF NOT EXISTS FOR (cc:CheckCategory) REQUIRE cc.id IS UNIQUE;

// Guidelines
CREATE CONSTRAINT guideline_id IF NOT EXISTS FOR (g:Guideline) REQUIRE g.id IS UNIQUE;
CREATE CONSTRAINT guideline_section_id IF NOT EXISTS FOR (gs:GuidelineSection) REQUIRE gs.id IS UNIQUE;
CREATE CONSTRAINT guideline_chunk_id IF NOT EXISTS FOR (gc:GuidelineChunk) REQUIRE gc.id IS UNIQUE;

// Design Components
CREATE CONSTRAINT design_component_id IF NOT EXISTS FOR (dc:DesignComponent) REQUIRE dc.id IS UNIQUE;

// Test Components
CREATE CONSTRAINT test_level_id IF NOT EXISTS FOR (tl:TestLevel) REQUIRE tl.id IS UNIQUE;
CREATE CONSTRAINT test_type_id IF NOT EXISTS FOR (tt:TestType) REQUIRE tt.id IS UNIQUE;
"""

SCHEMA_INDEXES = """
// ============================================
// Indexes for Performance
// ============================================

// Document indexes
CREATE INDEX document_type_idx IF NOT EXISTS FOR (d:Document) ON (d.document_type);
CREATE INDEX document_title_idx IF NOT EXISTS FOR (d:Document) ON (d.title);

// Section indexes
CREATE INDEX section_number_idx IF NOT EXISTS FOR (s:Section) ON (s.section_number);
CREATE INDEX section_required_idx IF NOT EXISTS FOR (s:Section) ON (s.is_required);

// Check item indexes
CREATE INDEX check_item_category_idx IF NOT EXISTS FOR (ci:CheckItem) ON (ci.category);
CREATE INDEX check_item_severity_idx IF NOT EXISTS FOR (ci:CheckItem) ON (ci.severity);
CREATE INDEX check_item_doc_type_idx IF NOT EXISTS FOR (ci:CheckItem) ON (ci.document_type);

// Guideline indexes
CREATE INDEX guideline_source_idx IF NOT EXISTS FOR (g:Guideline) ON (g.source);
CREATE INDEX guideline_chunk_embedding_idx IF NOT EXISTS FOR (gc:GuidelineChunk) ON (gc.embedding_id);

// Full-text search indexes
CREATE FULLTEXT INDEX check_item_search IF NOT EXISTS FOR (ci:CheckItem) ON EACH [ci.name, ci.description];
CREATE FULLTEXT INDEX guideline_search IF NOT EXISTS FOR (gc:GuidelineChunk) ON EACH [gc.content];
"""

# ==============================================
# Check Item Initial Data
# ==============================================

CHECK_ITEMS_DATA = [
    # Basic Design Check Items (BD-001 to BD-010)
    {
        "id": "BD-001",
        "name": "必須セクション存在確認",
        "description": "基本設計書に必要なセクション（概要、システム構成、機能設計、データ設計、インターフェース設計、非機能設計）が存在することを確認する",
        "category": "structure",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.2",
    },
    {
        "id": "BD-002",
        "name": "セクション順序確認",
        "description": "基本設計書のセクションがガイドラインに準拠した順序で配置されていることを確認する",
        "category": "structure",
        "severity": "high",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.2",
    },
    {
        "id": "BD-003",
        "name": "システム目的明記確認",
        "description": "システムの目的・背景が明確に記述されていることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.1",
    },
    {
        "id": "BD-004",
        "name": "システム構成図存在確認",
        "description": "システム構成を示す図（構成図、ネットワーク図等）が含まれていることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.2",
    },
    {
        "id": "BD-005",
        "name": "機能一覧の網羅性確認",
        "description": "要件定義書の機能要件に対応する機能が設計書に記載されていることを確認する",
        "category": "traceability",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.3",
    },
    {
        "id": "BD-006",
        "name": "データモデル定義確認",
        "description": "データモデル（ER図、テーブル定義等）が適切に定義されていることを確認する",
        "category": "completeness",
        "severity": "high",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.4",
    },
    {
        "id": "BD-007",
        "name": "外部インターフェース定義確認",
        "description": "外部システムとのインターフェースが定義されていることを確認する",
        "category": "completeness",
        "severity": "high",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.5",
    },
    {
        "id": "BD-008",
        "name": "非機能要件カバレッジ確認",
        "description": "性能、可用性、セキュリティ等の非機能要件が設計に反映されていることを確認する",
        "category": "traceability",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.2.6",
    },
    {
        "id": "BD-009",
        "name": "用語一貫性確認",
        "description": "文書内で使用される用語が一貫していることを確認する",
        "category": "quality",
        "severity": "medium",
        "document_type": "basic_design",
        "guideline_section": "第3編 3.1.1",
    },
    {
        "id": "BD-010",
        "name": "セキュリティ設計確認",
        "description": "セキュリティ要件（認証、認可、暗号化等）が設計に含まれていることを確認する",
        "category": "guideline",
        "severity": "critical",
        "document_type": "basic_design",
        "guideline_section": "第4編 第5章",
    },
    
    # Test Plan Check Items (TP-001 to TP-010)
    {
        "id": "TP-001",
        "name": "テスト方針明記確認",
        "description": "テスト全体の方針・目的が明確に記述されていることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.1",
    },
    {
        "id": "TP-002",
        "name": "テストレベル定義確認",
        "description": "各テストレベル（単体、結合、システム、受入）の定義と範囲が明確であることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.2",
    },
    {
        "id": "TP-003",
        "name": "テスト種別網羅確認",
        "description": "機能テスト、性能テスト、セキュリティテスト等の必要なテスト種別が計画されていることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.2",
    },
    {
        "id": "TP-004",
        "name": "開始/終了基準定義確認",
        "description": "各テストレベルの開始基準・終了基準が定義されていることを確認する",
        "category": "completeness",
        "severity": "high",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.3",
    },
    {
        "id": "TP-005",
        "name": "テストスケジュール整合性確認",
        "description": "テストスケジュールが開発スケジュールと整合していることを確認する",
        "category": "traceability",
        "severity": "high",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.4",
    },
    {
        "id": "TP-006",
        "name": "テスト体制定義確認",
        "description": "テスト実施体制（役割、責任）が定義されていることを確認する",
        "category": "completeness",
        "severity": "high",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.5",
    },
    {
        "id": "TP-007",
        "name": "テスト環境定義確認",
        "description": "テスト環境（ハードウェア、ソフトウェア、データ）が定義されていることを確認する",
        "category": "completeness",
        "severity": "high",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.6",
    },
    {
        "id": "TP-008",
        "name": "障害管理方法定義確認",
        "description": "障害発見時の管理方法・エスカレーション手順が定義されていることを確認する",
        "category": "completeness",
        "severity": "medium",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.7",
    },
    {
        "id": "TP-009",
        "name": "要件カバレッジ確認",
        "description": "機能要件・非機能要件に対するテストカバレッジが計画されていることを確認する",
        "category": "traceability",
        "severity": "critical",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.2",
    },
    {
        "id": "TP-010",
        "name": "合格判定基準定義確認",
        "description": "テスト合格の判定基準（品質指標）が定義されていることを確認する",
        "category": "completeness",
        "severity": "critical",
        "document_type": "test_plan",
        "guideline_section": "第3編 3.3.3",
    },
]

# ==============================================
# Cypher Queries for Data Operations
# ==============================================

CREATE_CHECK_ITEM_QUERY = """
MERGE (ci:CheckItem {id: $id})
SET ci.name = $name,
    ci.description = $description,
    ci.category = $category,
    ci.severity = $severity,
    ci.document_type = $document_type,
    ci.guideline_section = $guideline_section,
    ci.created_at = datetime()
RETURN ci
"""

CREATE_GUIDELINE_SECTION_QUERY = """
MERGE (gs:GuidelineSection {id: $id})
SET gs.section_number = $section_number,
    gs.title = $title,
    gs.source = $source,
    gs.summary = $summary,
    gs.created_at = datetime()
RETURN gs
"""

CREATE_GUIDELINE_CHUNK_QUERY = """
MERGE (gc:GuidelineChunk {id: $id})
SET gc.chunk_index = $chunk_index,
    gc.content = $content,
    gc.embedding_id = $embedding_id,
    gc.created_at = datetime()
WITH gc
MATCH (gs:GuidelineSection {id: $section_id})
MERGE (gs)-[:CONTAINS]->(gc)
RETURN gc
"""

LINK_CHECK_ITEM_TO_GUIDELINE_QUERY = """
MATCH (ci:CheckItem {id: $check_item_id})
MATCH (gs:GuidelineSection {section_number: $section_number})
MERGE (ci)-[:DERIVED_FROM]->(gs)
RETURN ci, gs
"""

# ==============================================
# Query Functions
# ==============================================

def get_check_items_for_document_type(document_type: str) -> str:
    """指定された文書タイプのチェック項目を取得するクエリ"""
    return f"""
    MATCH (ci:CheckItem)
    WHERE ci.document_type = '{document_type}'
    RETURN ci
    ORDER BY ci.id
    """


def get_related_guidelines_for_check_item(check_item_id: str) -> str:
    """チェック項目に関連するガイドラインを取得するクエリ"""
    return f"""
    MATCH (ci:CheckItem {{id: '{check_item_id}'}})-[:DERIVED_FROM]->(gs:GuidelineSection)
    OPTIONAL MATCH (gs)-[:CONTAINS]->(gc:GuidelineChunk)
    RETURN gs, collect(gc) as chunks
    """


def get_document_structure(document_id: str) -> str:
    """文書構造を取得するクエリ"""
    return f"""
    MATCH (d:Document {{id: '{document_id}'}})-[:HAS_SECTION]->(s:Section)
    OPTIONAL MATCH (s)-[:CONTAINS]->(dc:DesignComponent)
    RETURN s, collect(dc) as components
    ORDER BY s.section_number
    """


# ==============================================
# Neo4j Schema Definition
# ==============================================

Neo4jSchema = {
    "node_labels": [label.value for label in NodeLabel],
    "relationship_types": [rel.value for rel in RelationType],
    "constraints": [
        "document_id UNIQUE",
        "basic_design_id UNIQUE",
        "test_plan_id UNIQUE",
        "section_id UNIQUE",
        "check_item_id UNIQUE",
        "check_category_id UNIQUE",
        "guideline_id UNIQUE",
        "guideline_section_id UNIQUE",
        "guideline_chunk_id UNIQUE",
        "design_component_id UNIQUE",
        "test_level_id UNIQUE",
        "test_type_id UNIQUE",
    ],
}
