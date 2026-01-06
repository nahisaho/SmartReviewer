"""
MCP Client
==========

MCP Serverとの通信クライアント
"""

import asyncio
import json
from typing import Any, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


@dataclass
class ToolResult:
    """Tool実行結果"""
    success: bool
    content: Any
    error: Optional[str] = None


@dataclass
class ResourceContent:
    """Resource内容"""
    uri: str
    content: str
    mime_type: str = "text/plain"


@dataclass
class MCPClient:
    """
    MCP Client
    
    MCP Serverと通信するためのクライアント
    """
    server_name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    
    _session: Optional[ClientSession] = field(default=None, init=False)
    _connected: bool = field(default=False, init=False)
    
    async def connect(self) -> None:
        """サーバーに接続"""
        if self._connected:
            return
        
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env if self.env else None,
        )
        
        # stdio_clientはコンテキストマネージャとして使用
        # ここでは接続情報を保持
        self._server_params = server_params
        self._connected = True
    
    async def disconnect(self) -> None:
        """サーバーから切断"""
        self._session = None
        self._connected = False
    
    @asynccontextmanager
    async def session(self):
        """セッションコンテキストマネージャ"""
        if not self._connected:
            await self.connect()
        
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    
    async def list_tools(self) -> list[dict]:
        """
        利用可能なToolを一覧取得
        
        Returns:
            Tool情報のリスト
        """
        async with self.session() as session:
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in result.tools
            ]
    
    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Toolを実行
        
        Args:
            name: Tool名
            arguments: 引数
        
        Returns:
            ToolResult
        """
        try:
            async with self.session() as session:
                result = await session.call_tool(name, arguments)
                
                # 結果を解析
                content = []
                for item in result.content:
                    if hasattr(item, "text"):
                        content.append(item.text)
                    elif hasattr(item, "data"):
                        content.append(item.data)
                
                # 単一結果の場合はそのまま返す
                if len(content) == 1:
                    try:
                        # JSONとしてパース試行
                        return ToolResult(
                            success=True,
                            content=json.loads(content[0]),
                        )
                    except (json.JSONDecodeError, TypeError):
                        return ToolResult(
                            success=True,
                            content=content[0],
                        )
                
                return ToolResult(success=True, content=content)
        
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
            )
    
    async def list_resources(self) -> list[dict]:
        """
        利用可能なResourceを一覧取得
        
        Returns:
            Resource情報のリスト
        """
        async with self.session() as session:
            result = await session.list_resources()
            return [
                {
                    "uri": res.uri,
                    "name": res.name,
                    "description": getattr(res, "description", ""),
                    "mime_type": getattr(res, "mimeType", "text/plain"),
                }
                for res in result.resources
            ]
    
    async def read_resource(self, uri: str) -> ResourceContent:
        """
        Resourceを読み取る
        
        Args:
            uri: Resource URI
        
        Returns:
            ResourceContent
        """
        async with self.session() as session:
            result = await session.read_resource(uri)
            
            content = ""
            mime_type = "text/plain"
            
            for item in result.contents:
                if hasattr(item, "text"):
                    content = item.text
                    mime_type = getattr(item, "mimeType", "text/plain")
                elif hasattr(item, "blob"):
                    content = item.blob
                    mime_type = getattr(item, "mimeType", "application/octet-stream")
            
            return ResourceContent(
                uri=uri,
                content=content,
                mime_type=mime_type,
            )
    
    async def list_prompts(self) -> list[dict]:
        """
        利用可能なPromptを一覧取得
        
        Returns:
            Prompt情報のリスト
        """
        async with self.session() as session:
            result = await session.list_prompts()
            return [
                {
                    "name": prompt.name,
                    "description": getattr(prompt, "description", ""),
                    "arguments": getattr(prompt, "arguments", []),
                }
                for prompt in result.prompts
            ]
    
    async def get_prompt(
        self,
        name: str,
        arguments: dict[str, str],
    ) -> str:
        """
        Promptを取得
        
        Args:
            name: Prompt名
            arguments: 引数
        
        Returns:
            展開されたPrompt文字列
        """
        async with self.session() as session:
            result = await session.get_prompt(name, arguments)
            
            messages = []
            for msg in result.messages:
                if hasattr(msg.content, "text"):
                    messages.append(msg.content.text)
            
            return "\n".join(messages)
