"""Retrieval stage for querying and retrieving relevant content."""

from __future__ import annotations

from typing import Any, Dict, List
import logging

from scrag.core.pipeline.stages import PipelineStage, StageContext, StageResult
from ..query import RAGQueryManager
from ..embedders import BaseEmbedder
from ..stores import IndexStore

logger = logging.getLogger(__name__)


class RetrievalStage(PipelineStage[str, Dict[str, Any]]):
    """Pipeline stage that performs retrieval queries against indexed content."""
    
    def __init__(
        self,
        embedder: BaseEmbedder,
        index_store: IndexStore,
        top_k: int = 10,
        threshold: float = 0.0,
        name: str = "retrieval",
        config: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(name=name, config=config)
        self.query_manager = RAGQueryManager(
            embedder=embedder,
            index_store=index_store,
            default_top_k=top_k,
            default_threshold=threshold
        )
        self.embedder = embedder
        self.index_store = index_store
    
    def process(self, context: StageContext[str]) -> StageResult[Dict[str, Any]]:
        """Perform retrieval query and return results."""
        try:
            query_text = context.data.strip()
            
            if not query_text:
                return StageResult(
                    data={"results": [], "retrieved_content": "", "result_count": 0},
                    metadata={**context.metadata, "stage": self.name},
                    success=False,
                    error_message="Empty query"
                )
            
            # Extract query parameters from context
            top_k = context.stage_config.get("top_k", self.query_manager.default_top_k)
            threshold = context.stage_config.get("threshold", self.query_manager.default_threshold)
            filters = context.stage_config.get("filters", {})
            include_scores = context.stage_config.get("include_scores", True)
            
            # Execute query
            query_result = self.query_manager.query(
                query_text=query_text,
                top_k=top_k,
                threshold=threshold,
                filters=filters,
                include_scores=include_scores
            )
            
            if not query_result["success"]:
                return StageResult(
                    data=query_result,
                    metadata={**context.metadata, "stage": self.name},
                    success=False,
                    error_message=query_result.get("error", "Query failed")
                )
            
            # Combine metadata
            result_metadata = {
                **context.metadata,
                "stage": self.name,
                "query": query_text,
                "top_k": top_k,
                "threshold": threshold,
                "filters": filters,
                "embedder": self.embedder.name,
                "index_store": self.index_store.name
            }
            
            return StageResult(
                data=query_result,
                metadata=result_metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in retrieval stage: {e}")
            return StageResult(
                data={"results": [], "retrieved_content": "", "result_count": 0},
                metadata={**context.metadata, "stage": self.name, "error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    def validate_config(self) -> bool:
        """Validate retrieval stage configuration."""
        return self.embedder.is_available and self.index_store.is_available
    
    def supports(self, context: StageContext[str]) -> bool:
        """Check if the stage can process the given context."""
        return isinstance(context.data, str)
    
    @property
    def is_available(self) -> bool:
        """Check if the retrieval stage is available."""
        return self.embedder.is_available and self.index_store.is_available