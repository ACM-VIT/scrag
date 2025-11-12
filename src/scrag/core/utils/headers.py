"""HTTP header utilities for case-insensitive operations."""

from typing import Any, Dict, Optional


class CaseInsensitiveDict(dict):
    """A dictionary that performs case-insensitive lookups for HTTP headers.
    
    HTTP header names are case-insensitive according to RFC 7230. This class
    provides case-insensitive dictionary operations while preserving the original
    case of keys for display purposes.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._key_map = {}  # Maps lowercase keys to original keys
        self.update(*args, **kwargs)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set item with case-insensitive key handling."""
        if not isinstance(key, str):
            raise TypeError("Header keys must be strings")
        
        # Store the original case for display
        original_key = key
        lower_key = key.lower()
        
        # Remove any existing key with different case
        if lower_key in self._key_map:
            old_key = self._key_map[lower_key]
            if old_key != original_key:
                super().__delitem__(old_key)
        
        self._key_map[lower_key] = original_key
        super().__setitem__(original_key, value)
    
    def __getitem__(self, key: str) -> Any:
        """Get item with case-insensitive lookup."""
        if not isinstance(key, str):
            raise TypeError("Header keys must be strings")
        
        lower_key = key.lower()
        if lower_key in self._key_map:
            original_key = self._key_map[lower_key]
            return super().__getitem__(original_key)
        raise KeyError(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists with case-insensitive lookup."""
        if not isinstance(key, str):
            return False
        return key.lower() in self._key_map
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item with case-insensitive lookup, returning default if not found."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key: str, default: Any = None) -> Any:
        """Pop item with case-insensitive lookup."""
        if not isinstance(key, str):
            if default is not None:
                return default
            raise KeyError(key)
        
        lower_key = key.lower()
        if lower_key in self._key_map:
            original_key = self._key_map[lower_key]
            del self._key_map[lower_key]
            return super().pop(original_key, default)
        
        if default is not None:
            return default
        raise KeyError(key)
    
    def update(self, *args, **kwargs) -> None:
        """Update dictionary with case-insensitive handling."""
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 argument, got %d" % len(args))
            other = args[0]
            if hasattr(other, 'items'):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value
        
        for key, value in kwargs.items():
            self[key] = value
    
    def __delitem__(self, key: str) -> None:
        """Delete item with case-insensitive lookup."""
        if not isinstance(key, str):
            raise KeyError(key)
        
        lower_key = key.lower()
        if lower_key in self._key_map:
            original_key = self._key_map[lower_key]
            del self._key_map[lower_key]
            super().__delitem__(original_key)
        else:
            raise KeyError(key)
    
    def keys(self):
        """Return keys in their original case."""
        return super().keys()
    
    def items(self):
        """Return items with keys in their original case."""
        return super().items()
    
    def values(self):
        """Return values."""
        return super().values()
    
    def copy(self):
        """Create a copy of this case-insensitive dictionary."""
        new_dict = CaseInsensitiveDict()
        new_dict.update(self)
        return new_dict


def normalize_headers(headers: Dict[str, Any]) -> CaseInsensitiveDict:
    """Convert a regular dictionary to a case-insensitive header dictionary.
    
    Args:
        headers: Dictionary of HTTP headers
        
    Returns:
        CaseInsensitiveDict with normalized header handling
    """
    return CaseInsensitiveDict(headers)


def get_header_value(headers: Dict[str, Any], header_name: str, default: Any = None) -> Any:
    """Get a header value with case-insensitive lookup.
    
    Args:
        headers: Dictionary of HTTP headers
        header_name: Name of the header to retrieve
        default: Default value if header not found
        
    Returns:
        Header value or default if not found
    """
    if isinstance(headers, CaseInsensitiveDict):
        return headers.get(header_name, default)
    
    # For regular dictionaries, do case-insensitive lookup
    header_name_lower = header_name.lower()
    for key, value in headers.items():
        if key.lower() == header_name_lower:
            return value
    return default


def create_cache_key_from_headers(headers: Dict[str, Any], relevant_headers: list[str] = None) -> str:
    """Create a cache key from relevant HTTP headers.
    
    Args:
        headers: Dictionary of HTTP headers
        relevant_headers: List of header names to include in cache key
        
    Returns:
        String representation of relevant headers for cache key
    """
    if relevant_headers is None:
        relevant_headers = ["User-Agent", "Accept", "Accept-Language"]
    
    # Normalize headers for case-insensitive lookup
    normalized_headers = normalize_headers(headers)
    
    # Extract relevant headers in a consistent order
    key_parts = []
    for header_name in sorted(relevant_headers):
        value = get_header_value(normalized_headers, header_name)
        if value is not None:
            key_parts.append(f"{header_name.lower()}:{value}")
    
    return "|".join(key_parts)
