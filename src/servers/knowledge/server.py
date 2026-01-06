"""
SmartReviewer Knowledge Server
==============================

知識グラフ（Neo4j）サーバー
- グラフ探索
- 関連ノード取得
- 知識推論
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, UTC

from src.shared.config.settings import settings
from src.shared.config.clients import get_neo4j_driver
from src.knowledge.schema import CHECK_ITEMS_DATA, Neo4jSchema


# ==============================================
# Pydantic Models
# ==============================================

class GraphNode(BaseModel):
    """グラフノード"""
    id: str = Field(description="ノードID")
    labels: list[str] = Field(description="ノードラベル")
    properties: dict = Field(default_factory=dict, description="プロパティ")


class GraphRelationship(BaseModel):
    """グラフリレーションシップ"""
    id: str = Field(description="リレーションシップID")
    type: str = Field(description="リレーションシップタイプ")
    start_node_id: str = Field(description="開始ノードID")
    end_node_id: str = Field(description="終了ノードID")
    properties: dict = Field(default_factory=dict, description="プロパティ")


class TraversalResult(BaseModel):
    """グラフ探索結果"""
    nodes: list[GraphNode] = Field(default_factory=list, description="ノード一覧")
    relationships: list[GraphRelationship] = Field(default_factory=list, description="リレーション一覧")
    paths: list[list[str]] = Field(default_factory=list, description="パス一覧")


class CheckItemRelation(BaseModel):
    """チェック項目の関連情報"""
    check_item_id: str = Field(description="チェック項目ID")
    related_sections: list[dict] = Field(default_factory=list, description="関連セクション")
    related_guidelines: list[dict] = Field(default_factory=list, description="関連ガイドライン")
    prerequisite_items: list[dict] = Field(default_factory=list, description="前提チェック項目")
    dependent_items: list[dict] = Field(default_factory=list, description="依存チェック項目")


# ==============================================
# FastMCP Server
# ==============================================

app = FastMCP("smartreviewer-knowledge")


# ==============================================
# Tools
# ==============================================

@app.tool()
async def traverse_graph(
    start_node_id: str,
    relationship_types: Optional[list[str]] = None,
    direction: str = "outgoing",
    max_depth: int = 2,
    limit: int = 50,
) -> dict:
    """
    指定ノードからグラフを探索
    
    Args:
        start_node_id: 開始ノードID
        relationship_types: 辿るリレーションシップタイプ（空なら全て）
        direction: 探索方向（outgoing, incoming, both）
        max_depth: 最大探索深度
        limit: 最大取得ノード数
    
    Returns:
        探索結果
    """
    try:
        driver = get_neo4j_driver()
        
        # 方向指定
        if direction == "outgoing":
            rel_pattern = "-[r]->"
        elif direction == "incoming":
            rel_pattern = "<-[r]-"
        else:
            rel_pattern = "-[r]-"
        
        # リレーションシップタイプフィルタ
        rel_filter = ""
        if relationship_types:
            rel_filter = ":" + "|".join(relationship_types)
        
        query = f"""
        MATCH path = (start {{id: $start_id}}){rel_pattern.replace('[r]', f'[r{rel_filter}*1..{max_depth}]')}(end)
        WITH path, nodes(path) as pathNodes, relationships(path) as pathRels
        UNWIND pathNodes as n
        WITH COLLECT(DISTINCT n) as allNodes, COLLECT(DISTINCT pathRels) as allRels, path
        RETURN allNodes, allRels
        LIMIT $limit
        """
        
        with driver.session() as session:
            result = session.run(
                query,
                start_id=start_node_id,
                limit=limit,
            )
            
            nodes = []
            relationships = []
            seen_node_ids = set()
            seen_rel_ids = set()
            
            for record in result:
                # ノード処理
                for node in record.get("allNodes", []):
                    node_id = str(node.element_id)
                    if node_id not in seen_node_ids:
                        seen_node_ids.add(node_id)
                        nodes.append({
                            "id": node.get("id", node_id),
                            "labels": list(node.labels),
                            "properties": dict(node),
                        })
                
                # リレーション処理
                for rels in record.get("allRels", []):
                    for rel in rels:
                        rel_id = str(rel.element_id)
                        if rel_id not in seen_rel_ids:
                            seen_rel_ids.add(rel_id)
                            relationships.append({
                                "id": rel_id,
                                "type": rel.type,
                                "start_node_id": str(rel.start_node.element_id),
                                "end_node_id": str(rel.end_node.element_id),
                                "properties": dict(rel),
                            })
        
        return {
            "success": True,
            "start_node_id": start_node_id,
            "direction": direction,
            "max_depth": max_depth,
            "nodes_found": len(nodes),
            "relationships_found": len(relationships),
            "nodes": nodes,
            "relationships": relationships,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def get_check_item_relations(
    check_item_id: str,
) -> dict:
    """
    チェック項目の関連情報を取得
    
    Args:
        check_item_id: チェック項目ID
    
    Returns:
        関連情報（セクション、ガイドライン、前提・依存チェック項目）
    """
    try:
        # まずローカルデータから基本情報を取得
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
        
        driver = get_neo4j_driver()
        
        # 関連セクション取得
        sections_query = """
        MATCH (c:CheckItem {id: $check_id})-[:VERIFIES]->(s:Section)
        RETURN s
        """
        
        # 関連ガイドライン取得
        guidelines_query = """
        MATCH (c:CheckItem {id: $check_id})-[:BASED_ON]->(g:Guideline)
        RETURN g
        """
        
        # 前提チェック項目
        prereq_query = """
        MATCH (c:CheckItem {id: $check_id})-[:REQUIRES]->(p:CheckItem)
        RETURN p
        """
        
        # 依存チェック項目
        dependent_query = """
        MATCH (d:CheckItem)-[:REQUIRES]->(c:CheckItem {id: $check_id})
        RETURN d
        """
        
        with driver.session() as session:
            # 関連セクション
            sections = []
            result = session.run(sections_query, check_id=check_item_id)
            for record in result:
                node = record["s"]
                sections.append({
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                    "document_type": node.get("document_type", ""),
                })
            
            # 関連ガイドライン
            guidelines = []
            result = session.run(guidelines_query, check_id=check_item_id)
            for record in result:
                node = record["g"]
                guidelines.append({
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                    "section": node.get("section", ""),
                })
            
            # 前提チェック項目
            prereqs = []
            result = session.run(prereq_query, check_id=check_item_id)
            for record in result:
                node = record["p"]
                prereqs.append({
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                })
            
            # 依存チェック項目
            dependents = []
            result = session.run(dependent_query, check_id=check_item_id)
            for record in result:
                node = record["d"]
                dependents.append({
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                })
        
        return {
            "success": True,
            "check_item": {
                "id": check_item["id"],
                "name": check_item["name"],
                "description": check_item["description"],
                "category": check_item["category"],
                "severity": check_item["severity"],
                "document_type": check_item["document_type"],
                "guideline_section": check_item.get("guideline_section", ""),
            },
            "related_sections": sections,
            "related_guidelines": guidelines,
            "prerequisite_items": prereqs,
            "dependent_items": dependents,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def find_path(
    start_node_id: str,
    end_node_id: str,
    max_depth: int = 5,
) -> dict:
    """
    2ノード間の最短パスを検索
    
    Args:
        start_node_id: 開始ノードID
        end_node_id: 終了ノードID
        max_depth: 最大探索深度
    
    Returns:
        パス情報
    """
    try:
        driver = get_neo4j_driver()
        
        query = """
        MATCH path = shortestPath(
            (start {id: $start_id})-[*1..$max_depth]-(end {id: $end_id})
        )
        RETURN path, nodes(path) as pathNodes, relationships(path) as pathRels
        LIMIT 1
        """
        
        with driver.session() as session:
            result = session.run(
                query,
                start_id=start_node_id,
                end_id=end_node_id,
                max_depth=max_depth,
            )
            
            record = result.single()
            
            if not record:
                return {
                    "success": True,
                    "found": False,
                    "message": f"No path found between {start_node_id} and {end_node_id}",
                }
            
            nodes = []
            for node in record["pathNodes"]:
                nodes.append({
                    "id": node.get("id", str(node.element_id)),
                    "labels": list(node.labels),
                    "properties": dict(node),
                })
            
            relationships = []
            for rel in record["pathRels"]:
                relationships.append({
                    "id": str(rel.element_id),
                    "type": rel.type,
                    "start_node_id": str(rel.start_node.element_id),
                    "end_node_id": str(rel.end_node.element_id),
                    "properties": dict(rel),
                })
        
        return {
            "success": True,
            "found": True,
            "start_node_id": start_node_id,
            "end_node_id": end_node_id,
            "path_length": len(relationships),
            "nodes": nodes,
            "relationships": relationships,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def get_document_structure(
    document_type: str,
) -> dict:
    """
    文書タイプの標準構造を取得
    
    Args:
        document_type: 文書タイプ（basic_design / test_plan）
    
    Returns:
        標準セクション構造
    """
    try:
        driver = get_neo4j_driver()
        
        query = """
        MATCH (dt:DocumentType {id: $doc_type})-[:HAS_SECTION]->(s:Section)
        OPTIONAL MATCH (s)-[:HAS_SUBSECTION*]->(sub:Section)
        RETURN s, COLLECT(sub) as subsections
        ORDER BY s.order
        """
        
        with driver.session() as session:
            result = session.run(query, doc_type=document_type)
            
            sections = []
            for record in result:
                section = record["s"]
                subsections = record["subsections"]
                
                section_data = {
                    "id": section.get("id", ""),
                    "name": section.get("name", ""),
                    "description": section.get("description", ""),
                    "required": section.get("required", True),
                    "order": section.get("order", 0),
                    "subsections": [],
                }
                
                for sub in subsections:
                    if sub:
                        section_data["subsections"].append({
                            "id": sub.get("id", ""),
                            "name": sub.get("name", ""),
                            "description": sub.get("description", ""),
                            "required": sub.get("required", False),
                        })
                
                sections.append(section_data)
        
        return {
            "success": True,
            "document_type": document_type,
            "total_sections": len(sections),
            "sections": sections,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@app.tool()
async def get_all_check_items(
    document_type: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """
    チェック項目一覧を取得（ローカルデータから）
    
    Args:
        document_type: 文書タイプでフィルタ
        category: カテゴリでフィルタ
    
    Returns:
        チェック項目一覧
    """
    items = CHECK_ITEMS_DATA
    
    if document_type:
        items = [i for i in items if i["document_type"] == document_type]
    
    if category:
        items = [i for i in items if i["category"] == category]
    
    return {
        "success": True,
        "filters": {
            "document_type": document_type,
            "category": category,
        },
        "total": len(items),
        "items": items,
    }


@app.tool()
async def run_cypher_query(
    query: str,
    parameters: Optional[dict] = None,
) -> dict:
    """
    カスタムCypherクエリを実行（読み取り専用）
    
    Args:
        query: Cypherクエリ（MATCH/RETURNのみ）
        parameters: クエリパラメータ
    
    Returns:
        クエリ結果
    """
    try:
        # セキュリティチェック - 読み取り専用クエリのみ許可
        query_upper = query.upper().strip()
        forbidden_keywords = ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP", "DETACH"]
        
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                return {
                    "success": False,
                    "error": f"Write operations not allowed. Forbidden keyword: {keyword}",
                }
        
        if not query_upper.startswith("MATCH"):
            return {
                "success": False,
                "error": "Query must start with MATCH",
            }
        
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run(query, parameters or {})
            
            records = []
            for record in result:
                records.append(dict(record))
        
        return {
            "success": True,
            "query": query,
            "total": len(records),
            "results": records,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ==============================================
# Resources
# ==============================================

@app.resource("knowledge://schema")
async def get_schema() -> str:
    """Neo4jスキーマ情報"""
    schema = Neo4jSchema
    
    result = "# Knowledge Graph Schema\n\n"
    
    result += "## Node Labels\n"
    for label in schema.get("node_labels", []):
        result += f"- `{label}`\n"
    
    result += "\n## Relationship Types\n"
    for rel in schema.get("relationship_types", []):
        result += f"- `{rel}`\n"
    
    result += "\n## Constraints\n"
    for constraint in schema.get("constraints", []):
        result += f"- {constraint}\n"
    
    return result


@app.resource("knowledge://check-items")
async def list_all_check_items() -> str:
    """全チェック項目一覧"""
    result = "# Check Items\n\n"
    
    # 文書タイプ別に整理
    by_type = {}
    for item in CHECK_ITEMS_DATA:
        doc_type = item["document_type"]
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(item)
    
    for doc_type, items in by_type.items():
        result += f"## {doc_type}\n\n"
        for item in items:
            result += f"### {item['id']}: {item['name']}\n"
            result += f"- Category: {item['category']}\n"
            result += f"- Severity: {item['severity']}\n"
            result += f"- Description: {item['description']}\n"
            result += f"- Guideline: {item.get('guideline_section', 'N/A')}\n\n"
    
    return result


@app.resource("knowledge://check-items/{check_item_id}")
async def get_check_item_detail(check_item_id: str) -> str:
    """チェック項目詳細"""
    for item in CHECK_ITEMS_DATA:
        if item["id"] == check_item_id:
            result = f"# {item['name']}\n\n"
            result += f"- **ID**: {item['id']}\n"
            result += f"- **Document Type**: {item['document_type']}\n"
            result += f"- **Category**: {item['category']}\n"
            result += f"- **Severity**: {item['severity']}\n"
            result += f"- **Description**: {item['description']}\n"
            result += f"- **Guideline Section**: {item.get('guideline_section', 'N/A')}\n"
            return result
    
    return f"Check item not found: {check_item_id}"


# ==============================================
# Server Entry Point
# ==============================================

def create_server():
    """サーバーインスタンスを作成"""
    return app


if __name__ == "__main__":
    app.run()
