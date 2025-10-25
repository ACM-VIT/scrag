"""OpenAI-based embedder implementation."""

from __future__ import annotations

from typing import Dict, Any, List
import logging
import os

from .base import BaseEmbedder, EmbeddingContext, EmbeddingResult

logger = logging.getLogger(__name__)


class OpenAIEmbedder(BaseEmbedder):
    """Embedder using OpenAI's embedding API."""
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: str | None = None,
        batch_size: int = 100
    ) -> None:
        super().__init__(name="openai", model_name=model_name)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.batch_size = batch_size
        self._client = None
        
        # Model dimensions mapping
        self._model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
    def _get_client(self):
        """Lazy load the OpenAI client."""
        if self._client is not None:
            return self._client
            
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            
        try:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
            return self._client
        except ImportError:
            raise ImportError("openai library is required. Install with: pip install openai")
    
    @property
    def is_available(self) -> bool:
        """Check if OpenAI client is available and configured."""
        try:
            import openai
            return bool(self.api_key)
        except ImportError:
            return False
    
    def embed(self, context: EmbeddingContext) -> EmbeddingResult:
        """Generate embeddings using OpenAI API."""
        if not context.texts:
            return EmbeddingResult(
                embeddings=[],
                metadata={"model": self.model_name, "count": 0},
                success=True
            )
        
        try:
            client = self._get_client()
            all_embeddings = []
            
            # Process in batches to respect API limits
            for i in range(0, len(context.texts), self.batch_size):
                batch_texts = context.texts[i:i + self.batch_size]
                
                response = client.embeddings.create(
                    model=self.model_name,
                    input=batch_texts
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            
            metadata = {
                "model": self.model_name,
                "dimension": self.get_embedding_dimension(),
                "count": len(all_embeddings),
                "batch_size": self.batch_size,
                **context.metadata
            }
            
            return EmbeddingResult(
                embeddings=all_embeddings,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings with OpenAI {self.model_name}: {e}")
            return EmbeddingResult(
                embeddings=[],
                metadata={"error": str(e), "model": self.model_name},
                success=False
            )
    
    def get_embedding_dimension(self) -> int:
        """Return the embedding dimension for the model."""
        return self._model_dimensions.get(self.model_name, 1536)