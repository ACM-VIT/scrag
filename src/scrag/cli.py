#!/usr/bin/env python3
"""
Scrag CLI - Command Line Interface for the Scrag web scraper.

This module provides the main entry point for the Scrag command-line interface.
"""

import sys
from typing import List, Optional


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the Scrag CLI.
    
    Args:
        args: Command line arguments. If None, uses sys.argv[1:]
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if args is None:
        args = sys.argv[1:]
    
    print("Hello from Scrag! 🕷️")
    print("Adaptive web scraper for RAG pipelines and local LLM workflows")
    print(f"Version: 0.1.0")
    
    if args:
        print(f"Arguments received: {args}")
    else:
        print("No arguments provided. Use --help for usage information.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())