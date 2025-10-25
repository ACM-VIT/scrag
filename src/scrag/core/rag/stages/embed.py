"""Embed stage for generating embeddings from content."""

from __future__ import annotations

from typing import Any, Dict, List
import logging

from scrag.core.pipeline.stages import PipelineStage, StageContext, StageResult
from ..embedders import BaseEmbedder, EmbeddingContext

logger = logging.getLogger(__name__)


class EmbedStage(PipelineStage[List[str], List[List[float]]]):
    """Pipeline stage that generates embeddings from text chunks."""
    
    def __init__(
        self,
        embedder: BaseEmbedder,
        name: str = "embed",
        config: Dict[str, Any] | None = None
    ) -> None:
        super().__init__(name=name, config=config)
        self.embedder = embedder
    
    def process(self, context: StageContext[List[str]]) -> StageResult[List[List[float]]]:
        """Generate embeddings for the given text chunks."""
        try:
            if not context.data:
                return StageResult(
                    data=[],
                    metadata={**context.metadata, "embedding_count": 0},
                    success=True
                )
            
            # Create embedding context
            embedding_context = EmbeddingContext(
                texts=context.data,
                metadata=context.metadata
            )
            
            # Generate embeddings
            embedding_result = self.embedder.embed(embedding_context)
            
            if not embedding_result.success:
                return StageResult(
                    data=[],
                    metadata={**context.metadata, **embedding_result.metadata},
                    success=False,
                    error_message="Failed to generate embeddings"
                )
            
            # Combine metadata
            result_metadata = {
                **context.metadata,
                **embedding_result.metadata,
                "stage": self.name,
                "embedder": self.embedder.name,
                "embedding_count": len(embedding_result.embeddings)
            }
            
            return StageResult(
                data=embedding_result.embeddings,
                metadata=result_metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in embed stage: {e}")
            return StageResult(
                data=[],
                metadata={**context.metadata, "stage": self.name, "error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    def validate_config(self) -> bool:
        """Validate embed stage configuration."""
        return self.embedder.is_available
    
    def supports(self, context: StageContext[List[str]]) -> bool:
        """Check if the stage can process the given context."""
        return isinstance(context.data, list) and all(isinstance(item, str) for item in context.data)
    
    @property 
    def is_available(self) -> bool:
        """Check if the embed stage is available."""
        return self.embedder.is_available