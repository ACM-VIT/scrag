# Research & Discovery Documentation

This directory maintains institutional knowledge from discovery phases, spikes, and research efforts to prevent knowledge loss and inform future decisions.

## Structure

### `/spikes/`
Individual spike investigations with clear goals, findings, and recommendations:
- `web-crawler-architecture/` - Initial crawler design research
- `embedding-models-evaluation/` - Embedding model comparison
- `index-storage-backends/` - Storage backend analysis
- `search-apis-integration/` - External search API evaluation

### `/benchmarks/`
Performance and quality benchmarks:
- `extraction-speed-tests.md` - Extraction performance across strategies
- `content-quality-metrics.md` - Content quality evaluation criteria
- `index-query-performance.md` - Index query speed benchmarks

### `/decisions/`
Architecture decision records (ADRs):
- `001-pipeline-stage-interface.md` - Standardized pipeline component interface
- `002-crawl-manager-design.md` - Error handling and orchestration approach
- `003-index-store-abstraction.md` - Storage backend abstraction design

### `/prototypes/`
Proof-of-concept implementations and experiments:
- Working code that validates architectural decisions
- Small-scale implementations for testing approaches
- Integration experiments

## Guidelines

### Spike Documentation Template
Each spike should include:
1. **Objective** - Clear goals and success criteria
2. **Approach** - Methodology and tools used
3. **Findings** - Data, observations, and insights
4. **Recommendations** - Actionable next steps
5. **Artifacts** - Code, configs, or data produced

### Knowledge Preservation
- All major decisions must be documented
- Include context and trade-offs considered
- Link to related issues and PRs
- Update when decisions change

### Benchmarking Standards
- Reproducible test environments
- Clear metrics and measurement criteria
- Version all test data and configurations
- Regular updates to track improvements