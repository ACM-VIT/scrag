"""Factory functions for building RAG components from configuration."""

from __future__ import annotations

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from scrag.core.utils import ScragConfig
from .embedders import BaseEmbedder, SentenceTransformerEmbedder, OpenAIEmbedder
from .stores import IndexStore, FileIndexStore
from .stages import EmbedStage, IndexStage, RetrievalStage
from scrag.core.processors.chunking import ChunkingProcessor

logger = logging.getLogger(__name__)


def build_embedder(config: ScragConfig, model_type: Optional[str] = None) -> BaseEmbedder:
    """Build an embedder from configuration."""
    rag_config = config.data.get("rag", {})
    embeddings_config = rag_config.get("embeddings", {})
    
    # Determine model type
    if model_type is None:
        model_type = embeddings_config.get("default_model", "sentence-transformer")
    
    models_config = embeddings_config.get("models", {})
    model_config = models_config.get(model_type, {})
    
    if model_type == "sentence-transformer":
        return SentenceTransformerEmbedder(
            model_name=model_config.get("model_name", "all-MiniLM-L6-v2"),
            device=model_config.get("device", "cpu"),
            cache_folder=model_config.get("cache_folder")
        )
    elif model_type == "openai":
        return OpenAIEmbedder(
            model_name=model_config.get("model_name", "text-embedding-3-small"),
            api_key=model_config.get("api_key"),
            batch_size=model_config.get("batch_size", 100)
        )
    else:
        raise ValueError(f"Unknown embedder type: {model_type}")


def build_index_store(
    config: ScragConfig, 
    index_path: Optional[Path] = None,
    backend_type: Optional[str] = None
) -> IndexStore:
    """Build an index store from configuration."""
    rag_config = config.data.get("rag", {})
    storage_config = rag_config.get("storage", {})
    
    # Determine backend type
    if backend_type is None:
        backend_type = storage_config.get("default_backend", "file")
    
    backends_config = storage_config.get("backends", {})
    backend_config = backends_config.get(backend_type, {})
    
    if backend_type == "file":
        if index_path is None:
            base_path = backend_config.get("base_path", "data/indices")
            index_path = Path(base_path) / "default_index.json"
        
        # Get embedding dimension from embedder config
        embedder = build_embedder(config)
        embedding_dimension = embedder.get_embedding_dimension()
        
        return FileIndexStore(
            index_path=index_path,
            embedding_dimension=embedding_dimension,
            create_if_missing=backend_config.get("create_if_missing", True)
        )
    else:
        raise ValueError(f"Unknown index store backend: {backend_type}")


def build_chunking_processor(config: ScragConfig) -> ChunkingProcessor:
    """Build a chunking processor from configuration."""
    rag_config = config.data.get("rag", {})
    chunking_config = rag_config.get("chunking", {})
    
    return ChunkingProcessor(
        chunk_size=chunking_config.get("chunk_size", 512),
        chunk_overlap=chunking_config.get("chunk_overlap", 50),
        preserve_sentences=chunking_config.get("preserve_sentences", True),
        min_chunk_size=chunking_config.get("min_chunk_size", 50)
    )


def build_embed_stage(config: ScragConfig, model_type: Optional[str] = None) -> EmbedStage:
    """Build an embed stage from configuration."""
    embedder = build_embedder(config, model_type)
    return EmbedStage(embedder=embedder)


def build_index_stage(
    config: ScragConfig, 
    index_path: Optional[Path] = None,
    backend_type: Optional[str] = None
) -> IndexStage:
    """Build an index stage from configuration."""
    index_store = build_index_store(config, index_path, backend_type)
    return IndexStage(index_store=index_store)


def build_retrieval_stage(
    config: ScragConfig,
    index_path: Optional[Path] = None,
    model_type: Optional[str] = None,
    backend_type: Optional[str] = None
) -> RetrievalStage:
    """Build a retrieval stage from configuration."""
    embedder = build_embedder(config, model_type)
    index_store = build_index_store(config, index_path, backend_type)
    
    rag_config = config.data.get("rag", {})
    retrieval_config = rag_config.get("retrieval", {})
    
    return RetrievalStage(
        embedder=embedder,
        index_store=index_store,
        top_k=retrieval_config.get("default_top_k", 10),
        threshold=retrieval_config.get("default_threshold", 0.0)
    )


def build_rag_pipeline_components(config: ScragConfig) -> Dict[str, Any]:
    """Build all RAG pipeline components from configuration."""
    rag_config = config.data.get("rag", {})
    
    # Check if RAG pipeline is enabled
    pipeline_config = config.data.get("pipeline", {})
    rag_pipeline_config = pipeline_config.get("rag_pipeline", {})
    
    if not rag_pipeline_config.get("enabled", False):
        logger.info("RAG pipeline is disabled in configuration")
        return {}
    
    components = {}
    
    try:
        # Build chunking processor
        components["chunking_processor"] = build_chunking_processor(config)
        
        # Build embedder
        components["embedder"] = build_embedder(config)
        
        # Build default index store
        components["index_store"] = build_index_store(config)
        
        # Build stages
        components["embed_stage"] = build_embed_stage(config)
        components["index_stage"] = build_index_stage(config)
        components["retrieval_stage"] = build_retrieval_stage(config)
        
        logger.info("Successfully built RAG pipeline components")
        
    except Exception as e:
        logger.error(f"Error building RAG pipeline components: {e}")
        raise
    
    return components