# EPIC 2: RAG Index Construction System

**Epic ID:** EPIC-002  
**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Duration:** 6-8 weeks  
**Created:** 2025-10-25  

## Problem Statement

After crawling web content (EPIC-001), we need to make it searchable and useful for RAG (Retrieval-Augmented Generation) applications. The current system can extract and store content but lacks the embedding generation, indexing, and retrieval capabilities needed for the Universal RAG Builder vision.

## Solution Overview

Build a RAG index construction system that:
1. Generates embeddings for crawled content
2. Builds searchable indices using various backend storage options
3. Provides efficient retrieval and query capabilities
4. Abstracts storage backends for flexibility
5. Integrates seamlessly with existing and crawled content

## Scope & Boundaries

### In Scope
- [ ] Embed stage: Generate embeddings using various models
- [ ] Index stage: Build searchable vector indices
- [ ] Retrieval Query stage: Search indexed content efficiently
- [ ] IndexStore interface: Abstract storage backend operations
- [ ] Content chunking optimization for RAG
- [ ] CLI commands for index operations
- [ ] Multiple embedding model support

### Out of Scope
- [ ] LLM integration for answer generation (separate feature)
- [ ] Advanced query understanding (basic semantic search only)
- [ ] Real-time index updates (batch processing focus)
- [ ] Distributed indexing across multiple machines
- [ ] Custom embedding model training

## User Stories / Subtasks

### Discovery Phase
- [ ] [SPIKE-004] - Embedding Models Evaluation
- [ ] [SPIKE-005] - Vector Database Comparison
- [ ] [SPIKE-006] - Chunking Strategy Analysis

### Implementation Phase
- [ ] [TASK-011] - Implement IndexStore interface abstraction
- [ ] [TASK-012] - Create Embed stage with multiple model support
- [ ] [TASK-013] - Build Index stage for vector storage
- [ ] [TASK-014] - Implement Retrieval Query stage
- [ ] [TASK-015] - Add content chunking optimization
- [ ] [TASK-016] - Create file-based IndexStore implementation
- [ ] [TASK-017] - Add CLI commands for index operations

### Integration & Testing Phase
- [ ] [TASK-018] - Integration with crawled content from EPIC-001
- [ ] [TASK-019] - Performance testing with large document sets
- [ ] [TASK-020] - Documentation and examples

## Success Criteria

- [ ] Users can build searchable indices from crawled content
- [ ] System supports multiple embedding models (sentence-transformers, OpenAI, etc.)
- [ ] Retrieval queries return relevant results in <1 second for 10K+ documents
- [ ] IndexStore abstraction allows easy switching between storage backends
- [ ] Content chunking produces optimal chunk sizes for RAG applications
- [ ] Index construction handles large document sets (100K+ documents)

## Technical Requirements

### Architecture
- [ ] IndexStore interface abstracts vector storage operations
- [ ] Embed stage supports pluggable embedding models
- [ ] Index stage optimizes for query performance
- [ ] Retrieval Query stage provides semantic search capabilities
- [ ] All components implement PipelineStage interface

### Performance
- [ ] Index construction: 1000+ documents per minute
- [ ] Query response time: <1 second for 10K+ document indices
- [ ] Memory usage: Configurable based on available resources
- [ ] Storage efficiency: Compressed embeddings when possible

### Quality
- [ ] Code coverage ≥85% for new components
- [ ] Support for multiple embedding dimensions
- [ ] Proper error handling for model loading and inference
- [ ] Comprehensive integration testing

## Dependencies

### Internal Dependencies
- [ ] EPIC-001: Web Crawling & Discovery System (provides content)
- [ ] PipelineStage interface implementation
- [ ] Existing content processing pipeline

### External Dependencies
- [ ] Embedding model libraries (sentence-transformers, OpenAI API, etc.)
- [ ] Vector storage libraries (for different IndexStore backends)
- [ ] Chunking and text processing libraries

