"""
SmartReviewer - Document Processing Package
Chunking, embedding, and document parsing utilities
"""

from .chunking import (
    Chunk,
    ChunkMetadata,
    ChunkStrategy,
    DocumentChunker,
    chunk_document,
)
from .embedding import (
    EmbeddingCache,
    EmbeddingModel,
    EmbeddingResult,
    embed_text,
    embed_texts,
    get_embedding_model,
)

__all__ = [
    # Chunking
    "Chunk",
    "ChunkMetadata",
    "ChunkStrategy",
    "DocumentChunker",
    "chunk_document",
    # Embedding
    "EmbeddingCache",
    "EmbeddingModel",
    "EmbeddingResult",
    "embed_text",
    "embed_texts",
    "get_embedding_model",
]
