"""Processor interfaces and base implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

import re


@dataclass(slots=True)
class ProcessingContext:
    """Input payload for processor components."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProcessingResult:
    """Output from processor components."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProcessor(ABC):
    """Base class for content processors."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Transform processed content and metadata."""


class NormalizeWhitespaceProcessor(BaseProcessor):
    """Condense whitespace and enrich metadata with basic statistics."""

    def __init__(self, *, minimum_characters: int = 0) -> None:
        super().__init__(name="normalize_whitespace")
        self._minimum_characters = minimum_characters

    def process(self, context: ProcessingContext) -> ProcessingResult:
        cleaned = _normalize_whitespace(context.content)
        metadata = {
            **context.metadata,
            "processor": self.name,
            "char_count": len(cleaned),
            "meets_threshold": len(cleaned) >= self._minimum_characters,
        }
        return ProcessingResult(content=cleaned, metadata=metadata)


def _normalize_whitespace(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    return collapsed


PROCESSOR_REGISTRY = {
    "normalize_whitespace": NormalizeWhitespaceProcessor,
    "simple": NormalizeWhitespaceProcessor,
    "chunking": lambda **kwargs: _import_chunking_processor(**kwargs),
}


def _import_chunking_processor(**kwargs):
    """Lazy import ChunkingProcessor to avoid circular imports."""
    from .chunking import ChunkingProcessor
    return ChunkingProcessor(**kwargs)


def build_processors(names: Iterable[str], *, options: Dict[str, Dict] | None = None) -> List[BaseProcessor]:
    options = options or {}
    processors: List[BaseProcessor] = []
    for name in names:
        cls = PROCESSOR_REGISTRY.get(name)
        if not cls:
            continue
        kwargs = options.get(name, {})
        if callable(cls):
            processors.append(cls(**kwargs))
    return processors


# Backwards compatibility alias
SimpleProcessor = NormalizeWhitespaceProcessor
