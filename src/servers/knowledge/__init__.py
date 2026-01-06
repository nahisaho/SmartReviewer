"""
SmartReviewer Knowledge Server
==============================

MCP Server for ontology and knowledge graph operations
"""

from src.servers.knowledge.server import app, create_server

__all__ = ["app", "create_server"]