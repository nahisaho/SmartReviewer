"""
SmartReviewer - Data Pipelines Package
Document processing and indexing pipelines
"""

from .index_guidelines import GuidelineIndexer

__all__ = [
    "GuidelineIndexer",
]
