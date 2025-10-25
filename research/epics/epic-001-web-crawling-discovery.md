# EPIC 1: Web Crawling & Discovery System

**Epic ID:** EPIC-001  
**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Duration:** 8-10 weeks  
**Created:** 2025-10-25  

## Problem Statement

The current Scrag system can only extract content from individual URLs provided by users. To realize the vision of the Universal RAG Builder, we need a system that can automatically discover, crawl, and process relevant web content based on user queries. This capability is essential for creating comprehensive knowledge bases without manual URL collection.

## Solution Overview

Implement a web crawling and discovery system that:
1. Converts user queries into search strategies
2. Discovers relevant URLs from multiple sources
3. Fetches content with robust error handling and retry logic
4. Processes content using existing pipeline components
5. Manages the entire workflow with proper orchestration

## Scope & Boundaries

### In Scope
- [ ] Discovery Query stage: Convert user intent to search strategy
- [ ] Search stage: Find relevant URLs from web search APIs and RSS feeds
- [ ] Fetch stage: Retrieve content with rate limiting and error handling
- [ ] Process stage: Integration with existing extractor/processor pipeline
- [ ] CrawlManager: Job orchestration, error recovery, and progress tracking
- [ ] CLI commands for crawling operations
- [ ] Configuration system for crawling parameters

### Out of Scope
- [ ] Embedding generation (covered in EPIC-002)
- [ ] Index construction (covered in EPIC-002)
- [ ] Advanced JavaScript rendering (future enhancement)
- [ ] Distributed crawling across multiple machines
- [ ] Real-time crawling/monitoring

## User Stories / Subtasks

### Discovery Phase
- [ ] [SPIKE-001] - Web Crawler Architecture Research
- [ ] [SPIKE-002] - Discovery Query Strategy Analysis
- [ ] [SPIKE-003] - Search API Integration Evaluation

### Implementation Phase
- [ ] [TASK-001] - Implement PipelineStage interface
- [ ] [TASK-002] - Create Discovery Query stage
- [ ] [TASK-003] - Implement Search stage with web search APIs
- [ ] [TASK-004] - Build Fetch stage with retry logic
- [ ] [TASK-005] - Create CrawlManager for orchestration
- [ ] [TASK-006] - Add CLI commands for crawling
- [ ] [TASK-007] - Implement job persistence and recovery

### Integration & Testing Phase
- [ ] [TASK-008] - Integration testing with existing pipeline
- [ ] [TASK-009] - Performance testing and optimization
- [ ] [TASK-010] - Documentation and user guides

## Success Criteria

- [ ] Users can crawl content using queries like "latest machine learning research papers"
- [ ] System can handle 100+ URLs per crawl job with <5% failure rate
- [ ] Crawling respects robots.txt and implements proper rate limiting
- [ ] Failed URLs can be retried without reprocessing successful ones
- [ ] Integration maintains backward compatibility with existing extraction features
- [ ] Performance: Process 10+ URLs per minute on standard hardware

## Technical Requirements

### Architecture
- [ ] All components implement PipelineStage interface for consistency
- [ ] CrawlManager provides centralized orchestration and error handling
- [ ] Modular design allows easy addition of new discovery sources
- [ ] Clear separation between discovery, search, fetch, and process stages

### Performance
- [ ] Handle 1000+ URLs per crawl job
- [ ] Memory usage <1GB for typical jobs
- [ ] Concurrent processing with configurable limits
- [ ] Efficient deduplication to avoid redundant work

### Quality
- [ ] Code coverage ≥85% for new components
- [ ] Comprehensive error handling for network failures
- [ ] Proper logging and monitoring for debugging
- [ ] Configuration validation and helpful error messages

## Dependencies

### Internal Dependencies
- [ ] PipelineStage interface design and implementation
- [ ] Existing extractor/processor pipeline
- [ ] Configuration system enhancements

### External Dependencies
- [ ] Web search API access (Google Custom Search, Bing, etc.)
- [ ] HTTP libraries for web requests
- [ ] Rate limiting and retry libraries

## Risk Assessment

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Search API rate limits | High | Medium | Implement multiple API providers and local caching |
| Complex website structures | Medium | High | Use existing multi-strategy extraction approach |
| Performance with large URL lists | Medium | Medium | Implement streaming processing and memory optimization |
| Integration complexity | Medium | Low | Maintain existing interface contracts |

## Milestones & Timeline

- [ ] **Discovery Complete** - Week 2 - All spike work and research finished
- [ ] **Core Components** - Week 5 - Discovery, Search, Fetch stages implemented
- [ ] **Integration Complete** - Week 7 - CrawlManager and CLI integration
- [ ] **Production Ready** - Week 10 - Testing, docs, and performance optimization

## Architecture Overview

```
User Query → Discovery Query → Search → Fetch → Process → Storage
                ↓              ↓        ↓       ↓
           Search Strategy   URL List  Content  Processed Data
                            
           CrawlManager orchestrates entire workflow with:
           - Job persistence
           - Error recovery  
           - Progress tracking
           - Resource management
```

## Definition of Done

An epic is considered complete when:

- [ ] All linked subtasks are completed and closed
- [ ] Users can successfully crawl content based on text queries
- [ ] System handles both successful crawling and error scenarios gracefully
- [ ] Code review completed and approved for all components
- [ ] Unit tests written with ≥85% coverage for new code
- [ ] Integration tests cover major crawling workflows
- [ ] Performance benchmarks meet stated requirements
- [ ] Documentation updated (API docs, user guides, architecture)
- [ ] CLI commands are intuitive and well-documented
- [ ] Configuration system is flexible and validated
- [ ] Backward compatibility maintained with existing features

## Key Configuration

```yaml
# Addition to config/default.yml
crawling:
  discovery:
    enabled: true
    default_sources: ["web_search", "rss"]
    query_expansion: true
  
  search:
    web_search:
      provider: "google"  # google, bing, duckduckgo
      api_key: "${SEARCH_API_KEY}"
      results_per_query: 20
    rss:
      enabled: true
      default_feeds: []
  
  fetch:
    max_concurrent: 10
    rate_limit:
      requests_per_second: 5
      requests_per_domain: 2
    retry_policy:
      max_attempts: 3
      backoff_multiplier: 2.0
      max_delay: 300
    timeout: 30
  
  deduplication:
    enabled: true
    similarity_threshold: 0.95
    
  storage:
    job_persistence: true
    job_storage_dir: "data/crawl_jobs"
```

## Artifacts

- [ ] Architecture design document
- [ ] API specification for new components
- [ ] Performance benchmark results
- [ ] User guide for crawling features
- [ ] Configuration reference documentation
- [ ] Migration guide for existing users

## Related Epics

- **EPIC-002**: RAG Index Construction (depends on this epic)
- **Future**: Advanced JavaScript Rendering
- **Future**: Distributed Crawling System