"""
Tests for SmartReviewer Knowledge Server
========================================

Knowledge Graph MCPサーバーのユニットテスト
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ==============================================
# Fixtures
# ==============================================

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver"""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_driver, mock_session


# ==============================================
# Import Tests
# ==============================================

class TestImports:
    """インポートテスト"""
    
    def test_import_server(self):
        """サーバーモジュールがインポートできること"""
        from src.servers.knowledge import server
        assert server is not None
    
    def test_import_app(self):
        """appがインポートできること"""
        from src.servers.knowledge.server import app
        assert app is not None
    
    def test_import_create_server(self):
        """create_serverがインポートできること"""
        from src.servers.knowledge.server import create_server
        assert callable(create_server)
    
    def test_import_models(self):
        """Pydanticモデルがインポートできること"""
        from src.servers.knowledge.server import (
            GraphNode,
            GraphRelationship,
            TraversalResult,
            CheckItemRelation,
        )
        assert GraphNode is not None
        assert GraphRelationship is not None
        assert TraversalResult is not None
        assert CheckItemRelation is not None


# ==============================================
# Model Tests
# ==============================================

class TestModels:
    """Pydanticモデルテスト"""
    
    def test_graph_node_model(self):
        """GraphNodeモデルが正しく動作すること"""
        from src.servers.knowledge.server import GraphNode
        
        node = GraphNode(
            id="node-1",
            labels=["CheckItem", "Node"],
            properties={"name": "Test Node"},
        )
        
        assert node.id == "node-1"
        assert "CheckItem" in node.labels
        assert node.properties["name"] == "Test Node"
    
    def test_graph_relationship_model(self):
        """GraphRelationshipモデルが正しく動作すること"""
        from src.servers.knowledge.server import GraphRelationship
        
        rel = GraphRelationship(
            id="rel-1",
            type="RELATES_TO",
            start_node_id="node-1",
            end_node_id="node-2",
            properties={"weight": 1.0},
        )
        
        assert rel.id == "rel-1"
        assert rel.type == "RELATES_TO"
        assert rel.start_node_id == "node-1"
        assert rel.end_node_id == "node-2"
    
    def test_traversal_result_model(self):
        """TraversalResultモデルが正しく動作すること"""
        from src.servers.knowledge.server import TraversalResult, GraphNode, GraphRelationship
        
        result = TraversalResult(
            nodes=[
                GraphNode(id="n1", labels=["Node"], properties={}),
            ],
            relationships=[
                GraphRelationship(id="r1", type="REL", start_node_id="n1", end_node_id="n2"),
            ],
            paths=[["n1", "n2"]],
        )
        
        assert len(result.nodes) == 1
        assert len(result.relationships) == 1
        assert len(result.paths) == 1
    
    def test_check_item_relation_model(self):
        """CheckItemRelationモデルが正しく動作すること"""
        from src.servers.knowledge.server import CheckItemRelation
        
        relation = CheckItemRelation(
            check_item_id="BD-001",
            related_sections=[{"id": "sec-1", "name": "Section 1"}],
            related_guidelines=[{"id": "g-1", "name": "Guideline 1"}],
            prerequisite_items=[],
            dependent_items=[],
        )
        
        assert relation.check_item_id == "BD-001"
        assert len(relation.related_sections) == 1


# ==============================================
# Tool Tests (with mocks)
# ==============================================

