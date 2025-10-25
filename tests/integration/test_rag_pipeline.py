"""Integration tests for RAG pipeline."""

import json
import tempfile
from pathlib import Path
import pytest

from core.utils import ScragConfig
from core.rag.embedders import SentenceTransformerEmbedder
from core.rag.stores import FileIndexStore, IndexDocument
from core.rag.stages import EmbedStage, IndexStage, RetrievalStage
from core.rag.pipeline import RAGPipelineRunner
from core.processors.chunking import ChunkingProcessor
from core.processors.base import ProcessingContext
from core.pipeline.stages import StageContext


class TestRAGPipelineIntegration:
    """Integration tests for the complete RAG pipeline."""
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        Artificial Intelligence (AI) is a rapidly growing field that focuses on creating intelligent machines. 
        Machine learning is a subset of AI that enables computers to learn without being explicitly programmed.
        Deep learning is a subset of machine learning that uses neural networks with multiple layers.
        Natural language processing (NLP) is another important area of AI that deals with text and speech.
        Computer vision helps machines interpret and understand visual information from the world.
        Robotics combines AI with mechanical engineering to create autonomous systems.
        """
    
    @pytest.fixture
    def config(self):
        """Test configuration."""
        config_data = {
            "rag": {
                "chunking": {
                    "chunk_size": 100,
                    "chunk_overlap": 20,
                    "preserve_sentences": True,
                    "min_chunk_size": 30
                },
                "embeddings": {
                    "default_model": "sentence-transformer",
                    "models": {
                        "sentence-transformer": {
                            "model_name": "all-MiniLM-L6-v2",
                            "device": "cpu"
                        }
                    }
                },
                "storage": {
                    "default_backend": "file",
                    "backends": {
                        "file": {
                            "base_path": "test_data/indices",
                            "create_if_missing": True
                        }
                    }
                },
                "retrieval": {
                    "default_top_k": 5,
                    "default_threshold": 0.0
                }
            }
        }
        return ScragConfig(data=config_data, environment="test")
    
    def test_chunking_processor(self, sample_content):
        """Test content chunking."""
        processor = ChunkingProcessor(
            chunk_size=100,
            chunk_overlap=20,
            preserve_sentences=True
        )
        
        context = ProcessingContext(content=sample_content)
        result = processor.process(context)
        
        assert "chunks" in result.metadata
        chunks = result.metadata["chunks"]
        assert len(chunks) > 1
        assert all(len(chunk) <= 150 for chunk in chunks)  # Some tolerance for sentence preservation
    
    @pytest.mark.skipif(
        not _is_sentence_transformers_available(),
        reason="sentence-transformers not available"
    )
    def test_embed_stage(self, sample_content):
        """Test embedding generation."""
        # Chunk content first
        processor = ChunkingProcessor(chunk_size=100, chunk_overlap=20)
        context = ProcessingContext(content=sample_content)
        chunking_result = processor.process(context)
        chunks = chunking_result.metadata["chunks"]
        
        # Test embedding
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        embed_stage = EmbedStage(embedder=embedder)
        
        stage_context = StageContext(data=chunks)
        result = embed_stage.process(stage_context)
        
        assert result.success
        assert len(result.data) == len(chunks)
        assert all(len(embedding) == embedder.get_embedding_dimension() for embedding in result.data)
    
    @pytest.mark.skipif(
        not _is_sentence_transformers_available(),
        reason="sentence-transformers not available"
    )
    def test_index_stage(self, sample_content):
        """Test index building."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            # Prepare data
            processor = ChunkingProcessor(chunk_size=100, chunk_overlap=20)
            context = ProcessingContext(content=sample_content)
            chunking_result = processor.process(context)
            chunks = chunking_result.metadata["chunks"]
            
            embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
            embed_stage = EmbedStage(embedder=embedder)
            stage_context = StageContext(data=chunks)
            embed_result = embed_stage.process(stage_context)
            
            # Test indexing
            index_store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=embedder.get_embedding_dimension()
            )
            index_stage = IndexStage(index_store=index_store)
            
            index_context = StageContext(
                data=(chunks, embed_result.data),
                metadata=embed_result.metadata
            )
            result = index_stage.process(index_context)
            
            assert result.success
            assert result.data is True
            assert index_path.exists()
            
            # Verify index contents
            stats = index_store.get_stats()
            assert stats["total_documents"] == len(chunks)
    
    @pytest.mark.skipif(
        not _is_sentence_transformers_available(),
        reason="sentence-transformers not available"
    )
    def test_retrieval_stage(self, sample_content):
        """Test retrieval from index."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            # Build index first
            processor = ChunkingProcessor(chunk_size=100, chunk_overlap=20)
            context = ProcessingContext(content=sample_content)
            chunking_result = processor.process(context)
            chunks = chunking_result.metadata["chunks"]
            
            embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
            embed_stage = EmbedStage(embedder=embedder)
            stage_context = StageContext(data=chunks)
            embed_result = embed_stage.process(stage_context)
            
            index_store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=embedder.get_embedding_dimension()
            )
            index_stage = IndexStage(index_store=index_store)
            index_context = StageContext(
                data=(chunks, embed_result.data),
                metadata=embed_result.metadata
            )
            index_stage.process(index_context)
            
            # Test retrieval
            retrieval_stage = RetrievalStage(
                embedder=embedder,
                index_store=index_store,
                top_k=3
            )
            
            query = "machine learning neural networks"
            query_context = StageContext(
                data=query,
                stage_config={"top_k": 3, "include_scores": True}
            )
            result = retrieval_stage.process(query_context)
            
            assert result.success
            query_result = result.data
            assert query_result["result_count"] > 0
            assert len(query_result["results"]) <= 3
            
            # Check that results contain relevant content
            retrieved_text = query_result["retrieved_content"].lower()
            assert "machine learning" in retrieved_text or "neural" in retrieved_text
    
    @pytest.mark.skipif(
        not _is_sentence_transformers_available(),
        reason="sentence-transformers not available"
    )
    def test_end_to_end_pipeline(self, sample_content, config):
        """Test complete RAG pipeline from content to query."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            # Create pipeline runner
            runner = RAGPipelineRunner(config)
            
            # Build index
            source_metadata = {"source": "test_content", "type": "text"}
            result = runner.build_index_from_content(
                content=sample_content,
                index_path=index_path,
                source_metadata=source_metadata
            )
            
            assert result.success
            assert result.indexed
            assert len(result.chunks) > 1
            assert len(result.embeddings) == len(result.chunks)
            assert index_path.exists()
            
            # Query the index
            query_result = runner.query_index(
                query_text="What is deep learning?",
                index_path=index_path,
                top_k=2
            )
            
            assert query_result.success
            assert query_result.query_results["result_count"] > 0
            
            # Check relevance
            retrieved_content = query_result.query_results["retrieved_content"].lower()
            assert "deep learning" in retrieved_content or "neural" in retrieved_content


def _is_sentence_transformers_available() -> bool:
    """Check if sentence-transformers is available."""
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False