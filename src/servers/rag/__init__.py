"""
SmartReviewer RAG Server
========================

MCP Server for vector/graph search and hybrid retrieval
"""

from src.servers.rag.server import app, create_server

__all__ = ["app", "create_server"]