class TestTools:
    """Toolテスト"""
    
    @pytest.mark.asyncio
    async def test_get_all_check_items_no_filter(self):
        """全チェック項目取得（フィルタなし）"""
        from src.servers.knowledge.server import get_all_check_items
        
        result = await get_all_check_items()
        
        assert result["success"] is True
        assert "items" in result
        assert result["total"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_all_check_items_by_document_type(self):
        """文書タイプでフィルタされたチェック項目取得"""
        from src.servers.knowledge.server import get_all_check_items
        
        result = await get_all_check_items(document_type="basic_design")
        
        assert result["success"] is True
        assert result["filters"]["document_type"] == "basic_design"
        # 全てのアイテムが basic_design であること
        for item in result["items"]:
            assert item["document_type"] == "basic_design"
    
    @pytest.mark.asyncio
    async def test_get_all_check_items_by_category(self):
        """カテゴリでフィルタされたチェック項目取得"""
        from src.servers.knowledge.server import get_all_check_items
        
        result = await get_all_check_items(category="completeness")
        
        assert result["success"] is True
        assert result["filters"]["category"] == "completeness"
    
    @pytest.mark.asyncio
    async def test_traverse_graph_with_mock(self, mock_neo4j_driver):
        """グラフ探索テスト（モック使用）"""
        from src.servers.knowledge.server import traverse_graph
        
        mock_driver, mock_session = mock_neo4j_driver
        
        # モック結果を設定
        mock_session.run.return_value = iter([])
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await traverse_graph(
                start_node_id="BD-001",
                relationship_types=["APPLIES_TO"],
                direction="outgoing",
                max_depth=2,
            )
        
        assert result["success"] is True
        assert result["start_node_id"] == "BD-001"
        assert result["direction"] == "outgoing"
    
    @pytest.mark.asyncio
    async def test_traverse_graph_error_handling(self):
        """グラフ探索エラーハンドリング"""
        from src.servers.knowledge.server import traverse_graph
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", side_effect=Exception("Connection failed")):
            result = await traverse_graph(
                start_node_id="BD-001",
            )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_check_item_relations_found(self, mock_neo4j_driver):
        """チェック項目関連情報取得（存在する項目）"""
        from src.servers.knowledge.server import get_check_item_relations
        
        mock_driver, mock_session = mock_neo4j_driver
        mock_session.run.return_value = iter([])
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await get_check_item_relations(check_item_id="BD-001")
        
        assert result["success"] is True
        assert "check_item" in result
        assert result["check_item"]["id"] == "BD-001"
    
    @pytest.mark.asyncio
    async def test_get_check_item_relations_not_found(self, mock_neo4j_driver):
        """チェック項目関連情報取得（存在しない項目）"""
        from src.servers.knowledge.server import get_check_item_relations
        
        mock_driver, mock_session = mock_neo4j_driver
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await get_check_item_relations(check_item_id="NONEXISTENT-999")
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_find_path_with_mock(self, mock_neo4j_driver):
        """パス検索テスト（モック使用）"""
        from src.servers.knowledge.server import find_path
        
        mock_driver, mock_session = mock_neo4j_driver
        mock_session.run.return_value.single.return_value = None
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await find_path(
                start_node_id="BD-001",
                end_node_id="BD-005",
                max_depth=3,
            )
        
        assert result["success"] is True
        assert result["found"] is False
    
    @pytest.mark.asyncio
    async def test_get_document_structure_with_mock(self, mock_neo4j_driver):
        """文書構造取得テスト（モック使用）"""
        from src.servers.knowledge.server import get_document_structure
        
        mock_driver, mock_session = mock_neo4j_driver
        mock_session.run.return_value = iter([])
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await get_document_structure(document_type="basic_design")
        
        assert result["success"] is True
        assert result["document_type"] == "basic_design"
    
    @pytest.mark.asyncio
    async def test_run_cypher_query_valid(self, mock_neo4j_driver):
        """有効なCypherクエリ実行"""
        from src.servers.knowledge.server import run_cypher_query
        
        mock_driver, mock_session = mock_neo4j_driver
        mock_session.run.return_value = iter([])
        
        with patch("src.servers.knowledge.server.get_neo4j_driver", return_value=mock_driver):
            result = await run_cypher_query(
                query="MATCH (n:CheckItem) RETURN n LIMIT 10"
            )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_run_cypher_query_blocked_create(self):
        """CREATEクエリがブロックされること"""
        from src.servers.knowledge.server import run_cypher_query
        
        result = await run_cypher_query(
            query="CREATE (n:Test {name: 'test'})"
        )
        
        assert result["success"] is False
        assert "CREATE" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_cypher_query_blocked_delete(self):
        """DELETEクエリがブロックされること"""
        from src.servers.knowledge.server import run_cypher_query
        
        result = await run_cypher_query(
            query="MATCH (n) DELETE n"
        )
        
        assert result["success"] is False
        assert "DELETE" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_cypher_query_blocked_merge(self):
        """MERGEクエリがブロックされること"""
        from src.servers.knowledge.server import run_cypher_query
        
        result = await run_cypher_query(
            query="MERGE (n:Test {name: 'test'})"
        )
        
        assert result["success"] is False
        assert "MERGE" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_cypher_query_must_start_with_match(self):
        """MATCHで始まらないクエリがブロックされること"""
        from src.servers.knowledge.server import run_cypher_query
        
        result = await run_cypher_query(
            query="RETURN 1 + 1"
        )
        
        assert result["success"] is False
        assert "MATCH" in result["error"]


# ==============================================
# Resource Tests
# ==============================================

class TestResources:
    """Resourceテスト"""
    
    @pytest.mark.asyncio
    async def test_get_schema_resource(self):
        """スキーマリソースが正しく返されること"""
        from src.servers.knowledge.server import get_schema
        
        result = await get_schema()
        
        assert "# Knowledge Graph Schema" in result
        assert "## Node Labels" in result
        assert "## Relationship Types" in result
        assert "## Constraints" in result
    
    @pytest.mark.asyncio
    async def test_list_all_check_items_resource(self):
        """チェック項目一覧リソースが正しく返されること"""
        from src.servers.knowledge.server import list_all_check_items
        
        result = await list_all_check_items()
        
        assert "# Check Items" in result
        # 文書タイプ別のセクションがあること
        assert "basic_design" in result or "test_plan" in result
    
    @pytest.mark.asyncio
    async def test_get_check_item_detail_found(self):
        """チェック項目詳細リソース（存在する項目）"""
        from src.servers.knowledge.server import get_check_item_detail
        
        result = await get_check_item_detail("BD-001")
        
        assert "BD-001" in result
        assert "**ID**" in result
    
    @pytest.mark.asyncio
    async def test_get_check_item_detail_not_found(self):
        """チェック項目詳細リソース（存在しない項目）"""
        from src.servers.knowledge.server import get_check_item_detail
        
        result = await get_check_item_detail("NONEXISTENT-999")
        
        assert "not found" in result.lower()


# ==============================================
# Server Factory Tests
# ==============================================

class TestServerFactory:
    """サーバーファクトリテスト"""
    
    def test_create_server(self):
        """create_serverがappを返すこと"""
        from src.servers.knowledge.server import create_server, app
        
        server = create_server()
        
        assert server is app


# ==============================================
# Schema Tests
# ==============================================

class TestSchema:
    """Neo4jSchemaテスト"""
    
    def test_neo4j_schema_exists(self):
        """Neo4jSchemaが存在すること"""
        from src.knowledge.schema import Neo4jSchema
        
        assert isinstance(Neo4jSchema, dict)
    
    def test_neo4j_schema_has_node_labels(self):
        """Neo4jSchemaにnode_labelsがあること"""
        from src.knowledge.schema import Neo4jSchema
        
        assert "node_labels" in Neo4jSchema
        assert isinstance(Neo4jSchema["node_labels"], list)
        assert len(Neo4jSchema["node_labels"]) > 0
    
    def test_neo4j_schema_has_relationship_types(self):
        """Neo4jSchemaにrelationship_typesがあること"""
        from src.knowledge.schema import Neo4jSchema
        
        assert "relationship_types" in Neo4jSchema
        assert isinstance(Neo4jSchema["relationship_types"], list)
        assert len(Neo4jSchema["relationship_types"]) > 0
    
    def test_neo4j_schema_has_constraints(self):
        """Neo4jSchemaにconstraintsがあること"""
        from src.knowledge.schema import Neo4jSchema
        
        assert "constraints" in Neo4jSchema
        assert isinstance(Neo4jSchema["constraints"], list)


# ==============================================
# CHECK_ITEMS_DATA Tests
# ==============================================

class TestCheckItemsData:
    """CHECK_ITEMS_DATAテスト"""
    
    def test_check_items_data_exists(self):
        """CHECK_ITEMS_DATAが存在すること"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        assert isinstance(CHECK_ITEMS_DATA, list)
        assert len(CHECK_ITEMS_DATA) > 0
    
    def test_check_items_have_required_fields(self):
        """チェック項目が必須フィールドを持つこと"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        required_fields = ["id", "name", "description", "category", "severity", "document_type"]
        
        for item in CHECK_ITEMS_DATA:
            for field in required_fields:
                assert field in item, f"Missing field '{field}' in item {item.get('id', 'unknown')}"
    
    def test_check_items_ids_are_unique(self):
        """チェック項目IDが一意であること"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        ids = [item["id"] for item in CHECK_ITEMS_DATA]
        assert len(ids) == len(set(ids)), "Duplicate check item IDs found"
    
    def test_check_items_severity_values(self):
        """重要度が有効な値であること"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        valid_severities = {"critical", "high", "medium", "low"}
        
        for item in CHECK_ITEMS_DATA:
            assert item["severity"] in valid_severities, \
                f"Invalid severity '{item['severity']}' for item {item['id']}"
    
    def test_check_items_document_types(self):
        """文書タイプが有効な値であること"""
        from src.knowledge.schema import CHECK_ITEMS_DATA
        
        valid_doc_types = {"basic_design", "test_plan"}
        
        for item in CHECK_ITEMS_DATA:
            assert item["document_type"] in valid_doc_types, \
                f"Invalid document_type '{item['document_type']}' for item {item['id']}"
