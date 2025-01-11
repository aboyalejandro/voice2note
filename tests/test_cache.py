import pytest
from backend.cache import QueryCache


def test_cache_set_get(cache):
    """Test basic cache operations"""
    # Test setting and getting
    assert cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"

    # Test deletion
    assert cache.delete("test_key")
    assert cache.get("test_key") is None


def test_cache_invalidation(cache):
    """Test cache invalidation"""
    cache.set("notes:test_schema", ["note1", "note2"])
    cache.set("note:test_schema:123", {"title": "Test"})

    # Test invalidation
    assert cache.delete("notes:test_schema")
    assert cache.get("notes:test_schema") is None


def test_cache_serialization(cache):
    """Test JSON serialization"""
    complex_data = {
        "title": "Test Note",
        "items": [1, 2, 3],
        "metadata": {"key": "value"},
    }
    assert cache.set("test_complex", complex_data)
    assert cache.get("test_complex") == complex_data
