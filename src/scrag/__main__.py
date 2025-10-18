#!/usr/bin/env python3
"""
Main entry point for running Scrag as a module.

This allows the package to be executed with:
    python -m scrag
"""

from .cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())