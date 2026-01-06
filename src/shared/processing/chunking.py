"""
SmartReviewer - Document Chunking Module
Text chunking with semantic boundaries for RAG

Supports multiple chunking strategies:
- Fixed size with overlap
- Semantic (sentence/paragraph boundaries)
- Section-based (for structured documents)
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator
from uuid import uuid4

import structlog


logger = structlog.get_logger(__name__)


class ChunkStrategy(str, Enum):
    """Chunking strategy types."""
    FIXED = "fixed"           # Fixed size with overlap
    SEMANTIC = "semantic"     # Sentence/paragraph boundaries
    SECTION = "section"       # Document section boundaries
    HYBRID = "hybrid"         # Section + semantic fallback


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    document_id: str
    chunk_index: int
    start_char: int
    end_char: int
    section_number: str | None = None
    section_title: str | None = None
    hierarchy_level: int = 0
    parent_section: str | None = None
    content_type: str = "text"  # text, table, list, code
    extra: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """A document chunk with content and metadata."""
    content: str
    metadata: ChunkMetadata
    
    @property
    def char_count(self) -> int:
        return len(self.content)
    
    @property
    def word_count(self) -> int:
        # Japanese word count approximation
        return len(self.content.replace(" ", "").replace("\n", ""))


class DocumentChunker:
    """Document chunking with multiple strategies.
    
    Usage:
        chunker = DocumentChunker(
            chunk_size=800,
            chunk_overlap=100,
            strategy=ChunkStrategy.HYBRID
        )
        chunks = list(chunker.chunk(document_text, document_id="doc-001"))
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        strategy: ChunkStrategy = ChunkStrategy.HYBRID,
        min_chunk_size: int = 100,
    ):
        """Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy to use
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.min_chunk_size = min_chunk_size
        
        # Japanese section patterns
        self._section_patterns = [
            # "第N章", "第N節", "N.N.N" etc.
            re.compile(r'^(第[0-9０-９一二三四五六七八九十百]+[章節項])', re.MULTILINE),
            re.compile(r'^([0-9]+\.(?:[0-9]+\.)*[0-9]*)\s+(.+)$', re.MULTILINE),
            re.compile(r'^(#+)\s+(.+)$', re.MULTILINE),  # Markdown headers
        ]
        
        # Sentence boundaries (Japanese)
        self._sentence_end = re.compile(r'([。！？\n])')
        
        # Paragraph boundaries
        self._paragraph_sep = re.compile(r'\n\s*\n')
    
    def chunk(
        self,
        text: str,
        document_id: str,
        base_metadata: dict | None = None,
    ) -> Iterator[Chunk]:
        """Chunk document text.
        
        Args:
            text: Document text to chunk
            document_id: Document identifier
            base_metadata: Additional metadata to include
            
        Yields:
            Chunk objects
        """
        if self.strategy == ChunkStrategy.FIXED:
            yield from self._chunk_fixed(text, document_id, base_metadata)
        elif self.strategy == ChunkStrategy.SEMANTIC:
            yield from self._chunk_semantic(text, document_id, base_metadata)
        elif self.strategy == ChunkStrategy.SECTION:
            yield from self._chunk_section(text, document_id, base_metadata)
        else:  # HYBRID
            yield from self._chunk_hybrid(text, document_id, base_metadata)
    
    def _chunk_fixed(
        self,
        text: str,
        document_id: str,
        base_metadata: dict | None,
    ) -> Iterator[Chunk]:
        """Fixed-size chunking with overlap."""
        text_len = len(text)
        start = 0
        chunk_index = 0
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence end near chunk boundary
                search_start = max(end - 100, start)
                search_text = text[search_start:end + 50]
                
                matches = list(self._sentence_end.finditer(search_text))
                if matches:
                    # Use the last sentence end before target
                    for match in reversed(matches):
                        candidate = search_start + match.end()
                        if candidate <= end + 20:  # Allow slight overshoot
                            end = candidate
                            break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                yield Chunk(
                    content=chunk_text,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document_id}-{chunk_index:04d}",
                        document_id=document_id,
                        chunk_index=chunk_index,
                        start_char=start,
                        end_char=end,
                        extra=base_metadata or {},
                    ),
                )
                chunk_index += 1
            
            start = end - self.chunk_overlap
            if start >= end:
                start = end
    
    def _chunk_semantic(
        self,
        text: str,
        document_id: str,
        base_metadata: dict | None,
    ) -> Iterator[Chunk]:
        """Semantic chunking based on paragraphs and sentences."""
        paragraphs = self._paragraph_sep.split(text)
        
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # If paragraph alone exceeds chunk size, split by sentences
            if para_size > self.chunk_size:
                # Flush current chunk first
                if current_chunk:
                    yield self._create_chunk(
                        "\n\n".join(current_chunk),
                        document_id,
                        chunk_index,
                        start_char,
                        base_metadata,
                    )
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                yield from self._split_paragraph(
                    para, document_id, chunk_index, start_char, base_metadata
                )
                chunk_index += 1
                start_char += para_size + 2
                continue
            
            # Check if adding paragraph exceeds limit
            if current_size + para_size > self.chunk_size and current_chunk:
                yield self._create_chunk(
                    "\n\n".join(current_chunk),
                    document_id,
                    chunk_index,
                    start_char,
                    base_metadata,
                )
                chunk_index += 1
                start_char += current_size
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size + 2  # +2 for paragraph separator
        
        # Flush remaining
        if current_chunk:
            yield self._create_chunk(
                "\n\n".join(current_chunk),
                document_id,
                chunk_index,
                start_char,
                base_metadata,
            )
    
    def _chunk_section(
        self,
        text: str,
        document_id: str,
        base_metadata: dict | None,
    ) -> Iterator[Chunk]:
        """Section-based chunking for structured documents."""
        sections = self._extract_sections(text)
        chunk_index = 0
        
        for section in sections:
            section_text = section["content"]
            section_meta = {
                "section_number": section.get("number"),
                "section_title": section.get("title"),
                "hierarchy_level": section.get("level", 0),
            }
            
            if len(section_text) <= self.chunk_size:
                yield Chunk(
                    content=section_text,
                    metadata=ChunkMetadata(
                        chunk_id=f"{document_id}-{chunk_index:04d}",
                        document_id=document_id,
                        chunk_index=chunk_index,
                        start_char=section["start"],
                        end_char=section["end"],
                        section_number=section_meta["section_number"],
                        section_title=section_meta["section_title"],
                        hierarchy_level=section_meta["hierarchy_level"],
                        extra=base_metadata or {},
                    ),
                )
                chunk_index += 1
            else:
                # Large section: use semantic chunking
                for chunk in self._chunk_semantic(
                    section_text, document_id, {**(base_metadata or {}), **section_meta}
                ):
                    chunk.metadata.chunk_index = chunk_index
                    chunk.metadata.chunk_id = f"{document_id}-{chunk_index:04d}"
                    chunk.metadata.section_number = section_meta["section_number"]
                    chunk.metadata.section_title = section_meta["section_title"]
                    chunk.metadata.hierarchy_level = section_meta["hierarchy_level"]
                    yield chunk
                    chunk_index += 1
    
    def _chunk_hybrid(
        self,
        text: str,
        document_id: str,
        base_metadata: dict | None,
    ) -> Iterator[Chunk]:
        """Hybrid chunking: try section-based, fall back to semantic."""
        sections = self._extract_sections(text)
        
        if len(sections) > 1:
            # Document has sections, use section-based
            yield from self._chunk_section(text, document_id, base_metadata)
        else:
            # No clear sections, use semantic
            yield from self._chunk_semantic(text, document_id, base_metadata)
    
    def _extract_sections(self, text: str) -> list[dict]:
        """Extract sections from document."""
        sections = []
        
        # Find all section headers
        headers = []
        for pattern in self._section_patterns:
            for match in pattern.finditer(text):
                headers.append({
                    "start": match.start(),
                    "end": match.end(),
                    "match": match,
                })
        
        # Sort by position
        headers.sort(key=lambda x: x["start"])
        
        if not headers:
            # No sections found, return entire text as one section
            return [{
                "number": None,
                "title": None,
                "level": 0,
                "content": text,
                "start": 0,
                "end": len(text),
            }]
        
        # Extract sections
        for i, header in enumerate(headers):
            match = header["match"]
            groups = match.groups()
            
            # Determine section info based on pattern
            if groups[0].startswith("第"):
                number = groups[0]
                title = text[header["end"]:].split("\n")[0].strip() if header["end"] < len(text) else ""
                level = 1 if "章" in number else 2 if "節" in number else 3
            elif groups[0].startswith("#"):
                number = None
                title = groups[1] if len(groups) > 1 else ""
                level = len(groups[0])
            else:
                number = groups[0]
                title = groups[1] if len(groups) > 1 else ""
                level = number.count(".") + 1
            
            # Section content is from this header to next (or end)
            content_start = header["start"]
            content_end = headers[i + 1]["start"] if i + 1 < len(headers) else len(text)
            
            sections.append({
                "number": number,
                "title": title,
                "level": level,
                "content": text[content_start:content_end].strip(),
                "start": content_start,
                "end": content_end,
            })
        
        return sections
    
    def _split_paragraph(
        self,
        para: str,
        document_id: str,
        chunk_index: int,
        start_char: int,
        base_metadata: dict | None,
    ) -> Iterator[Chunk]:
        """Split a large paragraph by sentences."""
        sentences = self._sentence_end.split(para)
        
        current = []
        current_size = 0
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            if current_size + len(sent) > self.chunk_size and current:
                yield self._create_chunk(
                    "".join(current),
                    document_id,
                    chunk_index,
                    start_char,
                    base_metadata,
                )
                current = []
                current_size = 0
            
            current.append(sent)
            current_size += len(sent)
        
        if current:
            yield self._create_chunk(
                "".join(current),
                document_id,
                chunk_index,
                start_char,
                base_metadata,
            )
    
    def _create_chunk(
        self,
        content: str,
        document_id: str,
        chunk_index: int,
        start_char: int,
        base_metadata: dict | None,
    ) -> Chunk:
        """Create a chunk with metadata."""
        return Chunk(
            content=content,
            metadata=ChunkMetadata(
                chunk_id=f"{document_id}-{chunk_index:04d}",
                document_id=document_id,
                chunk_index=chunk_index,
                start_char=start_char,
                end_char=start_char + len(content),
                extra=base_metadata or {},
            ),
        )


# Convenience function
def chunk_document(
    text: str,
    document_id: str,
    chunk_size: int = 800,
    overlap: int = 100,
    strategy: str = "hybrid",
) -> list[Chunk]:
    """Chunk a document with default settings.
    
    Args:
        text: Document text
        document_id: Document identifier
        chunk_size: Target chunk size
        overlap: Chunk overlap
        strategy: Chunking strategy (fixed, semantic, section, hybrid)
        
    Returns:
        List of Chunk objects
    """
    chunker = DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        strategy=ChunkStrategy(strategy),
    )
    return list(chunker.chunk(text, document_id))
