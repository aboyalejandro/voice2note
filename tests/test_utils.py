import pytest
from datetime import datetime, timedelta
from backend.cache import QueryCache


def test_cache_ttl(cache):
    """Test cache TTL functionality"""
    # Set with 1 second TTL
    cache.set("ttl_test", "value", timeout=1)
    assert cache.get("ttl_test") == "value"

    # Wait for expiration
    import time

    time.sleep(1.1)
    assert cache.get("ttl_test") is None


def test_cache_maxsize(cache):
    """Test cache maxsize limit"""
    # Fill cache to maxsize
    for i in range(1000):
        cache.set(f"key_{i}", f"value_{i}")

    # Verify older items are evicted
    assert cache.get("key_0") is None


def test_datetime_serialization(cache):
    """Test datetime handling in cache"""
    now = datetime.now()
    data = {"timestamp": now, "date": now.date()}
    assert cache.set("datetime_test", data)
    retrieved = cache.get("datetime_test")
    assert isinstance(retrieved["timestamp"], str)
    assert isinstance(retrieved["date"], str)
