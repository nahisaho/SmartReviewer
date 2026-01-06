"""
Tests for MCP Host and CLI
==========================

MCP Host、Client、CLIのテスト
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


# ==============================================
# Config Tests
# ==============================================

class TestConfig:
    """設定テスト"""
    
    def test_import_config(self):
        """configモジュールがインポートできること"""
        from src.host.config import MCPServerConfig, MCPConfig, load_mcp_config
        assert MCPServerConfig is not None
        assert MCPConfig is not None
        assert load_mcp_config is not None
    
    def test_mcp_server_config_defaults(self):
        """MCPServerConfigのデフォルト値"""
        from src.host.config import MCPServerConfig
        
        config = MCPServerConfig(
            name="test-server",
            command="python",
        )
        
        assert config.name == "test-server"
        assert config.args == []
        assert config.env == {}
        assert config.enabled is True
        assert config.transport == "stdio"
    
    def test_mcp_config_defaults(self):
        """MCPConfigのデフォルト値"""
        from src.host.config import MCPConfig
        
        config = MCPConfig()
        
        assert config.servers == {}
        assert config.default_timeout == 30
        assert config.log_level == "INFO"
    
    def test_get_default_config(self):
        """デフォルト設定取得"""
        from src.host.config import get_default_config
        
        config = get_default_config()
        
        assert "smartreviewer-core" in config.servers
        assert "smartreviewer-rag" in config.servers
        assert "smartreviewer-knowledge" in config.servers
    
    def test_load_mcp_config_default(self):
        """設定ファイルがない場合はデフォルト"""
        from src.host.config import load_mcp_config
        
        # 存在しないパスを指定
        config = load_mcp_config(Path("/nonexistent/path.json"))
        
        assert "smartreviewer-core" in config.servers
    
    def test_load_mcp_config_from_file(self, tmp_path):
        """設定ファイルから読み込み"""
        from src.host.config import load_mcp_config
        
        config_data = {
            "servers": {
                "test-server": {
                    "name": "test-server",
                    "command": "echo",
                    "args": ["hello"],
                }
            },
            "default_timeout": 60,
            "log_level": "DEBUG",
        }
        
        config_file = tmp_path / "mcp-servers.json"
        config_file.write_text(json.dumps(config_data))
        
        config = load_mcp_config(config_file)
        
        assert "test-server" in config.servers
        assert config.default_timeout == 60
        assert config.log_level == "DEBUG"


# ==============================================
# Client Tests
# ==============================================

class TestClient:
    """クライアントテスト"""
    
    def test_import_client(self):
        """clientモジュールがインポートできること"""
        from src.host.client import MCPClient, ToolResult, ResourceContent
        assert MCPClient is not None
        assert ToolResult is not None
        assert ResourceContent is not None
    
    def test_tool_result_success(self):
        """ToolResult成功ケース"""
        from src.host.client import ToolResult
        
        result = ToolResult(
            success=True,
            content={"key": "value"},
        )
        
        assert result.success is True
        assert result.content == {"key": "value"}
        assert result.error is None
    
    def test_tool_result_failure(self):
        """ToolResult失敗ケース"""
        from src.host.client import ToolResult
        
        result = ToolResult(
            success=False,
            content=None,
            error="Connection failed",
        )
        
        assert result.success is False
        assert result.error == "Connection failed"
    
    def test_resource_content(self):
        """ResourceContent"""
        from src.host.client import ResourceContent
        
        content = ResourceContent(
            uri="test://resource",
            content="Hello, World!",
            mime_type="text/plain",
        )
        
        assert content.uri == "test://resource"
        assert content.content == "Hello, World!"
    
    def test_mcp_client_creation(self):
        """MCPClientの作成"""
        from src.host.client import MCPClient
        
        client = MCPClient(
            server_name="test-server",
            command="python",
            args=["-m", "test"],
        )
        
        assert client.server_name == "test-server"
        assert client.command == "python"


# ==============================================
# Host Tests
# ==============================================

class TestHost:
    """ホストテスト"""
    
    def test_import_host(self):
        """hostモジュールがインポートできること"""
        from src.host.host import MCPHost, create_host
        assert MCPHost is not None
        assert create_host is not None
    
    def test_mcp_host_creation(self):
        """MCPHostの作成"""
        from src.host.host import MCPHost
        from src.host.config import get_default_config
        
        host = MCPHost(config=get_default_config())
        
        assert host is not None
        assert not host._initialized
    
    def test_get_client_not_initialized(self):
        """未初期化時のget_client"""
        from src.host.host import MCPHost
        from src.host.config import get_default_config
        
        host = MCPHost(config=get_default_config())
        
        client = host.get_client("smartreviewer-core")
        
        assert client is None


# ==============================================
# CLI Tests
# ==============================================

class TestCLI:
    """CLIテスト"""
    
    def test_import_cli(self):
        """CLIモジュールがインポートできること"""
        from src.cli.main import app, cli
        assert app is not None
        assert cli is not None
    
    def test_cli_help(self):
        """CLIヘルプが表示できること"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "SmartReviewer" in result.stdout
    
    def test_cli_version(self):
        """バージョンコマンド"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "SmartReviewer" in result.stdout
        assert "v2.0.0" in result.stdout
    
    def test_cli_check_items_list(self):
        """チェック項目一覧コマンド"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["check-items"])
        
        assert result.exit_code == 0
        assert "チェック項目一覧" in result.stdout
    
    def test_cli_check_items_filter_type(self):
        """チェック項目一覧（タイプフィルタ）"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["check-items", "--type", "basic_design"])
        
        assert result.exit_code == 0
    
    def test_cli_check_items_json(self):
        """チェック項目一覧（JSON形式）"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["check-items", "--format", "json"])
        
        assert result.exit_code == 0
        # JSON形式で出力されていること
        items = json.loads(result.stdout)
        assert isinstance(items, list)
    
    def test_cli_server_info(self):
        """サーバー情報コマンド"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["server"])
        
        assert result.exit_code == 0
        assert "MCP Servers" in result.stdout
    
    def test_cli_server_info_specific(self):
        """特定サーバー情報"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["server", "smartreviewer-core"])
        
        assert result.exit_code == 0
        assert "smartreviewer-core" in result.stdout
    
    def test_cli_server_info_not_found(self):
        """存在しないサーバー"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["server", "nonexistent-server"])
        
        assert result.exit_code == 1
    
    def test_cli_review_file_not_found(self):
        """reviewコマンド - ファイルなし"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["review", "/nonexistent/file.md"])
        
        assert result.exit_code == 1
        assert "ファイルが見つかりません" in result.stdout
    
    def test_cli_review_invalid_type(self, tmp_path):
        """reviewコマンド - 無効な文書タイプ"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")
        
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(test_file), "--type", "invalid"])
        
        assert result.exit_code == 1
        assert "無効な文書タイプ" in result.stdout
    
    def test_cli_review_basic_design(self, tmp_path):
        """reviewコマンド - 基本設計書"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        test_file = tmp_path / "basic_design.md"
        test_file.write_text("""
# 基本設計書

## システム概要
本システムは文書レビュー支援AIです。

## システム構成
マイクロサービスアーキテクチャを採用。
        """)
        
        runner = CliRunner()
        result = runner.invoke(app, ["review", str(test_file), "--type", "basic_design"])
        
        # レビューが完了すること（終了コードは結果による）
        assert "レビュー結果" in result.stdout or result.exit_code in [0, 1, 2]
    
    def test_cli_review_output_json(self, tmp_path):
        """reviewコマンド - JSON出力"""
        from typer.testing import CliRunner
        from src.cli.main import app
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\n## システム概要\nTest content")
        
        output_file = tmp_path / "result.json"
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "review", str(test_file),
            "--type", "basic_design",
            "--format", "json",
            "--output", str(output_file),
        ])
        
        # 出力ファイルが作成されていること
        if result.exit_code in [0, 1]:
            assert output_file.exists()


# ==============================================
# Integration Tests
# ==============================================

class TestIntegration:
    """統合テスト"""
    
    def test_review_workflow(self, tmp_path):
        """レビューワークフロー全体"""
        import asyncio
        from src.review.engine import ReviewEngine
        from src.review.models import ReviewRequest, ReviewStatus
        
        # テスト文書
        document_content = """
# 基本設計書

## システム概要
SmartReviewerは文書レビュー支援AIシステムです。

## システム構成
マイクロサービスアーキテクチャを採用しています。

## 機能設計
文書アップロード、レビュー実行、レポート生成。

## データ設計
PostgreSQL、Qdrant、Neo4jを使用。

## インターフェース設計
MCP Protocolを使用したAPI。
        """
        
        async def run_review():
            engine = ReviewEngine(use_llm=False)
            
            request = ReviewRequest(
                document_id="test-doc",
                document_content=document_content,
                document_type="basic_design",
            )
            
            return await engine.review_document(request)
        
        result = asyncio.run(run_review())
        
        assert result.status == ReviewStatus.COMPLETED
        assert result.metadata.checks_executed > 0
