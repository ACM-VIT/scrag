# Version Consolidation Fix

## Overview

This PR consolidates duplicate version definitions to eliminate the risk of version drift between multiple sources.

## Problem

The project had version definitions in two locations:
- `src/scrag/pyproject.toml` (canonical source)
- `src/scrag/core/__init__.py` (duplicate)

This created a risk of version drift where the two definitions could become out of sync.

## Solution

- **Removed duplicate** `__version__` from `core/__init__.py`
- **Updated CLI** to read version directly from `pyproject.toml` using `tomllib`
- **Added error handling** for cases where `pyproject.toml` cannot be read
- **Single source of truth** now maintained in `pyproject.toml`

## Changes Made

### Modified Files
- `src/scrag/core/__init__.py` - Removed duplicate `__version__` definition
- `src/scrag/core/cli/app.py` - Updated to read version from `pyproject.toml`

### Technical Details
- Added `_get_version()` function that reads from `pyproject.toml`
- Uses `tomllib` for TOML parsing (Python 3.11+)
- Graceful fallback to "unknown" if version cannot be read
- No breaking changes to CLI interface

## Acceptance Criteria Met

- [x] **One and only one definition of version remains**
  - Version now only defined in `pyproject.toml`
  - Duplicate removed from `core/__init__.py`

- [x] **uv run scrag --version prints the expected version**
  - CLI now reads version from canonical source
  - Tested and verified to work correctly

## Testing

The implementation has been tested to ensure:
- Version is correctly read from `pyproject.toml`
- CLI `--version` command works as expected
- No duplicate version definitions remain
- Error handling works for edge cases

## Benefits

- **Eliminates version drift risk** - Single source of truth
- **Maintains CLI compatibility** - No breaking changes
- **Follows best practices** - Version in project metadata
- **Robust error handling** - Graceful fallbacks

This fix ensures version consistency across the project and follows Python packaging best practices.
