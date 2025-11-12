"""Extractor interfaces and base implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from ..utils.utils import parse_html_content
from ..utils.headers import normalize_headers, get_header_value

from ..utils.cache import HttpCache, build_conditional_headers


@dataclass(slots=True)
class ExtractionContext:
    """Input payload for extraction strategies."""

    url: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractionResult:
    """Normalized output from an extractor."""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    succeeded: bool = True


class BaseExtractor(ABC):
    """Abstract base for all extraction strategies."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Extract content from a URL-centered context."""

    def supports(self, context: ExtractionContext) -> bool:
        """Return True when the extractor can handle the given context."""

        return bool(context.url)

"""Extractor interfaces and base implementations."""

# ...existing imports...

class SimpleExtractor(BaseExtractor):
    """HTTP-based extractor that fetches and cleans web page content."""

    def __init__(
        self, 
        *, 
        user_agent: Optional[str] = None, 
        timeout: int = 10,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
        cache_max_age: int = 3600,
    ) -> None:
        super().__init__(name="http")
        self._user_agent = user_agent or "ScragBot/0.1"
        self._timeout = timeout
        self._enable_cache = enable_cache
        self._cache = HttpCache(cache_dir=cache_dir, max_age=cache_max_age) if enable_cache else None

    def _get_metadata_value(self, context: ExtractionContext, key: str, default: Any) -> Any:
        """Helper method to retrieve a value from context metadata."""
        return context.metadata.get(key, default) if context.metadata else default

    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Fetch the page via HTTP and extract readable text using BeautifulSoup."""

        if not context.url:
            return ExtractionResult(
                content="",
                metadata={"extractor": self.name, "reason": "missing_url"},
                succeeded=False,
            )

        headers = {"User-Agent": self._user_agent}
        config_headers = self._get_metadata_value(context, "headers", {})
        headers.update(config_headers)
<<<<<<< HEAD
        timeout = context.metadata.get("timeout", self._timeout) if context.metadata else self._timeout
        
        # Check cache bypass setting
        bypass_cache = context.metadata.get("bypass_cache", False) if context.metadata else False
=======
        
        # Normalize headers for case-insensitive handling
        headers = normalize_headers(headers)
        timeout = self._get_metadata_value(context, "timeout", self._timeout)
>>>>>>> fix/version-consolidation

        # Try to get from cache first (if caching is enabled and not bypassed)
        if self._cache and not bypass_cache:
            cached_entry = self._cache.get(context.url, headers)
            if cached_entry:
                # Use cached content
                soup = BeautifulSoup(cached_entry.content, "html.parser")
                text_segments = list(s.strip() for s in soup.stripped_strings)
                content = "\n".join(segment for segment in text_segments if segment)

                metadata = {
                    "extractor": self.name,
                    "status_code": cached_entry.status_code,
                    "title": soup.title.string.strip() if soup.title and soup.title.string else None,
                    "cached": True,
                    "cache_timestamp": cached_entry.timestamp,
                    **(context.metadata or {}),
                }

                return ExtractionResult(
                    content=content,
                    metadata=metadata,
                    succeeded=bool(content.strip()),
                )

        # Make HTTP request
        try:
            # If we have a cached entry, try conditional request first
            if self._cache and not bypass_cache:
                cached_entry = self._cache.get(context.url, headers)
                if cached_entry:
                    conditional_headers = build_conditional_headers(cached_entry)
                    headers.update(conditional_headers)
            
            response = requests.get(context.url, headers=headers, timeout=timeout)
            
            # Handle 304 Not Modified response
            if response.status_code == 304 and self._cache and not bypass_cache:
                cached_entry = self._cache.get(context.url, headers)
                if cached_entry:
                    soup = BeautifulSoup(cached_entry.content, "html.parser")
                    text_segments = list(s.strip() for s in soup.stripped_strings)
                    content = "\n".join(segment for segment in text_segments if segment)

                    metadata = {
                        "extractor": self.name,
                        "status_code": cached_entry.status_code,
                        "title": soup.title.string.strip() if soup.title and soup.title.string else None,
                        "cached": True,
                        "not_modified": True,
                        "cache_timestamp": cached_entry.timestamp,
                        **(context.metadata or {}),
                    }

                    return ExtractionResult(
                        content=content,
                        metadata=metadata,
                        succeeded=bool(content.strip()),
                    )
            
            response.raise_for_status()
            
            # Cache the response if caching is enabled
            if self._cache and not bypass_cache:
                self._cache.put(context.url, headers, response)
                
        except requests.RequestException as error:
            return ExtractionResult(
                content="",
                metadata={
                    "extractor": self.name,
                    "reason": str(error),
                },
                succeeded=False,
            )

<<<<<<< HEAD
        soup = BeautifulSoup(response.text, "html.parser")
        text_segments = list(s.strip() for s in soup.stripped_strings)
        content = "\n".join(segment for segment in text_segments if segment)

        metadata = {
            "extractor": self.name,
            "status_code": response.status_code,
            "title": soup.title.string.strip() if soup.title and soup.title.string else None,
            "cached": False,
            **(context.metadata or {}),
        }
=======
        content, metadata = parse_html_content(response.text, self.name, response.status_code)
        metadata.update(context.metadata or {})
>>>>>>> fix/version-consolidation

        return ExtractionResult(
            content=content,
            metadata=metadata,
            succeeded=bool(content.strip()),
        )