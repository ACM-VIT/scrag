# ADR-002: CrawlManager Design for Error Handling & Orchestration

**Status:** Proposed  
**Date:** 2025-10-25  
**Deciders:** Development Team  

## Context

Web crawling introduces new challenges not present in single-URL extraction:
- Network failures and timeouts
- Rate limiting and backoff strategies
- Content deduplication
- Resource management (memory, connections)
- Batch processing coordination
- Partial failure handling

The current `PipelineRunner` is designed for single-document processing and lacks the resilience patterns needed for large-scale crawling operations.

## Decision

We will implement a `CrawlManager` that handles orchestration, error recovery, and resource management for multi-document crawling:

```python
@dataclass
class CrawlJob:
    """Represents a crawling job with multiple URLs"""
    job_id: str
    urls: List[str]
    config: CrawlConfig
    created_at: datetime
    status: CrawlStatus

@dataclass
class CrawlResult:
    """Result from crawling operation"""
    job_id: str
    successful_urls: List[str]
    failed_urls: List[FailedUrl]
    total_processed: int
    artifacts: List[Path]

class CrawlManager:
    """Orchestrates crawling operations with error handling"""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.retry_handler = RetryHandler(config.retry_policy)
        self.rate_limiter = RateLimiter(config.rate_limits)
        self.deduplicator = ContentDeduplicator()
    
    async def crawl(self, job: CrawlJob) -> CrawlResult:
        """Execute crawling job with error handling"""
        pass
    
    def recover_failed_urls(self, job_id: str) -> CrawlResult:
        """Retry failed URLs from previous job"""
        pass
```

### Key Features

1. **Retry Logic**: Exponential backoff with jitter
2. **Rate Limiting**: Per-domain and global rate limits
3. **Deduplication**: Content-based and URL-based deduplication
4. **Partial Recovery**: Ability to retry only failed URLs
5. **Resource Management**: Connection pooling and memory limits
6. **Progress Tracking**: Real-time job status and metrics

## Consequences

### Positive
- Robust error handling for production crawling
- Efficient resource utilization
- Resumable crawling operations
- Better user experience with progress tracking
- Scalable to large URL lists

### Negative
- Added complexity
- More configuration options to manage
- Additional testing requirements
- Potential performance overhead

## Implementation Plan

1. Create `CrawlManager` in `src/scrag/core/crawling/`
2. Implement retry and rate limiting utilities
3. Add deduplication mechanisms
4. Create job persistence for recovery
5. Update CLI to support crawling commands
6. Add comprehensive monitoring and logging

## Configuration

```yaml
crawling:
  retry_policy:
    max_attempts: 3
    backoff_multiplier: 2.0
    max_delay: 300
  rate_limits:
    global_rps: 10
    per_domain_rps: 2
  deduplication:
    enabled: true
    similarity_threshold: 0.95
  resources:
    max_concurrent: 10
    connection_timeout: 30
    max_memory_mb: 1024
```

## Related

- ADR-001: PipelineStage Interface Design
- Issue: [To be created] - Implement CrawlManager
- Epic: Web Crawling & Discovery System