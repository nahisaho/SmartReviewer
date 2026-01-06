"""
SmartReviewer Setup Package
Infrastructure initialization scripts
"""

from .qdrant_setup import setup_collections as setup_qdrant
from .neo4j_setup import setup_database as setup_neo4j
from .minio_setup import setup_buckets as setup_minio


__all__ = [
    "setup_qdrant",
    "setup_neo4j",
    "setup_minio",
]
