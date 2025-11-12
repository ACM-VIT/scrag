"""Utility functions for content extraction."""

from typing import Any, Dict, Tuple
from bs4 import BeautifulSoup


def parse_html_content(html: str, extractor_name: str, status_code: int) -> Tuple[str, Dict[str, Any]]:
    """Parse HTML content using BeautifulSoup and extract text and metadata.

    Args:
        html (str): The HTML content to parse.
        extractor_name (str): The name of the extractor.
        status_code (int): The HTTP status code of the response.

    Returns:
        Tuple[str, Dict[str, Any]]: Extracted content and metadata.
    """
    soup = BeautifulSoup(html, "html.parser")
    text_segments = list(s.strip() for s in soup.stripped_strings)
    content = "\n".join(segment for segment in text_segments if segment)

    metadata = {
        "extractor": extractor_name,
        "status_code": status_code,
        "title": soup.title.string.strip() if soup.title and soup.title.string else None,
    }

    return content, metadata