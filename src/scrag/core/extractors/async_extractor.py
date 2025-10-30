"""Async HTTP extractor using aiohttp for concurrent scraping."""

from __future__ import annotations
from ..utils.utils import parse_html_content
from ..utils.headers import normalize_headers, get_header_value


import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import aiohttp
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised in unit tests
    aiohttp = None  # type: ignore[assignment]

from .base import BaseExtractor, ExtractionContext, ExtractionResult
from ..utils.cache import HttpCache, build_conditional_headers


class AsyncHttpExtractor(BaseExtractor):
    """Async extractor using aiohttp for concurrent batch scraping."""

    def __init__(
        self,
        *,
        user_agent: Optional[str] = None,
        timeout: int = 10,
        max_concurrent: int = 10,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
        cache_max_age: int = 3600,
    ) -> None:
        super().__init__(name="async_http")
        self._user_agent = user_agent or "ScragBot/0.1"
        self._timeout = timeout
        self._max_concurrent = max_concurrent
        self._enable_cache = enable_cache
        self._cache = HttpCache(cache_dir=cache_dir, max_age=cache_max_age) if enable_cache else None

    def supports(self, context: ExtractionContext) -> bool:
        """Check if aiohttp is available."""
        return aiohttp is not None and bool(context.url)

    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Extract content synchronously (for single URL compatibility)."""
        if not context.url:
            return ExtractionResult(
                content="",
                metadata={"extractor": self.name, "reason": "missing_url"},
                succeeded=False,
            )

        if aiohttp is None:
            return ExtractionResult(
                content="",
                metadata={"extractor": self.name, "reason": "aiohttp not installed"},
                succeeded=False,
            )

        try:
            return asyncio.run(self._extract_single(context))
        except Exception as error:
            return ExtractionResult(
                content="",
                metadata={"extractor": self.name, "reason": str(error)},
                succeeded=False,
            )

    async def _extract_single(self, context: ExtractionContext) -> ExtractionResult:
        """Extract content from a single URL using aiohttp."""
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        headers = {"User-Agent": self._user_agent}
        
<<<<<<< HEAD
        # Add config headers
        config_headers = context.metadata.get("headers", {}) if context.metadata else {}
        headers.update(config_headers)
        
        # Check cache bypass setting
        bypass_cache = context.metadata.get("bypass_cache", False) if context.metadata else False

        # Try to get from cache first (if caching is enabled and not bypassed)
        if self._cache and not bypass_cache:
            cached_entry = self._cache.get(context.url, headers)
            if cached_entry:
                # Use cached content
                soup = BeautifulSoup(cached_entry.content, "html.parser")
                text_segments = list(s.strip() for s in soup.stripped_strings)
                content = "\n".join(segment for segment in text_segments if segment)

                metadata: Dict[str, Any] = {
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
=======
        # Normalize headers for case-insensitive handling
        headers = normalize_headers(headers)
>>>>>>> fix/version-consolidation

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                # If we have a cached entry, try conditional request first
                if self._cache and not bypass_cache:
                    cached_entry = self._cache.get(context.url, headers)
                    if cached_entry:
                        conditional_headers = build_conditional_headers(cached_entry)
                        headers.update(conditional_headers)
                
                async with session.get(context.url, headers=headers) as response:
                    # Handle 304 Not Modified response
                    if response.status == 304 and self._cache and not bypass_cache:
                        cached_entry = self._cache.get(context.url, headers)
                        if cached_entry:
                            soup = BeautifulSoup(cached_entry.content, "html.parser")
                            text_segments = list(s.strip() for s in soup.stripped_strings)
                            content = "\n".join(segment for segment in text_segments if segment)

                            metadata: Dict[str, Any] = {
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
                    html = await response.text()
                    
                    # Cache the response if caching is enabled
                    if self._cache and not bypass_cache:
                        # Create a mock requests.Response-like object for caching
                        class MockResponse:
                            def __init__(self, text: str, status: int, headers: Dict[str, str]):
                                self.text = text
                                self.status_code = status
                                self.headers = headers
                        
                        mock_response = MockResponse(html, response.status, dict(response.headers))
                        self._cache.put(context.url, headers, mock_response)

<<<<<<< HEAD
                    soup = BeautifulSoup(html, "html.parser")
                    text_segments = list(s.strip() for s in soup.stripped_strings)
                    content = "\n".join(segment for segment in text_segments if segment)

                    metadata: Dict[str, Any] = {
                        "extractor": self.name,
                        "status_code": response.status,
                        "title": soup.title.string.strip() if soup.title and soup.title.string else None,
                        "cached": False,
                        **(context.metadata or {}),
                    }
=======
                    # Use the shared helper method
                    content, metadata = parse_html_content(html, self.name, response.status)
>>>>>>> fix/version-consolidation

                    return ExtractionResult(
                        content=content,
                        metadata=metadata,
                        succeeded=bool(content.strip()),
                    )
            except asyncio.TimeoutError:
                return ExtractionResult(
                    content="",
                    metadata={"extractor": self.name, "reason": "Request timeout"},
                    succeeded=False,
                )
            except aiohttp.ClientError as error:
                return ExtractionResult(
                    content="",
                    metadata={"extractor": self.name, "reason": str(error)},
                    succeeded=False,
                )

    async def extract_batch(self, contexts: List[ExtractionContext]) -> List[ExtractionResult]:
        """Extract content from multiple URLs concurrently."""
        if aiohttp is None:
            return [
                ExtractionResult(
                    content="",
                    metadata={"extractor": self.name, "reason": "aiohttp not installed"},
                    succeeded=False,
                )
            ] * len(contexts)

        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def fetch_with_semaphore(context: ExtractionContext) -> ExtractionResult:
            async with semaphore:
                return await self._extract_single(context)

        tasks = [fetch_with_semaphore(context) for context in contexts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(
                    ExtractionResult(
                        content="",
                        metadata={"extractor": self.name, "reason": str(result)},
                        succeeded=False,
                    )
                )
            else:
                processed_results.append(result)

        return processed_results
