# ADR-001: PipelineStage Interface Design

**Status:** Proposed  
**Date:** 2025-10-25  
**Deciders:** Development Team  

## Context

As we expand Scrag with web crawling and RAG indexing capabilities, we need a consistent interface for all pipeline components to ensure:
- Predictable integration patterns
- Consistent error handling
- Standardized configuration
- Uniform monitoring and observability

Current components (extractors, processors, storage) have similar but inconsistent interfaces, which could lead to integration issues as we add crawling and indexing stages.

## Decision

We will implement a standardized `PipelineStage` interface that all pipeline components must implement:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class StageContext:
    """Common context passed between pipeline stages"""
    data: Any
    metadata: Dict[str, Any]
    stage_config: Dict[str, Any]

@dataclass
class StageResult:
    """Standardized result from pipeline stages"""
    data: Any
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class PipelineStage(ABC, Generic[T, U]):
    """Base interface for all pipeline components"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    @abstractmethod
    def process(self, context: StageContext[T]) -> StageResult[U]:
        """Process input context and return result"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate stage configuration"""
        pass
    
    def supports(self, context: StageContext[T]) -> bool:
        """Check if stage can process the given context"""
        return True
```

## Consequences

### Positive
- Consistent interface across all components
- Easier testing with standardized mocks
- Simplified pipeline orchestration
- Better error handling and monitoring
- Clear separation of concerns

### Negative
- Requires refactoring existing components
- Additional abstraction layer
- Learning curve for contributors

## Implementation Plan

1. Define the interface in `src/scrag/core/pipeline/stages.py`
2. Migrate existing extractors to implement PipelineStage
3. Update processors and storage adapters
4. Implement new crawling stages with the interface
5. Update pipeline orchestration to use standardized interface

## Related

- Issue: [To be created] - Implement PipelineStage interface
- Epic: Web Crawling & Discovery System