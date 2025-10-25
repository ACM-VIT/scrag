"""File-based index store implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from .base import IndexStore, IndexDocument, SearchResult, SearchQuery

logger = logging.getLogger(__name__)


class FileIndexStore(IndexStore):
    """File-based implementation of IndexStore using JSON and numpy."""
    
    def __init__(
        self,
        index_path: str | Path,
        embedding_dimension: int = 768,
        create_if_missing: bool = True
    ) -> None:
        super().__init__(name="file_store")
        self.index_path = Path(index_path)
        self.embedding_dimension = embedding_dimension
        self.create_if_missing = create_if_missing
        
        # Internal storage
        self._documents: Dict[str, IndexDocument] = {}
        self._embeddings: Optional[np.ndarray] = None
        self._doc_ids: List[str] = []
        
        # Load existing index if it exists
        if self.index_path.exists():
            self._load_index()
        elif create_if_missing:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_available(self) -> bool:
        """Check if the store is available."""
        return self.index_path.parent.exists() or self.create_if_missing
    
    def add_documents(self, documents: List[IndexDocument]) -> bool:
        """Add documents to the index."""
        try:
            for doc in documents:
                # Validate embedding dimension
                if len(doc.embedding) != self.embedding_dimension:
                    logger.warning(f"Document {doc.id} has embedding dimension {len(doc.embedding)}, expected {self.embedding_dimension}")
                    continue
                
                # Add or update document
                if doc.id in self._documents:
                    # Update existing document
                    idx = self._doc_ids.index(doc.id)
                    self._documents[doc.id] = doc
                    if self._embeddings is not None:
                        self._embeddings[idx] = np.array(doc.embedding)
                else:
                    # Add new document
                    self._documents[doc.id] = doc
                    self._doc_ids.append(doc.id)
                    
                    # Update embeddings matrix
                    new_embedding = np.array(doc.embedding).reshape(1, -1)
                    if self._embeddings is None:
                        self._embeddings = new_embedding
                    else:
                        self._embeddings = np.vstack([self._embeddings, new_embedding])
            
            # Save to disk
            self._save_index()
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to index: {e}")
            return False
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar documents using cosine similarity."""
        if self._embeddings is None or len(self._doc_ids) == 0:
            return []
        
        try:
            query_embedding = np.array(query.embedding).reshape(1, -1)
            
            # Compute cosine similarity
            # Normalize embeddings
            norm_embeddings = self._embeddings / np.linalg.norm(self._embeddings, axis=1, keepdims=True)
            norm_query = query_embedding / np.linalg.norm(query_embedding)
            
            # Calculate similarities
            similarities = np.dot(norm_embeddings, norm_query.T).flatten()
            
            # Apply threshold filter
            valid_indices = similarities >= query.threshold
            similarities = similarities[valid_indices]
            valid_doc_ids = [self._doc_ids[i] for i in range(len(self._doc_ids)) if valid_indices[i]]
            
            # Sort by similarity (descending)
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Apply top_k limit
            top_indices = sorted_indices[:query.top_k]
            
            results = []
            for idx in top_indices:
                doc_id = valid_doc_ids[idx]
                doc = self._documents[doc_id]
                score = float(similarities[idx])
                
                # Apply metadata filters
                if self._matches_filters(doc, query.filters):
                    results.append(SearchResult(
                        document=doc,
                        score=score,
                        metadata={"similarity": score}
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[IndexDocument]:
        """Retrieve a document by ID."""
        return self._documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        try:
            if doc_id not in self._documents:
                return False
            
            # Find index and remove
            idx = self._doc_ids.index(doc_id)
            
            # Remove from storage
            del self._documents[doc_id]
            self._doc_ids.pop(idx)
            
            # Remove from embeddings matrix
            if self._embeddings is not None:
                if self._embeddings.shape[0] == 1:
                    self._embeddings = None
                else:
                    self._embeddings = np.delete(self._embeddings, idx, axis=0)
            
            # Save to disk
            self._save_index()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_documents": len(self._documents),
            "embedding_dimension": self.embedding_dimension,
            "index_path": str(self.index_path),
            "index_size_mb": self._get_index_size_mb()
        }
    
    def clear(self) -> bool:
        """Clear all documents from the index."""
        try:
            self._documents.clear()
            self._doc_ids.clear()
            self._embeddings = None
            
            # Remove index file
            if self.index_path.exists():
                self.index_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False
    
    def _load_index(self) -> None:
        """Load index from disk."""
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load documents
            self._documents = {}
            self._doc_ids = []
            embeddings_list = []
            
            for doc_data in data.get('documents', []):
                doc = IndexDocument(
                    id=doc_data['id'],
                    content=doc_data['content'],
                    embedding=doc_data['embedding'],
                    metadata=doc_data.get('metadata', {})
                )
                self._documents[doc.id] = doc
                self._doc_ids.append(doc.id)
                embeddings_list.append(doc.embedding)
            
            # Rebuild embeddings matrix
            if embeddings_list:
                self._embeddings = np.array(embeddings_list)
            
            # Update embedding dimension from loaded data
            if 'embedding_dimension' in data:
                self.embedding_dimension = data['embedding_dimension']
            
            logger.info(f"Loaded index with {len(self._documents)} documents from {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error loading index from {self.index_path}: {e}")
            # Initialize empty index
            self._documents = {}
            self._doc_ids = []
            self._embeddings = None
    
    def _save_index(self) -> None:
        """Save index to disk."""
        try:
            # Prepare data for serialization
            documents_data = []
            for doc_id in self._doc_ids:
                doc = self._documents[doc_id]
                documents_data.append({
                    'id': doc.id,
                    'content': doc.content,
                    'embedding': doc.embedding,
                    'metadata': doc.metadata
                })
            
            data = {
                'embedding_dimension': self.embedding_dimension,
                'documents': documents_data,
                'stats': self.get_stats()
            }
            
            # Write to temporary file first, then rename for atomicity
            temp_path = self.index_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_path.rename(self.index_path)
            logger.debug(f"Saved index with {len(self._documents)} documents to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error saving index to {self.index_path}: {e}")
            raise
    
    def _matches_filters(self, doc: IndexDocument, filters: Dict[str, Any]) -> bool:
        """Check if document matches the given filters."""
        if not filters:
            return True
        
        for key, value in filters.items():
            doc_value = doc.metadata.get(key)
            if doc_value != value:
                return False
        
        return True
    
    def _get_index_size_mb(self) -> float:
        """Get the size of the index file in MB."""
        try:
            if self.index_path.exists():
                return self.index_path.stat().st_size / (1024 * 1024)
            return 0.0
        except Exception:
            return 0.0