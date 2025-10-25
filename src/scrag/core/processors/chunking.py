"""Content chunking processor for RAG optimization."""

from __future__ import annotations

from typing import Dict, Any, List
import re
import logging

from scrag.core.processors.base import BaseProcessor, ProcessingContext, ProcessingResult

logger = logging.getLogger(__name__)


class ChunkingProcessor(BaseProcessor):
    """Processor that splits content into RAG-optimized chunks."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        preserve_sentences: bool = True,
        min_chunk_size: int = 50
    ) -> None:
        super().__init__(name="chunking")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_sentences = preserve_sentences
        self.min_chunk_size = min_chunk_size
    
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Split content into chunks with metadata preservation."""
        try:
            chunks = self._split_into_chunks(context.content)
            
            # Create metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = {
                    "chunk_id": i,
                    "chunk_size": len(chunk),
                    "total_chunks": len(chunks),
                    "overlap_size": self.chunk_overlap if i > 0 else 0,
                    **context.metadata
                }
                chunk_metadata.append(chunk_meta)
            
            # Join chunks for processing result (can be split again later)
            processed_content = "\n\n".join(chunks)
            
            result_metadata = {
                "chunks": chunks,
                "chunk_metadata": chunk_metadata,
                "chunk_count": len(chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "preserve_sentences": self.preserve_sentences,
                **context.metadata
            }
            
            return ProcessingResult(
                content=processed_content,
                metadata=result_metadata
            )
            
        except Exception as e:
            logger.error(f"Error chunking content: {e}")
            return ProcessingResult(
                content=context.content,
                metadata={**context.metadata, "chunking_error": str(e)}
            )
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []
        
        if self.preserve_sentences:
            return self._split_by_sentences(text)
        else:
            return self._split_by_characters(text)
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text into chunks while preserving sentence boundaries."""
        # Split into sentences using basic regex
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if len(current_chunk.strip()) >= self.min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from previous chunk
                if self.chunk_overlap > 0 and chunks:
                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                    current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the final chunk if it meets minimum size
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_characters(self, text: str) -> List[str]:
        """Split text into chunks by character count with overlap."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Determine end position
            end = start + self.chunk_size
            
            if end >= len(text):
                # Final chunk
                chunk = text[start:]
                if len(chunk.strip()) >= self.min_chunk_size:
                    chunks.append(chunk.strip())
                break
            
            # Try to find a good break point (space or punctuation)
            chunk_text = text[start:end]
            
            # Look for word boundary within last 50 characters
            break_point = self._find_break_point(chunk_text)
            if break_point > 0:
                chunk = text[start:start + break_point]
            else:
                chunk = chunk_text
            
            if len(chunk.strip()) >= self.min_chunk_size:
                chunks.append(chunk.strip())
            
            # Move start position, accounting for overlap
            if break_point > 0:
                start = start + break_point - self.chunk_overlap
            else:
                start = end - self.chunk_overlap
            
            # Ensure we make progress
            start = max(start, len(chunks[-1]) + start - self.chunk_overlap if chunks else 0)
        
        return chunks
    
    def _find_break_point(self, text: str) -> int:
        """Find a good break point near the end of a chunk."""
        # Look for sentence endings first
        for i in range(len(text) - 1, max(0, len(text) - 100), -1):
            if text[i] in '.!?':
                return i + 1
        
        # Look for word boundaries
        for i in range(len(text) - 1, max(0, len(text) - 50), -1):
            if text[i].isspace():
                return i
        
        return 0
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= overlap_size:
            return text
        
        # Try to get overlap at word boundary
        overlap_text = text[-overlap_size:]
        
        # Find first space to start at word boundary
        space_idx = overlap_text.find(' ')
        if space_idx > 0:
            return overlap_text[space_idx + 1:]
        
        return overlap_text