"""
MCP Host
========

複数MCP Serverを統合管理するホストアプリケーション
"""

import asyncio
from typing import Any, Optional
from dataclasses import dataclass, field

from src.host.config import MCPConfig, MCPServerConfig, load_mcp_config
from src.host.client import MCPClient, ToolResult, ResourceContent


@dataclass
class MCPHost:
    """
    MCP Host
    
    複数のMCP Serverを統合管理し、統一APIを提供する
    """
    config: MCPConfig = field(default_factory=load_mcp_config)
    
    _clients: dict[str, MCPClient] = field(default_factory=dict, init=False)
    _initialized: bool = field(default=False, init=False)
    
    async def initialize(self) -> None:
        """
        ホストを初期化し、設定されたサーバーに接続
        """
        if self._initialized:
            return
        
        for name, server_config in self.config.servers.items():
            if not server_config.enabled:
                continue
            
            client = MCPClient(
                server_name=name,
                command=server_config.command,
                args=server_config.args,
                env=server_config.env,
            )
            
            await client.connect()
            self._clients[name] = client
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        """
        全サーバーから切断
        """
        for client in self._clients.values():
            await client.disconnect()
        
        self._clients.clear()
        self._initialized = False
    
    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """
        指定サーバーのクライアントを取得
        
        Args:
            server_name: サーバー名
        
        Returns:
            MCPClient または None
        """
        return self._clients.get(server_name)
    
    async def list_all_tools(self) -> dict[str, list[dict]]:
        """
        全サーバーのToolを一覧取得
        
        Returns:
            サーバー名 -> Tool一覧のマップ
        """
        result = {}
        
        for name, client in self._clients.items():
            try:
                tools = await client.list_tools()
                result[name] = tools
            except Exception as e:
                result[name] = [{"error": str(e)}]
        
        return result
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        指定サーバーのToolを実行
        
        Args:
            server_name: サーバー名
            tool_name: Tool名
            arguments: 引数
        
        Returns:
            ToolResult
        """
        client = self._clients.get(server_name)
        if not client:
            return ToolResult(
                success=False,
                content=None,
                error=f"Server not found: {server_name}",
            )
        
        return await client.call_tool(tool_name, arguments)
    
    async def list_all_resources(self) -> dict[str, list[dict]]:
        """
        全サーバーのResourceを一覧取得
        
        Returns:
            サーバー名 -> Resource一覧のマップ
        """
        result = {}
        
        for name, client in self._clients.items():
            try:
                resources = await client.list_resources()
                result[name] = resources
            except Exception as e:
                result[name] = [{"error": str(e)}]
        
        return result
    
    async def read_resource(
        self,
        server_name: str,
        uri: str,
    ) -> ResourceContent:
        """
        指定サーバーのResourceを読み取る
        
        Args:
            server_name: サーバー名
            uri: Resource URI
        
        Returns:
            ResourceContent
        """
        client = self._clients.get(server_name)
        if not client:
            return ResourceContent(
                uri=uri,
                content=f"Error: Server not found: {server_name}",
                mime_type="text/plain",
            )
        
        return await client.read_resource(uri)
    
    # ==============================================
    # High-level APIs (SmartReviewer specific)
    # ==============================================
    
    async def upload_document(
        self,
        content: str,
        filename: str,
        document_type: str,
        title: str = "",
        version: str = "",
    ) -> ToolResult:
        """
        文書をアップロード（smartreviewer-core）
        
        Args:
            content: 文書内容
            filename: ファイル名
            document_type: 文書タイプ
            title: タイトル
            version: バージョン
        
        Returns:
            ToolResult
        """
        return await self.call_tool(
            server_name="smartreviewer-core",
            tool_name="upload_document",
            arguments={
                "content": content,
                "filename": filename,
                "document_type": document_type,
                "title": title,
                "version": version,
            },
        )
    
    async def review_document(
        self,
        document_id: str,
        check_item_ids: Optional[list[str]] = None,
        parallel: bool = True,
    ) -> ToolResult:
        """
        文書をレビュー（smartreviewer-core）
        
        Args:
            document_id: 文書ID
            check_item_ids: チェック項目IDリスト
            parallel: 並列実行フラグ
        
        Returns:
            ToolResult
        """
        arguments = {
            "document_id": document_id,
            "parallel": parallel,
        }
        
        if check_item_ids:
            arguments["check_item_ids"] = check_item_ids
        
        return await self.call_tool(
            server_name="smartreviewer-core",
            tool_name="review_document",
            arguments=arguments,
        )
    
    async def get_check_items(
        self,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> ToolResult:
        """
        チェック項目を取得（smartreviewer-core）
        
        Args:
            document_type: 文書タイプ
            category: カテゴリ
        
        Returns:
            ToolResult
        """
        arguments = {}
        if document_type:
            arguments["document_type"] = document_type
        if category:
            arguments["category"] = category
        
        return await self.call_tool(
            server_name="smartreviewer-core",
            tool_name="get_check_items",
            arguments=arguments,
        )
    
    async def search_guidelines(
        self,
        query: str,
        top_k: int = 5,
    ) -> ToolResult:
        """
        ガイドラインを検索（smartreviewer-rag）
        
        Args:
            query: 検索クエリ
            top_k: 取得件数
        
        Returns:
            ToolResult
        """
        return await self.call_tool(
            server_name="smartreviewer-rag",
            tool_name="vector_search",
            arguments={
                "query": query,
                "top_k": top_k,
            },
        )
    
    async def get_knowledge_schema(self) -> ResourceContent:
        """
        知識グラフスキーマを取得（smartreviewer-knowledge）
        
        Returns:
            ResourceContent
        """
        return await self.read_resource(
            server_name="smartreviewer-knowledge",
            uri="knowledge://schema",
        )


# ==============================================
# Factory Function
# ==============================================

async def create_host(config: Optional[MCPConfig] = None) -> MCPHost:
    """
    MCPHostを作成して初期化
    
    Args:
        config: MCP設定（省略時はデフォルト）
    
    Returns:
        初期化済みMCPHost
    """
    if config is None:
        config = load_mcp_config()
    
    host = MCPHost(config=config)
    await host.initialize()
    return host
