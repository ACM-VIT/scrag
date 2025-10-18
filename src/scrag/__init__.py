# Scrag - Adaptive Web Scraper for RAG Pipelines
__version__ = "0.1.0"
__author__ = "ACM VIT"
__description__ = "Adaptive, multi-strategy web scraper for RAG pipelines and local LLM workflows"

# Import main CLI function for easy access
from .cli import main

__all__ = ["main", "__version__"]