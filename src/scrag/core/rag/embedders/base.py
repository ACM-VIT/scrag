"""Base embedding interfaces for RAG components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List
import numpy as np


@dataclass(slots=True)
class EmbeddingContext:
    """Input context for embedding generation."""
    
    texts: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EmbeddingResult:
    """Result from embedding generation."""
    
    embeddings: List[List[float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


class BaseEmbedder(ABC):
    """Abstract base class for embedding models."""
    
    def __init__(self, name: str, model_name: str) -> None:
        self.name = name
        self.model_name = model_name
    
    @abstractmethod
    def embed(self, context: EmbeddingContext) -> EmbeddingResult:
        """Generate embeddings for the given texts."""
        
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        
    @property
    def is_available(self) -> bool:
        """Check if the embedder is properly configured and available."""
        return True