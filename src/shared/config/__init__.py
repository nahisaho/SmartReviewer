"""
SmartReviewer - Shared Configuration
"""

from .settings import Settings, get_settings, settings
from .clients import get_qdrant_client, get_neo4j_driver, get_minio_client, close_all_clients

__all__ = [
    "Settings",
    "get_settings", 
    "settings",
    "get_qdrant_client",
    "get_neo4j_driver",
    "get_minio_client",
    "close_all_clients",
]