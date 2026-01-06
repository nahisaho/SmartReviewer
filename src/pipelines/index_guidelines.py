"""
SmartReviewer - Guideline Indexer
Index guideline documents into Vector DB for RAG

Usage:
    python -m src.pipelines.index_guidelines --input data/documents/guidelines/
"""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from src.shared.config import get_qdrant_client, settings
from src.shared.processing import (
    DocumentChunker,
    ChunkStrategy,
    get_embedding_model,
)


logger = structlog.get_logger(__name__)


class GuidelineIndexer:
    """Index guideline documents into Vector DB."""
    
    def __init__(self):
        """Initialize indexer."""
        self.qdrant = get_qdrant_client()
        self.embedder = get_embedding_model()
        self.chunker = DocumentChunker(
            chunk_size=800,
            chunk_overlap=100,
            strategy=ChunkStrategy.HYBRID,
        )
        self.collection = settings.qdrant.collection_guidelines
    
    def index_file(
        self,
        file_path: Path,
        guideline_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Index a single guideline file.
        
        Args:
            file_path: Path to guideline file
            guideline_id: Unique identifier for the guideline
            metadata: Additional metadata
            
        Returns:
            Number of chunks indexed
        """
        logger.info("Indexing guideline file", path=str(file_path), guideline_id=guideline_id)
        
        # Read file
        text = file_path.read_text(encoding="utf-8")
        
        # Chunk document
        chunks = list(self.chunker.chunk(
            text,
            document_id=guideline_id,
            base_metadata=metadata,
        ))
        
        if not chunks:
            logger.warning("No chunks generated", path=str(file_path))
            return 0
        
        logger.info("Generated chunks", count=len(chunks))
        
        # Generate embeddings
        texts = [c.content for c in chunks]
        embeddings = self.embedder.embed(texts, show_progress=True)
        
        # Prepare points for Qdrant
        from qdrant_client.models import PointStruct
        
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid4())
            
            payload = {
                "chunk_id": chunk.metadata.chunk_id,
                "document_id": chunk.metadata.document_id,
                "guideline_id": guideline_id,
                "chunk_index": chunk.metadata.chunk_index,
                "content": chunk.content,
                "section_number": chunk.metadata.section_number,
                "section_title": chunk.metadata.section_title,
                "hierarchy_level": chunk.metadata.hierarchy_level,
                "char_count": chunk.char_count,
                **(metadata or {}),
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            ))
        
        # Upsert to Qdrant
        self.qdrant.upsert(
            collection_name=self.collection,
            points=points,
        )
        
        logger.info("Indexed chunks to Qdrant", count=len(points))
        return len(points)
    
    def index_directory(
        self,
        dir_path: Path,
        extensions: list[str] | None = None,
    ) -> dict[str, int]:
        """Index all guideline files in a directory.
        
        Args:
            dir_path: Directory path
            extensions: File extensions to process (default: .txt, .md)
            
        Returns:
            Dict of file -> chunk count
        """
        extensions = extensions or [".txt", ".md"]
        results = {}
        
        for ext in extensions:
            for file_path in dir_path.glob(f"**/*{ext}"):
                if file_path.name.startswith("_") or file_path.name == "README.md":
                    continue
                
                guideline_id = file_path.stem
                
                try:
                    count = self.index_file(
                        file_path,
                        guideline_id=guideline_id,
                        metadata={"source_file": file_path.name},
                    )
                    results[str(file_path)] = count
                except Exception as e:
                    logger.error("Failed to index file", path=str(file_path), error=str(e))
                    results[str(file_path)] = -1
        
        return results
    
    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Search guidelines.
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum score threshold
            
        Returns:
            List of matching chunks with scores
        """
        query_embedding = self.embedder.embed_single(query)
        
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
        )
        
        return [
            {
                "score": r.score,
                "content": r.payload.get("content"),
                "guideline_id": r.payload.get("guideline_id"),
                "section_number": r.payload.get("section_number"),
                "section_title": r.payload.get("section_title"),
            }
            for r in results
        ]


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index guideline documents")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/documents/guidelines"),
        help="Input directory or file",
    )
    parser.add_argument(
        "--test-search",
        type=str,
        help="Test search after indexing",
    )
    
    args = parser.parse_args()
    
    indexer = GuidelineIndexer()
    
    if args.input.is_file():
        count = indexer.index_file(args.input, args.input.stem)
        print(f"Indexed {count} chunks from {args.input}")
    else:
        results = indexer.index_directory(args.input)
        total = sum(c for c in results.values() if c > 0)
        print(f"\nIndexed {total} chunks from {len(results)} files")
        for path, count in results.items():
            status = f"{count} chunks" if count >= 0 else "FAILED"
            print(f"  {path}: {status}")
    
    if args.test_search:
        print(f"\nTest search: {args.test_search}")
        results = indexer.search(args.test_search)
        for r in results:
            print(f"\n[{r['score']:.3f}] {r['section_number']} {r['section_title']}")
            print(f"  {r['content'][:200]}...")


if __name__ == "__main__":
    main()
