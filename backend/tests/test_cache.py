"""
Tests for cache functionality.
"""
import pytest
from app.core.cache import SimpleCache
import time


def test_cache_basic_operations():
    """Test basic cache get/set operations."""
    cache = SimpleCache(name="test", ttl=60)
    
    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Test cache miss
    assert cache.get("nonexistent") is None


def test_cache_expiration():
    """Test that cached values expire after TTL."""
    cache = SimpleCache(name="test", ttl=1)  # 1 second TTL
    
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key1") is None


def test_cache_invalidation():
    """Test cache invalidation."""
    cache = SimpleCache(name="test", ttl=60)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    # Invalidate single key
    cache.invalidate("key1")
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"


def test_cache_invalidate_pattern():
    """Test pattern-based invalidation."""
    cache = SimpleCache(name="test", ttl=60)
    
    cache.set("profile_1", "data1")
    cache.set("profile_2", "data2")
    cache.set("model_1", "data3")
    
    # Invalidate all profile keys
    count = cache.invalidate_pattern("profile_")
    assert count == 2
    assert cache.get("profile_1") is None
    assert cache.get("profile_2") is None
    assert cache.get("model_1") == "data3"


def test_cache_clear():
    """Test clearing entire cache."""
    cache = SimpleCache(name="test", ttl=60)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_stats():
    """Test cache statistics."""
    cache = SimpleCache(name="test", ttl=60)
    
    # Initial stats
    stats = cache.stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["size"] == 0
    
    # Add data and check
    cache.set("key1", "value1")
    cache.get("key1")  # Hit
    cache.get("key2")  # Miss
    
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["name"] == "test"
    assert stats["ttl"] == 60


def test_cache_complex_values():
    """Test caching complex data structures."""
    cache = SimpleCache(name="test", ttl=60)
    
    # Test list
    cache.set("list", [1, 2, 3])
    assert cache.get("list") == [1, 2, 3]
    
    # Test dict
    cache.set("dict", {"key": "value"})
    assert cache.get("dict") == {"key": "value"}
    
    # Test None value
    cache.set("none", None)
    # Note: None is a valid cached value, different from cache miss
    # Our implementation returns None for both, which is acceptable for this use case
