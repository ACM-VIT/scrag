"""Unit tests for RAG stores."""

import tempfile
from pathlib import Path
import pytest

from core.rag.stores import FileIndexStore, IndexDocument, SearchQuery


class TestFileIndexStore:
    """Unit tests for FileIndexStore."""
    
    def test_create_empty_store(self):
        """Test creating an empty index store."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=384
            )
            
            assert store.is_available
            assert store.get_stats()["total_documents"] == 0
    
    def test_add_and_retrieve_documents(self):
        """Test adding and retrieving documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            # Add test documents
            documents = [
                IndexDocument(
                    id="doc1",
                    content="This is the first document about cats.",
                    embedding=[0.1, 0.2, 0.3],
                    metadata={"topic": "animals"}
                ),
                IndexDocument(
                    id="doc2", 
                    content="This is the second document about dogs.",
                    embedding=[0.4, 0.5, 0.6],
                    metadata={"topic": "animals"}
                ),
                IndexDocument(
                    id="doc3",
                    content="This document is about programming.",
                    embedding=[0.7, 0.8, 0.9],
                    metadata={"topic": "technology"}
                )
            ]
            
            success = store.add_documents(documents)
            assert success
            
            # Test retrieval by ID
            doc1 = store.get_document("doc1")
            assert doc1 is not None
            assert doc1.content == "This is the first document about cats."
            
            # Test stats
            stats = store.get_stats()
            assert stats["total_documents"] == 3
    
    def test_search_functionality(self):
        """Test search functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            # Add test documents
            documents = [
                IndexDocument(
                    id="doc1",
                    content="Document about machine learning",
                    embedding=[1.0, 0.0, 0.0],  # Orthogonal vectors for testing
                    metadata={"topic": "ai"}
                ),
                IndexDocument(
                    id="doc2",
                    content="Document about cooking recipes",
                    embedding=[0.0, 1.0, 0.0],
                    metadata={"topic": "food"}
                ),
                IndexDocument(
                    id="doc3",
                    content="Document about neural networks", 
                    embedding=[0.8, 0.0, 0.6],  # Similar to doc1
                    metadata={"topic": "ai"}
                )
            ]
            
            store.add_documents(documents)
            
            # Search with query similar to doc1
            query = SearchQuery(
                embedding=[0.9, 0.1, 0.0],  # Close to doc1
                top_k=2,
                threshold=0.5
            )
            
            results = store.search(query)
            assert len(results) <= 2
            
            # Results should be ordered by similarity
            if len(results) > 1:
                assert results[0].score >= results[1].score
    
    def test_delete_document(self):
        """Test document deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            # Add document
            doc = IndexDocument(
                id="test_doc",
                content="Test document",
                embedding=[0.1, 0.2, 0.3]
            )
            store.add_documents([doc])
            
            # Verify it exists
            assert store.get_document("test_doc") is not None
            assert store.get_stats()["total_documents"] == 1
            
            # Delete it
            success = store.delete_document("test_doc")
            assert success
            
            # Verify it's gone
            assert store.get_document("test_doc") is None
            assert store.get_stats()["total_documents"] == 0
    
    def test_persistence(self):
        """Test that data persists across store instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            # Create store and add document
            store1 = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            doc = IndexDocument(
                id="persistent_doc",
                content="This should persist",
                embedding=[0.1, 0.2, 0.3]
            )
            store1.add_documents([doc])
            
            # Create new store instance with same path
            store2 = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            # Document should still exist
            retrieved_doc = store2.get_document("persistent_doc")
            assert retrieved_doc is not None
            assert retrieved_doc.content == "This should persist"
            assert store2.get_stats()["total_documents"] == 1
    
    def test_clear_index(self):
        """Test clearing the entire index."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test_index.json"
            
            store = FileIndexStore(
                index_path=index_path,
                embedding_dimension=3
            )
            
            # Add documents
            documents = [
                IndexDocument(id="doc1", content="Doc 1", embedding=[0.1, 0.2, 0.3]),
                IndexDocument(id="doc2", content="Doc 2", embedding=[0.4, 0.5, 0.6])
            ]
            store.add_documents(documents)
            
            assert store.get_stats()["total_documents"] == 2
            
            # Clear index
            success = store.clear()
            assert success
            assert store.get_stats()["total_documents"] == 0
            assert not index_path.exists()