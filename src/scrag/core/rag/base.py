"""RAG component interfaces and baseline implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(slots=True)
class RAGContext:
    """Payload required to build or query RAG structures."""

    chunks: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RAGResult:
    """Result returned by a RAG component."""

    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRAGComponent(ABC):
    """Base class for RAG-oriented operations."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def run(self, context: RAGContext) -> RAGResult:
        """Execute the component behavior against the context."""


class NoOpRAGComponent(BaseRAGComponent):
    """Skeleton implementation that performs no mutations."""

    def __init__(self) -> None:
        super().__init__(name="noop")

    def run(self, context: RAGContext) -> RAGResult:
        """Return a success result with untouched metadata."""

        return RAGResult(success=True, metadata={"component": self.name, **context.metadata})


# Import submodules for convenience
from . import embedders, stores
from .query import QueryProcessor, RAGQueryManager
