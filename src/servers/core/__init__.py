"""
SmartReviewer Core MCP Server
=============================

文書管理・レビュー結果管理を担当するMCPサーバー

Tools:
  - upload_document: 文書アップロード・解析
  - get_check_items: チェック項目取得
  - create_report: レビュー結果レポート生成

Resources:
  - documents/*: アップロード済み文書
  - results/*: レビュー結果
  - check-items: チェック項目マスター
"""

from src.servers.core.server import create_server, app

__all__ = ["create_server", "app"]