## Risk Assessment

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Embedding model API rate limits | Medium | Medium | Support local models as fallback |
| Large memory requirements | High | Medium | Implement streaming and batching |
| Query performance with scale | High | Low | Optimize indexing and use efficient vector libraries |
| Model compatibility issues | Medium | Medium | Comprehensive testing across models |

## Milestones & Timeline

- [ ] **Discovery Complete** - Week 2 - All spike work and model evaluation finished
- [ ] **Core Components** - Week 4 - Embed, Index, Retrieval stages implemented
- [ ] **Backend Integration** - Week 6 - Multiple IndexStore implementations
- [ ] **Production Ready** - Week 8 - Testing, optimization, and documentation

## Architecture Overview

```
Processed Content → Embed → Index → IndexStore
                     ↓       ↓        ↓
                  Embeddings Vectors  Stored Index

User Query → Retrieval Query → IndexStore → Ranked Results
              ↓
         Query Embedding

IndexStore Interface:
├── FileIndexStore (JSON/SQLite)
├── ChromaIndexStore  
├── PineconeIndexStore
└── WeaviateIndexStore
```

## Definition of Done

An epic is considered complete when:

- [ ] All linked subtasks are completed and closed
- [ ] Users can build and query RAG indices from any content source
- [ ] System works with multiple embedding models and storage backends
- [ ] Performance requirements are met for indexing and retrieval
- [ ] Code review completed and approved for all components
- [ ] Unit tests written with ≥85% coverage for new code
- [ ] Integration tests cover end-to-end RAG workflows
- [ ] Documentation includes examples for different backends
- [ ] CLI commands are intuitive and well-documented
- [ ] IndexStore abstraction properly isolates backend details
- [ ] Content chunking produces high-quality embeddings

## Key Configuration

```yaml
# Addition to config/default.yml
indexing:
  enabled: true
  
  embedding:
    model: "sentence-transformers/all-MiniLM-L6-v2"
    # Alternative: "openai/text-embedding-ada-002"
    # Alternative: "local/custom-model"
    batch_size: 32
    max_length: 512
    normalize: true
  
  chunking:
    strategy: "semantic"  # semantic, fixed, sliding
    chunk_size: 512
    overlap: 64
    respect_boundaries: true  # Don't split sentences/paragraphs
  
  index_store:
    backend: "file"  # file, chroma, pinecone, weaviate
    config:
      file:
        directory: "data/indices"
        format: "json"
        compression: true
      
      chroma:
        host: "localhost"
        port: 8000
        collection_name: "scrag_index"
      
      pinecone:
        api_key: "${PINECONE_API_KEY}"
        environment: "us-west1-gcp"
        index_name: "scrag-index"
  
  retrieval:
    default_top_k: 10
    similarity_threshold: 0.7
    rerank: false  # Future enhancement
```

## CLI Commands

```bash
# Build index from crawled content
scrag index build --job-id crawl-123 --index-name ml-papers

# Build index from local files
scrag index build --input data/documents/ --index-name local-docs

# Query an index
scrag index query --index-name ml-papers "transformer architecture"

# List available indices
scrag index list

# Get index statistics
scrag index stats --index-name ml-papers

# Delete an index
scrag index delete --index-name old-index
```

## Artifacts

- [ ] IndexStore interface specification
- [ ] Embedding model comparison and recommendations
- [ ] Performance benchmark results for different backends
- [ ] User guide for RAG index construction
- [ ] Configuration reference for all backends
- [ ] Example notebooks demonstrating usage

## Integration with EPIC-001

```python
# End-to-end workflow
crawl_result = crawl_manager.crawl(job)
index_result = index_builder.build(
    content_source=crawl_result.artifacts,
    index_name=f"crawl-{crawl_result.job_id}"
)
query_results = retrieval_engine.query(
    index_name=index_result.index_name,
    query="user question"
)
```

## Related Epics

- **EPIC-001**: Web Crawling & Discovery System (provides content)
- **Future**: LLM Integration for Answer Generation
- **Future**: Real-time Index Updates
- **Future**: Advanced Query Understanding