"""Tests for case-insensitive HTTP header handling."""

import pytest

from src.scrag.core.utils.headers import (
    CaseInsensitiveDict,
    normalize_headers,
    get_header_value,
    create_cache_key_from_headers,
)


def test_case_insensitive_dict_basic_operations():
    """Test basic operations of CaseInsensitiveDict."""
    headers = CaseInsensitiveDict()
    
    # Test setting and getting with different cases
    headers["User-Agent"] = "TestAgent/1.0"
    assert headers["user-agent"] == "TestAgent/1.0"
    assert headers["USER-AGENT"] == "TestAgent/1.0"
    assert headers["User-Agent"] == "TestAgent/1.0"
    
    # Test contains
    assert "user-agent" in headers
    assert "USER-AGENT" in headers
    assert "User-Agent" in headers
    assert "content-type" not in headers


def test_case_insensitive_dict_get_method():
    """Test the get method with case-insensitive lookup."""
    headers = CaseInsensitiveDict({"User-Agent": "TestAgent/1.0"})
    
    assert headers.get("user-agent") == "TestAgent/1.0"
    assert headers.get("USER-AGENT") == "TestAgent/1.0"
    assert headers.get("User-Agent") == "TestAgent/1.0"
    assert headers.get("content-type") is None
    assert headers.get("content-type", "default") == "default"


def test_case_insensitive_dict_update():
    """Test updating with case-insensitive handling."""
    headers = CaseInsensitiveDict({"User-Agent": "TestAgent/1.0"})
    
    # Update with different case
    headers.update({"user-agent": "UpdatedAgent/2.0"})
    assert headers["User-Agent"] == "UpdatedAgent/2.0"
    
    # Add new header
    headers.update({"Accept": "text/html"})
    assert headers["accept"] == "text/html"
    assert headers["Accept"] == "text/html"


def test_case_insensitive_dict_preserves_original_case():
    """Test that original case is preserved for display."""
    headers = CaseInsensitiveDict()
    headers["User-Agent"] = "TestAgent/1.0"
    headers["accept"] = "text/html"
    headers["Content-Type"] = "text/html"
    
    # Keys should be in their original case
    keys = list(headers.keys())
    assert "User-Agent" in keys
    assert "accept" in keys
    assert "Content-Type" in keys


def test_normalize_headers():
    """Test the normalize_headers function."""
    regular_dict = {"User-Agent": "TestAgent/1.0", "Accept": "text/html"}
    normalized = normalize_headers(regular_dict)
    
    assert isinstance(normalized, CaseInsensitiveDict)
    assert normalized["user-agent"] == "TestAgent/1.0"
    assert normalized["accept"] == "text/html"


def test_get_header_value():
    """Test the get_header_value function."""
    headers = {"User-Agent": "TestAgent/1.0", "Accept": "text/html"}
    
    # Test with regular dictionary
    assert get_header_value(headers, "user-agent") == "TestAgent/1.0"
    assert get_header_value(headers, "USER-AGENT") == "TestAgent/1.0"
    assert get_header_value(headers, "User-Agent") == "TestAgent/1.0"
    assert get_header_value(headers, "content-type") is None
    assert get_header_value(headers, "content-type", "default") == "default"
    
    # Test with CaseInsensitiveDict
    normalized_headers = normalize_headers(headers)
    assert get_header_value(normalized_headers, "user-agent") == "TestAgent/1.0"
    assert get_header_value(normalized_headers, "USER-AGENT") == "TestAgent/1.0"


def test_create_cache_key_from_headers():
    """Test cache key generation from headers."""
    headers = {
        "User-Agent": "TestAgent/1.0",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",  # Should be ignored
    }
    
    # Test with default relevant headers
    cache_key = create_cache_key_from_headers(headers)
    expected_parts = [
        "accept:text/html",
        "accept-language:en-US,en;q=0.9",
        "user-agent:TestAgent/1.0",
    ]
    expected_key = "|".join(expected_parts)
    assert cache_key == expected_key
    
    # Test with custom relevant headers
    custom_key = create_cache_key_from_headers(
        headers, 
        relevant_headers=["User-Agent", "Content-Type"]
    )
    expected_custom_parts = [
        "content-type:application/json",
        "user-agent:TestAgent/1.0",
    ]
    expected_custom_key = "|".join(expected_custom_parts)
    assert custom_key == expected_custom_key


def test_create_cache_key_case_insensitive():
    """Test that cache key generation is case-insensitive."""
    headers1 = {
        "User-Agent": "TestAgent/1.0",
        "Accept": "text/html",
    }
    
    headers2 = {
        "user-agent": "TestAgent/1.0",
        "accept": "text/html",
    }
    
    headers3 = {
        "USER-AGENT": "TestAgent/1.0",
        "ACCEPT": "text/html",
    }
    
    key1 = create_cache_key_from_headers(headers1)
    key2 = create_cache_key_from_headers(headers2)
    key3 = create_cache_key_from_headers(headers3)
    
    # All should produce the same cache key
    assert key1 == key2 == key3


def test_case_insensitive_dict_error_handling():
    """Test error handling in CaseInsensitiveDict."""
    headers = CaseInsensitiveDict()
    
    # Test with non-string key
    with pytest.raises(TypeError):
        headers[123] = "value"
    
    with pytest.raises(TypeError):
        headers.get(123)
    
    with pytest.raises(KeyError):
        headers["nonexistent"]
    
    # Test pop with non-string key
    with pytest.raises(KeyError):
        headers.pop(123)
    
    # Test del with non-string key
    with pytest.raises(KeyError):
        del headers[123]
