"""PipelineStage interface and standardized components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar('T')
U = TypeVar('U')


@dataclass(slots=True)
class StageContext:
    """Common context passed between pipeline stages."""
    
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage_config: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StageResult:
    """Standardized result from pipeline stages."""
    
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class PipelineStage(ABC, Generic[T, U]):
    """Base interface for all pipeline components."""
    
    def __init__(self, name: str, config: Dict[str, Any] | None = None) -> None:
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def process(self, context: StageContext[T]) -> StageResult[U]:
        """Process input context and return result."""
        
    def validate_config(self) -> bool:
        """Validate stage configuration."""
        return True
    
    def supports(self, context: StageContext[T]) -> bool:
        """Check if stage can process the given context."""
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if the stage is properly configured and available."""
        return True