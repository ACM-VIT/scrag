"""Base index storage interfaces for RAG components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid


@dataclass(slots=True)
class IndexDocument:
    """Document to be indexed with embeddings."""
    
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass(slots=True)
class SearchQuery:
    """Query for searching indexed documents."""
    
    embedding: List[float]
    top_k: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 0.0


@dataclass(slots=True)
class SearchResult:
    """Result from search operation."""
    
    document: IndexDocument
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class IndexStore(ABC):
    """Abstract base class for index storage backends."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    @abstractmethod
    def add_documents(self, documents: List[IndexDocument]) -> bool:
        """Add documents to the index."""
        
    @abstractmethod
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search for similar documents."""
        
    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[IndexDocument]:
        """Retrieve a document by ID."""
        
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        
    @abstractmethod
    def clear(self) -> bool:
        """Clear all documents from the index."""
        
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the store is properly configured and available."""