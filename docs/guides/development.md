# Development Setup Guide

This document tracks the current contributor workflow for Scrag. It assumes you are working on the Python CLI and pipeline that live under `src/scrag/core`.

## Prerequisites

- Python 3.13 (matches `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) 0.4+ (manages virtualenvs and dependency resolution)
- Git
- Optional: Node.js 20+ if you plan to work on the Next.js frontend in `src/web`

## Environment Setup

1. **Fork and clone**

   ```bash
   git clone https://github.com/YOUR_USERNAME/scrag.git
   cd scrag
   ```

2. **Install dependencies**

   ```bash
   uv sync
   uv pip install -e src/scrag
   ```

   - `uv sync` bootstraps the project environment.
   - The editable install exposes the `scrag` entry point so you can iterate on the CLI.

3. **Smoke-test the CLI**

   ```bash
   uv run scrag info
   ```

   Seeing the merged configuration JSON confirms the config loader and Typer wiring are in sync.

## Daily Workflow

### Run tests

```bash
# Entire test suite
uv run pytest

# Target specific modules
uv run pytest tests/unit/test_cli.py -k min_length
```

Unit coverage currently focuses on the CLI contract, extractor fallbacks, and pipeline orchestration. Add regression tests any time you modify these behaviors.

### Code quality

`pyproject.toml` defines Ruff rules. Install Ruff locally (once) to lint before committing:

```bash
uv tool install ruff
ruff check src tests
ruff format src tests
```

If you prefer, add Ruff as a dev dependency via `uv add --dev ruff`.

### Configuration tips

- Defaults live in `config/default.yml`. Create environment-specific overrides (e.g. `config/local.yml`) when you need experimental tweaks.
- The pipeline honors optional sections:
  - `pipeline.extractor_options.<key>` for constructor kwargs per extractor.
  - `pipeline.processor_options.<key>` for processor kwargs.
  - `pipeline.minimum_content_length` prevents short, noisy pages from halting the pipeline; use the CLI `--min-length` flag for ad-hoc overrides.

### Extending the pipeline

| Component | Location | Registration |
|-----------|----------|--------------|
| Extractor | `core/extractors/` | Add class and register in `EXTRACTOR_REGISTRY` |
| Processor | `core/processors/` | Register in `PROCESSOR_REGISTRY` |
| Storage   | `core/storage/`    | Register in `STORAGE_REGISTRY` |

Implementation checklist:

1. Create the class (subclassing the appropriate base type).
2. Register the class in the relevant registry so configuration keys resolve.
3. Add tests in `tests/unit/` that cover success and failure paths. Use `unittest.mock` to avoid hitting the network.
4. Update documentation (this guide or architecture notes) and sample configuration if new options are required.

### Debugging

- Use `uv run python -m core.cli extract ...` when you want to attach a debugger via `-m pdb`.
- Inspect failure output: the pipeline now bubbles up the last failure reason (e.g. short content) to speed up diagnosis.
- Saved artifacts in `data/` include metadata with extractor and processor details; examine them to understand actual runtime behavior.

## Project Layout

```
src/scrag/core/
├── cli/            # Typer entry points and CLI glue
├── extractors/     # Strategy implementations & registry
├── processors/     # Text normalization steps & registry
├── storage/        # Persistence adapters (memory, file, etc.)
├── pipeline.py     # PipelineRunner orchestrating the stages
└── utils/          # Config loader and supporting utilities
```

Tests mirror the runtime modules under `tests/unit/`.

## Contribution Checklist

1. Create a feature branch from `main`.
2. Write or update tests before finalizing the implementation.
3. Ensure `uv run pytest` passes.
4. Run `ruff check` (or your chosen linter) and fix reported issues.
5. Update relevant docs (`README.md`, guides, config comments) to reflect user-facing changes.
6. Submit a PR with a concise description, reproduction steps (if fixing a bug), and screenshots or sample command output when helpful.

## Getting Help

- Review [ARCHITECTURE.md](../../ARCHITECTURE.md) for a high-level overview of the extractor/processor/storage contracts.
- Explore existing tests to understand mocking patterns and expected behavior.
- Open a discussion or issue on GitHub when you encounter blocking questions.