# CLI Versioning Strategy

**Date:** 2025-10-25  
**Status:** Proposed  

## Objective

Implement CLI versioning to ensure backward compatibility and smooth upgrades as we add web crawling and RAG indexing features.

## Current State

- CLI currently has basic commands: `info`, `extract`
- No versioning strategy in place
- Configuration changes could break existing workflows

## Proposed Versioning Strategy

### 1. Semantic Versioning for CLI Commands

```python
# Add to core/cli/app.py
CLI_VERSION = "v1"  # Major version for breaking changes

app = typer.Typer(
    name=f"scrag-{CLI_VERSION}",
    help="Adaptive scraping toolkit for RAG pipelines."
)
```

### 2. Command Organization

```
scrag v1 commands:
├── info                    # Current config inspection
├── extract <url>           # Single URL extraction
└── config validate         # Validate configuration

scrag v2 commands (future):
├── v1 commands (maintained)
├── crawl query <query>     # Discovery-based crawling
├── crawl urls <file>       # Batch URL crawling  
├── index build <job_id>    # Build RAG index from crawl
├── index query <query>     # Query existing index
└── job status <job_id>     # Check crawl/index job status
```

### 3. Configuration Schema Versioning

```yaml
# config/default.yml
schema_version: "1.0"
environment: default

# v1.0 config
scraping:
  user_agent: "scragBot/0.1"
  request_timeout: 10

pipeline:
  extractors: ["newspaper", "readability", "http"]
  processors: ["normalize_whitespace"]
  minimum_content_length: 200
  storage:
    type: file
    options:
      directory: data
      format: json

# v2.0 config (future) - additive only
crawling:
  discovery:
    enabled: false  # Default to maintain backward compatibility
    sources: ["web_search", "rss"]
  batch:
    max_concurrent: 10
    retry_policy:
      max_attempts: 3

indexing:
  enabled: false  # Default to maintain backward compatibility
  backend: "file"
  embedding:
    model: "sentence-transformers/all-MiniLM-L6-v2"
```

## Implementation Plan

### Phase 1: Add Versioning Foundation
1. Add CLI version constant
2. Implement config schema validation
3. Add backward compatibility layer
4. Update documentation

### Phase 2: Maintain Compatibility
1. Keep v1 commands working
2. Add deprecation warnings when appropriate
3. Provide migration guides
4. Test compatibility across versions

## Configuration Migration Strategy

```python
class ConfigMigrator:
    """Handle config schema migrations"""
    
    def migrate(self, config_data: dict) -> dict:
        schema_version = config_data.get("schema_version", "1.0")
        
        if schema_version == "1.0":
            return self._migrate_1_0_to_2_0(config_data)
        return config_data
    
    def _migrate_1_0_to_2_0(self, config: dict) -> dict:
        """Migrate v1.0 config to v2.0 with defaults"""
        migrated = config.copy()
        migrated["schema_version"] = "2.0"
        
        # Add new sections with safe defaults
        migrated.setdefault("crawling", {
            "discovery": {"enabled": False},
            "batch": {"max_concurrent": 10}
        })
        
        migrated.setdefault("indexing", {
            "enabled": False,
            "backend": "file"
        })
        
        return migrated
```

## Deprecation Strategy

```python
def deprecated_command(func):
    """Decorator for deprecated CLI commands"""
    def wrapper(*args, **kwargs):
        typer.echo(
            "Warning: This command is deprecated and will be removed in v3. "
            "Use 'scrag crawl' instead.",
            err=True
        )
        return func(*args, **kwargs)
    return wrapper

@app.command()
@deprecated_command
def old_command():
    """Legacy command with deprecation warning"""
    pass
```

## Benefits

1. **Backward Compatibility**: Existing scripts continue working
2. **Clear Migration Path**: Users know when and how to upgrade
3. **Feature Rollout**: New features can be added gradually
4. **Risk Reduction**: Breaking changes are controlled and communicated

## Testing Strategy

1. **Version Compatibility Tests**: Test old configs with new CLI
2. **Migration Tests**: Validate config migrations work correctly
3. **Integration Tests**: Ensure new features don't break old workflows
4. **Documentation Tests**: Keep examples up-to-date

## Documentation Updates

1. **Migration Guide**: Step-by-step upgrade instructions
2. **Version Changelog**: Clear list of changes per version
3. **Compatibility Matrix**: What works with what
4. **Deprecation Timeline**: When features will be removed