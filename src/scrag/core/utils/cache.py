"""HTTP caching utilities for web scraping."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import requests


class CacheEntry:
    """Represents a cached HTTP response."""
    
    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        content: str,
        status_code: int,
        response_headers: Dict[str, str],
        timestamp: float,
    ):
        self.url = url
        self.headers = headers
        self.content = content
        self.status_code = status_code
        self.response_headers = response_headers
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "headers": self.headers,
            "content": self.content,
            "status_code": self.status_code,
            "response_headers": self.response_headers,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CacheEntry:
        """Create from dictionary."""
        return cls(
            url=data["url"],
            headers=data["headers"],
            content=data["content"],
            status_code=data["status_code"],
            response_headers=data["response_headers"],
            timestamp=data["timestamp"],
        )


class HttpCache:
    """Lightweight on-disk HTTP cache with ETag and Last-Modified support."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_age: int = 3600):
        """
        Initialize HTTP cache.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.scrag/cache
            max_age: Maximum age of cached entries in seconds (default: 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".scrag" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = max_age
    
    def _get_cache_key(self, url: str, headers: Dict[str, str]) -> str:
        """Generate cache key from URL and relevant headers."""
        # Include User-Agent and other relevant headers in cache key
        relevant_headers = {
            k: v for k, v in headers.items() 
            if k.lower() in {"user-agent", "accept", "accept-language"}
        }
        
        key_data = f"{url}:{json.dumps(relevant_headers, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, url: str, headers: Dict[str, str]) -> Optional[CacheEntry]:
        """
        Get cached response if available and not expired.
        
        Args:
            url: URL to fetch
            headers: Request headers
            
        Returns:
            Cached entry if available and fresh, None otherwise
        """
        cache_key = self._get_cache_key(url, headers)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            entry = CacheEntry.from_dict(data)
            
            # Check if cache entry is expired
            if time.time() - entry.timestamp > self.max_age:
                cache_path.unlink()  # Remove expired entry
                return None
            
            return entry
            
        except (json.JSONDecodeError, KeyError, OSError):
            # Remove corrupted cache file
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def put(self, url: str, headers: Dict[str, str], response: requests.Response) -> None:
        """
        Cache HTTP response.
        
        Args:
            url: URL that was fetched
            headers: Request headers used
            response: HTTP response to cache
        """
        cache_key = self._get_cache_key(url, headers)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            entry = CacheEntry(
                url=url,
                headers=headers,
                content=response.text,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                timestamp=time.time(),
            )
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False)
                
        except OSError:
            # Ignore cache write errors
            pass
    
    def clear(self) -> None:
        """Clear all cached entries."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cache state."""
        if not self.cache_dir.exists():
            return {"entries": 0, "size_bytes": 0, "cache_dir": str(self.cache_dir)}
        
        entries = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in entries)
        
        return {
            "entries": len(entries),
            "size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }


def get_cache_headers(response_headers: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract ETag and Last-Modified headers from response.
    
    Args:
        response_headers: Response headers dictionary
        
    Returns:
        Tuple of (etag, last_modified) values
    """
    etag = response_headers.get("etag")
    last_modified = response_headers.get("last-modified")
    return etag, last_modified


def build_conditional_headers(
    cached_entry: CacheEntry, 
    use_etag: bool = True, 
    use_last_modified: bool = True
) -> Dict[str, str]:
    """
    Build conditional request headers from cached entry.
    
    Args:
        cached_entry: Previously cached response
        use_etag: Whether to include If-None-Match header
        use_last_modified: Whether to include If-Modified-Since header
        
    Returns:
        Dictionary of conditional headers
    """
    headers = {}
    
    if use_etag and cached_entry.response_headers.get("etag"):
        headers["If-None-Match"] = cached_entry.response_headers["etag"]
    
    if use_last_modified and cached_entry.response_headers.get("last-modified"):
        headers["If-Modified-Since"] = cached_entry.response_headers["last-modified"]
    
    return headers
