"""
MCP Server Configuration
========================

MCP Serverの設定管理
"""

import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional


class MCPServerConfig(BaseModel):
    """MCP Server設定"""
    name: str = Field(description="サーバー名")
    command: str = Field(description="起動コマンド")
    args: list[str] = Field(default_factory=list, description="コマンド引数")
    env: dict[str, str] = Field(default_factory=dict, description="環境変数")
    port: Optional[int] = Field(default=None, description="ポート番号")
    enabled: bool = Field(default=True, description="有効フラグ")
    transport: str = Field(default="stdio", description="トランスポート (stdio / sse)")


class MCPConfig(BaseModel):
    """MCP設定全体"""
    servers: dict[str, MCPServerConfig] = Field(
        default_factory=dict,
        description="サーバー設定マップ"
    )
    default_timeout: int = Field(default=30, description="デフォルトタイムアウト秒")
    log_level: str = Field(default="INFO", description="ログレベル")


def load_mcp_config(config_path: Optional[Path] = None) -> MCPConfig:
    """
    MCP設定をファイルから読み込む
    
    Args:
        config_path: 設定ファイルパス（省略時はデフォルトパス）
    
    Returns:
        MCPConfig
    """
    if config_path is None:
        # デフォルトパスを探索
        search_paths = [
            Path("mcp-servers.json"),
            Path(".mcp/servers.json"),
            Path.home() / ".config" / "smartreviewer" / "mcp-servers.json",
        ]
        
        for path in search_paths:
            if path.exists():
                config_path = path
                break
    
    if config_path is None or not config_path.exists():
        # デフォルト設定を返す
        return get_default_config()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return MCPConfig(**data)


def save_mcp_config(config: MCPConfig, config_path: Path) -> None:
    """
    MCP設定をファイルに保存
    
    Args:
        config: 設定
        config_path: 保存先パス
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)


def get_default_config() -> MCPConfig:
    """
    デフォルトMCP設定を取得
    
    Returns:
        MCPConfig
    """
    return MCPConfig(
        servers={
            "smartreviewer-core": MCPServerConfig(
                name="smartreviewer-core",
                command="python",
                args=["-m", "src.servers.core.server"],
                port=8001,
                transport="stdio",
            ),
            "smartreviewer-rag": MCPServerConfig(
                name="smartreviewer-rag",
                command="python",
                args=["-m", "src.servers.rag.server"],
                port=8002,
                transport="stdio",
            ),
            "smartreviewer-knowledge": MCPServerConfig(
                name="smartreviewer-knowledge",
                command="python",
                args=["-m", "src.servers.knowledge.server"],
                port=8003,
                transport="stdio",
            ),
        },
        default_timeout=30,
        log_level="INFO",
    )
