"""
SmartReviewer - MCP Client Factory
Database and service client management
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from .settings import settings

if TYPE_CHECKING:
    from minio import Minio
    from neo4j import Driver
    from qdrant_client import QdrantClient


@lru_cache
def get_qdrant_client() -> "QdrantClient":
    """Get cached Qdrant client instance."""
    from qdrant_client import QdrantClient
    
    return QdrantClient(
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        api_key=settings.qdrant.api_key,
    )


@lru_cache
def get_neo4j_driver() -> "Driver":
    """Get cached Neo4j driver instance."""
    from neo4j import GraphDatabase
    
    return GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.user, settings.neo4j.password),
        max_connection_lifetime=settings.neo4j.max_connection_lifetime,
        max_connection_pool_size=settings.neo4j.max_connection_pool_size,
    )


@lru_cache
def get_minio_client() -> "Minio":
    """Get cached MinIO client instance."""
    from minio import Minio
    
    return Minio(
        settings.minio.endpoint,
        access_key=settings.minio.access_key,
        secret_key=settings.minio.secret_key,
        secure=settings.minio.secure,
    )


def close_all_clients() -> None:
    """Close all cached client connections."""
    # Neo4j driver needs explicit close
    if get_neo4j_driver.cache_info().currsize > 0:
        try:
            get_neo4j_driver().close()
        except Exception:
            pass
    
    # Clear caches
    get_qdrant_client.cache_clear()
    get_neo4j_driver.cache_clear()
    get_minio_client.cache_clear()
