# Project Structure Summary

This document provides a complete overview of the Scrag project structure and organization.

## Directory Structure

```
scrag/
├── ARCHITECTURE.md                    # Comprehensive architecture documentation
├── CODE_OF_CONDUCT.md                # Community conduct guidelines
├── CONTRIBUTING.md                   # Contribution guidelines
├── LICENSE                          # Project license
├── README.md                        # Updated project overview with structure
│
├── src/scrag/                       # Main source code package
│   ├── __init__.py                  # Package initialization
│   ├── extractors/                  # Content extraction strategies
│   ├── processors/                  # Text processing and cleaning
│   ├── storage/                     # Storage backends and adapters
│   ├── rag/                         # RAG pipeline components
│   ├── cli/                         # Command-line interface
│   ├── web/                         # Web interface
│   └── utils/                       # Utility functions and helpers
│
├── tests/                           # Comprehensive test suite
│   ├── README.md                    # Testing documentation
│   ├── unit/                        # Unit tests for individual components
│   ├── integration/                 # Integration tests for workflows
│   ├── performance/                 # Performance and benchmark tests
│   └── fixtures/                    # Test data and mock objects
│
├── docs/                            # Project documentation
│   ├── api/                         # API reference documentation
│   │   └── README.md                # API documentation overview
│   ├── guides/                      # User and developer guides
│   │   ├── README.md                # Guides overview
│   │   ├── getting-started.md       # Quick start guide
│   │   └── development.md           # Development setup guide
│   └── tutorials/                   # Step-by-step tutorials
│       └── README.md                # Tutorials overview
│
├── config/                          # Configuration management
│   ├── README.md                    # Configuration documentation
│   ├── extractors/                  # Extractor-specific configurations
│   └── rag/                         # RAG pipeline configurations
│
├── deployment/                      # Deployment configurations
│   ├── README.md                    # Deployment documentation
│   ├── docker/                      # Docker configurations
│   ├── kubernetes/                  # Kubernetes manifests
│   └── aws/                         # AWS-specific deployment files
│
└── scripts/                         # Development and build scripts
    └── README.md                    # Scripts documentation
```

## Key Architectural Decisions

### 1. Dependency Management
- **Canonical Source**: Dependencies are defined in `src/scrag/pyproject.toml`
- **Package Manager**: Uses `uv` for dependency resolution and virtual environment management
- **Lock File**: `src/scrag/uv.lock` ensures reproducible builds
- **No requirements.txt**: Root `requirements.txt` has been removed to avoid conflicts with `pyproject.toml`

### 2. Modular Design
- **Extractors**: Pluggable content extraction strategies
- **Processors**: Composable text processing pipeline
- **Storage**: Flexible storage backend adapters
- **RAG**: Specialized RAG pipeline components

### 3. Configuration-Driven
- Hierarchical configuration system
- Environment-specific overrides
- Runtime parameter support
- Validation and schema enforcement

### 4. Extensibility Focus
- Clear interfaces for new components
- Template-based extension patterns
- Plugin architecture support
- Factory patterns for component creation

### 5. Testing Strategy
- Unit tests for individual components
- Integration tests for workflows
- Performance benchmarks
- Comprehensive test fixtures

### 6. Documentation-First
- Architecture documentation (ARCHITECTURE.md)
- API reference generation
- User guides and tutorials
- Tutorial code validation

## Design Patterns Used

1. **Strategy Pattern** - Multiple extraction/processing strategies
2. **Factory Pattern** - Component instantiation and management
3. **Pipeline Pattern** - Sequential processing workflows
4. **Adapter Pattern** - External service integration
5. **Observer Pattern** - Event-driven interactions
6. **Template Method** - Extensible workflow patterns

## Development Workflow

### For Contributors
1. Read `docs/guides/getting-started.md`
2. Follow setup in `docs/guides/development.md`
3. Write tests in appropriate `tests/` subdirectory
4. Update documentation for new features

### For Users
1. Install following `docs/guides/getting-started.md`
2. Refer to `docs/api/` for detailed API documentation
3. Check `docs/tutorials/` for step-by-step guides

## Quality Assurance

### Code Quality
- Type hints throughout codebase
- Comprehensive docstrings
- Automated linting and formatting
- Security scanning integration

### Testing Coverage
- Unit test coverage targets
- Integration test scenarios
- Performance benchmark suites
- Continuous integration workflows

### Documentation Standards
- Architecture documentation
- API reference generation
- User guide maintenance
- Tutorial code validation

## Future Extensions

The structure supports future enhancements:
- Microservices migration path
- Additional extraction strategies
- New storage backends
- Enhanced web interface
- Advanced RAG capabilities

## Maintenance

### Regular Tasks
- Dependency updates via `scripts/`
- Documentation updates
- Performance monitoring
- Security audits

### Release Process
- Version management
- Changelog maintenance
- Automated testing
- Documentation deployment

This structure provides a solid foundation for the Scrag project, enabling scalable development, easy maintenance, and clear contributor onboarding.