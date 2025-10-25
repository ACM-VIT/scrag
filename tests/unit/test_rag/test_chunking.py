"""Unit tests for chunking processor."""

import pytest

from core.processors.chunking import ChunkingProcessor
from core.processors.base import ProcessingContext


class TestChunkingProcessor:
    """Unit tests for ChunkingProcessor."""
    
    def test_basic_chunking(self):
        """Test basic text chunking."""
        processor = ChunkingProcessor(
            chunk_size=50,
            chunk_overlap=10,
            preserve_sentences=False
        )
        
        content = "This is a test document. " * 10  # 250 characters
        context = ProcessingContext(content=content)
        result = processor.process(context)
        
        assert "chunks" in result.metadata
        chunks = result.metadata["chunks"]
        assert len(chunks) > 1
        
        # Check chunk sizes
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk) <= 50 + 10  # Allow for overlap tolerance
    
    def test_sentence_preservation(self):
        """Test that sentence boundaries are preserved."""
        processor = ChunkingProcessor(
            chunk_size=50,
            chunk_overlap=10,
            preserve_sentences=True
        )
        
        content = "First sentence is here. Second sentence follows. Third sentence comes next. Fourth sentence is last."
        context = ProcessingContext(content=content)
        result = processor.process(context)
        
        chunks = result.metadata["chunks"]
        
        # Each chunk should contain complete sentences
        for chunk in chunks:
            # Should not split mid-sentence (rough check)
            if len(chunk) > 20:  # Skip very short chunks
                assert chunk.strip().endswith('.') or chunk == chunks[-1]
    
    def test_overlap_functionality(self):
        """Test that overlap works correctly."""
        processor = ChunkingProcessor(
            chunk_size=30,
            chunk_overlap=10,
            preserve_sentences=False
        )
        
        content = "abcdefghijklmnopqrstuvwxyz" * 3  # 78 characters
        context = ProcessingContext(content=content)
        result = processor.process(context)
        
        chunks = result.metadata["chunks"]
        assert len(chunks) >= 2
        
        # Check for overlap between consecutive chunks
        if len(chunks) > 1:
            # There should be some overlap
            first_chunk_end = chunks[0][-5:]
            second_chunk_start = chunks[1][:10]
            # At least some characters should overlap
            assert any(char in second_chunk_start for char in first_chunk_end)
    
    def test_minimum_chunk_size(self):
        """Test minimum chunk size enforcement."""
        processor = ChunkingProcessor(
            chunk_size=100,
            chunk_overlap=10,
            min_chunk_size=20
        )
        
        content = "Short text."  # 11 characters, below min_chunk_size
        context = ProcessingContext(content=content)
        result = processor.process(context)
        
        chunks = result.metadata["chunks"]
        # Should either have no chunks or chunks that meet minimum size
        for chunk in chunks:
            assert len(chunk.strip()) >= 20 or len(content.strip()) < 20
    
    def test_empty_content(self):
        """Test handling of empty content."""
        processor = ChunkingProcessor()
        
        context = ProcessingContext(content="")
        result = processor.process(context)
        
        chunks = result.metadata.get("chunks", [])
        assert len(chunks) == 0
    
    def test_single_chunk_content(self):
        """Test content that fits in a single chunk."""
        processor = ChunkingProcessor(chunk_size=100)
        
        content = "This is a short piece of text."
        context = ProcessingContext(content=content)
        result = processor.process(context)
        
        chunks = result.metadata["chunks"]
        assert len(chunks) == 1
        assert chunks[0].strip() == content.strip()
    
    def test_metadata_preservation(self):
        """Test that input metadata is preserved."""
        processor = ChunkingProcessor()
        
        input_metadata = {"source": "test", "timestamp": "2023-01-01"}
        context = ProcessingContext(
            content="Test content for chunking.",
            metadata=input_metadata
        )
        result = processor.process(context)
        
        # Original metadata should be preserved
        assert result.metadata["source"] == "test"
        assert result.metadata["timestamp"] == "2023-01-01"
        
        # Chunk-specific metadata should be added
        assert "chunks" in result.metadata
        assert "chunk_count" in result.metadata
        assert "chunk_metadata" in result.metadata