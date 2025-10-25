"""RAG component interfaces and baseline implementation."""

from .base import RAGContext, RAGResult, BaseRAGComponent, NoOpRAGComponent
from . import embedders, stores, stages
from .query import QueryProcessor, RAGQueryManager
from .factory import (
    build_embedder,
    build_index_store, 
    build_chunking_processor,
    build_embed_stage,
    build_index_stage,
    build_retrieval_stage,
    build_rag_pipeline_components
)
from .pipeline import RAGPipelineRunner, RAGPipelineResult

__all__ = [
    # Base components
    "RAGContext",
    "RAGResult", 
    "BaseRAGComponent",
    "NoOpRAGComponent",
    
    # Submodules
    "embedders",
    "stores", 
    "stages",
    
    # Query components
    "QueryProcessor",
    "RAGQueryManager",
    
    # Factory functions
    "build_embedder",
    "build_index_store",
    "build_chunking_processor", 
    "build_embed_stage",
    "build_index_stage",
    "build_retrieval_stage",
    "build_rag_pipeline_components",
    
    # Pipeline
    "RAGPipelineRunner",
    "RAGPipelineResult",
]
