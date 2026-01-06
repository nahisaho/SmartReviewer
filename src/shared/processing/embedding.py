"""
SmartReviewer - Embedding Module
Text embedding generation using sentence-transformers

Supports:
- Batch embedding generation
- Caching for efficiency
- Multiple model support (optimized for Japanese)
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import structlog

from ..config import settings


logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    embedding: list[float]
    model: str
    dimensions: int
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "embedding": self.embedding,
            "model": self.model,
            "dimensions": self.dimensions,
        }


class EmbeddingModel:
    """Embedding model wrapper.
    
    Usage:
        model = EmbeddingModel()
        embeddings = model.embed(["テキスト1", "テキスト2"])
    """
    
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str | None = None):
        """Singleton pattern for model caching."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name: str | None = None):
        """Initialize embedding model.
        
        Args:
            model_name: Model name/path. Defaults to settings.
        """
        self.model_name = model_name or settings.embedding.model_name
        self.batch_size = settings.embedding.batch_size
        self.max_length = settings.embedding.max_length
        self.normalize = settings.embedding.normalize
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the embedding model."""
        if self._model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("Loading embedding model", model=self.model_name)
            self._model = SentenceTransformer(
                self.model_name,
                trust_remote_code=True,
            )
            self._model.max_seq_length = self.max_length
            
            # Get vector dimension
            self._dimensions = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Embedding model loaded",
                model=self.model_name,
                dimensions=self._dimensions,
            )
            
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions
    
    def embed(
        self,
        texts: list[str],
        show_progress: bool = False,
    ) -> list[list[float]]:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        logger.debug("Generating embeddings", count=len(texts))
        
        # Add instruction prefix for e5 models
        if "e5" in self.model_name.lower():
            texts = [f"query: {t}" if len(t) < 200 else f"passage: {t}" for t in texts]
        
        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.normalize,
            convert_to_numpy=True,
        )
        
        return embeddings.tolist()
    
    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embed([text])[0]
    
    def embed_with_metadata(
        self,
        texts: list[str],
    ) -> list[EmbeddingResult]:
        """Generate embeddings with metadata.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of EmbeddingResult objects
        """
        embeddings = self.embed(texts)
        
        return [
            EmbeddingResult(
                text=text,
                embedding=emb,
                model=self.model_name,
                dimensions=self._dimensions,
            )
            for text, emb in zip(texts, embeddings)
        ]
    
    def similarity(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:
        """Compute similarity between query and documents.
        
        Args:
            query: Query text
            documents: List of document texts
            
        Returns:
            List of similarity scores
        """
        query_emb = np.array(self.embed_single(query))
        doc_embs = np.array(self.embed(documents))
        
        # Cosine similarity (embeddings are normalized)
        similarities = np.dot(doc_embs, query_emb)
        
        return similarities.tolist()


class EmbeddingCache:
    """Cache for embeddings to avoid recomputation."""
    
    def __init__(self, cache_dir: Path | str | None = None):
        """Initialize cache.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/embeddings/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, list[float]] = {}
    
    def _hash_text(self, text: str, model: str) -> str:
        """Generate hash for text+model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, text: str, model: str) -> list[float] | None:
        """Get cached embedding.
        
        Args:
            text: Original text
            model: Model name
            
        Returns:
            Cached embedding or None
        """
        key = self._hash_text(text, model)
        
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.npy"
        if cache_file.exists():
            embedding = np.load(cache_file).tolist()
            self._memory_cache[key] = embedding
            return embedding
        
        return None
    
    def set(self, text: str, model: str, embedding: list[float]) -> None:
        """Cache embedding.
        
        Args:
            text: Original text
            model: Model name
            embedding: Embedding vector
        """
        key = self._hash_text(text, model)
        
        # Memory cache
        self._memory_cache[key] = embedding
        
        # File cache
        cache_file = self.cache_dir / f"{key}.npy"
        np.save(cache_file, np.array(embedding))
    
    def clear(self) -> None:
        """Clear all caches."""
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.npy"):
            f.unlink()


# Convenience functions
def get_embedding_model() -> EmbeddingModel:
    """Get the singleton embedding model instance."""
    return EmbeddingModel()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using default model.
    
    Args:
        texts: Texts to embed
        
    Returns:
        List of embedding vectors
    """
    return get_embedding_model().embed(texts)


def embed_text(text: str) -> list[float]:
    """Embed single text using default model.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector
    """
    return get_embedding_model().embed_single(text)
