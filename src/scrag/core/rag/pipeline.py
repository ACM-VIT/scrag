"""End-to-end RAG pipeline runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from scrag.core.utils import ScragConfig
from scrag.core.pipeline.stages import StageContext
from scrag.core.processors.base import ProcessingContext
from .factory import (
    build_chunking_processor,
    build_embed_stage, 
    build_index_stage,
    build_retrieval_stage
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RAGPipelineResult:
    """Result from RAG pipeline execution."""
    
    success: bool
    chunks: List[str] = None
    embeddings: List[List[float]] = None
    indexed: bool = False
    query_results: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None


class RAGPipelineRunner:
    """Orchestrate end-to-end RAG pipeline operations."""
    
    def __init__(self, config: ScragConfig) -> None:
        self.config = config
    
    def build_index_from_content(
        self,
        content: str,
        index_path: Path,
        source_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGPipelineResult:
        """Build a complete RAG index from raw content."""
        try:
            metadata = source_metadata or {}
            
            # Step 1: Chunk the content
            chunking_processor = build_chunking_processor(self.config)
            processing_context = ProcessingContext(content=content, metadata=metadata)
            chunking_result = chunking_processor.process(processing_context)
            
            if not chunking_result.metadata.get("chunks"):
                return RAGPipelineResult(
                    success=False,
                    error_message="Failed to chunk content"
                )
            
            chunks = chunking_result.metadata["chunks"]
            
            # Step 2: Generate embeddings
            embed_stage = build_embed_stage(self.config)
            embed_context = StageContext(data=chunks, metadata=chunking_result.metadata)
            embed_result = embed_stage.process(embed_context)
            
            if not embed_result.success:
                return RAGPipelineResult(
                    success=False,
                    chunks=chunks,
                    error_message=embed_result.error_message
                )
            
            embeddings = embed_result.data
            
            # Step 3: Build index
            index_stage = build_index_stage(self.config, index_path=index_path)
            index_context = StageContext(
                data=(chunks, embeddings),
                metadata=embed_result.metadata
            )
            index_result = index_stage.process(index_context)
            
            if not index_result.success:
                return RAGPipelineResult(
                    success=False,
                    chunks=chunks,
                    embeddings=embeddings,
                    error_message=index_result.error_message
                )
            
            return RAGPipelineResult(
                success=True,
                chunks=chunks,
                embeddings=embeddings,
                indexed=True,
                metadata=index_result.metadata
            )
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return RAGPipelineResult(
                success=False,
                error_message=str(e)
            )
    
    def query_index(
        self,
        query_text: str,
        index_path: Path,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> RAGPipelineResult:
        """Query an existing RAG index."""
        try:
            # Build retrieval stage
            retrieval_stage = build_retrieval_stage(self.config, index_path=index_path)
            
            # Set up query context
            stage_config = {}
            if top_k is not None:
                stage_config["top_k"] = top_k
            if threshold is not None:
                stage_config["threshold"] = threshold
            
            query_context = StageContext(
                data=query_text,
                stage_config=stage_config
            )
            
            # Execute query
            query_result = retrieval_stage.process(query_context)
            
            if not query_result.success:
                return RAGPipelineResult(
                    success=False,
                    error_message=query_result.error_message
                )
            
            return RAGPipelineResult(
                success=True,
                query_results=query_result.data,
                metadata=query_result.metadata
            )
            
        except Exception as e:
            logger.error(f"Error querying RAG index: {e}")
            return RAGPipelineResult(
                success=False,
                error_message=str(e)
            )
    
    def build_index_from_url(
        self,
        url: str,
        index_path: Path
    ) -> RAGPipelineResult:
        """Extract content from URL and build RAG index."""
        try:
            # Use existing pipeline to extract content
            import importlib.util
            
            # Import PipelineRunner from the pipeline.py file
            pipeline_file = Path(__file__).parent.parent / "pipeline.py"
            spec = importlib.util.spec_from_file_location("pipeline_module", pipeline_file)
            pipeline_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pipeline_module)
            PipelineRunner = pipeline_module.PipelineRunner
            
            pipeline_runner = PipelineRunner(self.config)
            extraction_result = pipeline_runner.run(url=url)
            
            if not extraction_result.content:
                return RAGPipelineResult(
                    success=False,
                    error_message="Failed to extract content from URL"
                )
            
            # Add URL metadata
            source_metadata = {
                "url": url,
                "extractor": extraction_result.extractor,
                "processors": extraction_result.processors,
                **extraction_result.metadata
            }
            
            # Build index from extracted content
            return self.build_index_from_content(
                content=extraction_result.content,
                index_path=index_path,
                source_metadata=source_metadata
            )
            
        except Exception as e:
            logger.error(f"Error building index from URL {url}: {e}")
            return RAGPipelineResult(
                success=False,
                error_message=str(e)
            )