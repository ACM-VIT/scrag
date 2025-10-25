# ADR-003: IndexStore Abstraction for Backend Independence

**Status:** Proposed  
**Date:** 2025-10-25  
**Deciders:** Development Team  

## Context

RAG index construction requires flexible storage backends for different use cases:
- Local development: Simple file-based storage
- Production: Vector databases (Chroma, Pinecone, Weaviate)
- Enterprise: Self-hosted solutions (Milvus, Qdrant)
- Cloud: Managed services (OpenSearch, Elasticsearch)

Hard-coding specific backends creates vendor lock-in and limits deployment flexibility. We need an abstraction that allows easy switching between backends without changing application logic.

## Decision

We will implement an `IndexStore` interface that abstracts vector storage operations:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Document:
    """Document with content and metadata"""
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]

@dataclass
class QueryResult:
    """Result from index query"""
    documents: List[Document]
    scores: List[float]
    query_metadata: Dict[str, Any]

class IndexStore(ABC):
    """Abstract interface for index storage backends"""
    
    @abstractmethod
    async def create_index(self, name: str, dimension: int) -> bool:
        """Create a new index"""
        pass
    
    @abstractmethod
    async def add_documents(self, index_name: str, documents: List[Document]) -> bool:
        """Add documents to index"""
        pass
    
    @abstractmethod
    async def query(self, index_name: str, query_embedding: List[float], 
                   top_k: int = 10, filters: Dict[str, Any] = None) -> QueryResult:
        """Query index for similar documents"""
        pass
    
    @abstractmethod
    async def delete_documents(self, index_name: str, document_ids: List[str]) -> bool:
        """Delete documents from index"""
        pass
    
    @abstractmethod
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics"""
        pass
```

### Concrete Implementations

1. **FileIndexStore**: JSON/SQLite-based for development
2. **ChromaIndexStore**: Chroma database integration
3. **PineconeIndexStore**: Pinecone cloud service
4. **WeaviateIndexStore**: Weaviate database
5. **ElasticsearchIndexStore**: Elasticsearch with vector search

## Consequences

### Positive
- Backend flexibility and vendor independence
- Easy testing with file-based backends
- Consistent API across different storage systems
- Simplified migration between backends
- Clear separation of concerns

### Negative
- Additional abstraction complexity
- Potential lowest-common-denominator API
- Need to maintain multiple backend implementations
- Testing overhead for all backends

## Implementation Plan

1. Define `IndexStore` interface in `src/scrag/core/storage/index/`
2. Implement `FileIndexStore` for basic functionality
3. Add configuration for backend selection
4. Create factory pattern for IndexStore instantiation
5. Implement additional backends based on user needs
6. Add comprehensive integration tests

## Configuration

```yaml
index_store:
  backend: "file"  # file, chroma, pinecone, weaviate, elasticsearch
  config:
    # File backend
    file:
      directory: "data/indices"
      format: "json"
    
    # Chroma backend
    chroma:
      host: "localhost"
      port: 8000
      collection_name: "scrag_index"
    
    # Pinecone backend
    pinecone:
      api_key: "${PINECONE_API_KEY}"
      environment: "us-west1-gcp"
      index_name: "scrag-index"
```

## Factory Pattern

```python
class IndexStoreFactory:
    """Factory for creating IndexStore instances"""
    
    @staticmethod
    def create(backend: str, config: Dict[str, Any]) -> IndexStore:
        if backend == "file":
            return FileIndexStore(**config)
        elif backend == "chroma":
            return ChromaIndexStore(**config)
        # ... other backends
        else:
            raise ValueError(f"Unknown backend: {backend}")
```

## Related

- ADR-001: PipelineStage Interface Design
- Issue: [To be created] - Implement IndexStore abstraction
- Epic: RAG Index Construction