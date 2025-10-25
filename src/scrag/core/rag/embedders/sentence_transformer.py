"""SentenceTransformer-based embedder implementation."""

from __future__ import annotations

from typing import Dict, Any, List
import logging

from .base import BaseEmbedder, EmbeddingContext, EmbeddingResult

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Embedder using SentenceTransformers library."""
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_folder: str | None = None
    ) -> None:
        super().__init__(name="sentence_transformer", model_name=model_name)
        self.device = device
        self.cache_folder = cache_folder
        self._model = None
        self._embedding_dimension = None
        
    def _load_model(self) -> None:
        """Lazy load the SentenceTransformer model."""
        if self._model is not None:
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_folder
            )
            # Get embedding dimension by encoding a sample
            sample_embedding = self._model.encode(["sample"], convert_to_numpy=True)
            self._embedding_dimension = sample_embedding.shape[1]
            logger.info(f"Loaded SentenceTransformer model {self.model_name} with dimension {self._embedding_dimension}")
        except ImportError:
            raise ImportError("sentence-transformers library is required. Install with: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model {self.model_name}: {e}")
            raise
    
    @property
    def is_available(self) -> bool:
        """Check if SentenceTransformers is available."""
        try:
            import sentence_transformers
            return True
        except ImportError:
            return False
    
    def embed(self, context: EmbeddingContext) -> EmbeddingResult:
        """Generate embeddings using SentenceTransformers."""
        if not context.texts:
            return EmbeddingResult(
                embeddings=[],
                metadata={"model": self.model_name, "count": 0},
                success=True
            )
        
        try:
            self._load_model()
            
            # Generate embeddings
            embeddings = self._model.encode(
                context.texts,
                convert_to_numpy=True,
                show_progress_bar=len(context.texts) > 100
            )
            
            # Convert to list of lists for JSON serialization
            embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            metadata = {
                "model": self.model_name,
                "dimension": self._embedding_dimension,
                "count": len(embeddings_list),
                "device": self.device,
                **context.metadata
            }
            
            return EmbeddingResult(
                embeddings=embeddings_list,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings with {self.model_name}: {e}")
            return EmbeddingResult(
                embeddings=[],
                metadata={"error": str(e), "model": self.model_name},
                success=False
            )
    
    def get_embedding_dimension(self) -> int:
        """Return the embedding dimension."""
        if self._embedding_dimension is None:
            self._load_model()
        return self._embedding_dimension