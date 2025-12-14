"""
Simple in-memory cache with TTL support for frequently accessed data.

This cache is designed for read-heavy, write-rarely data like profiles and models.
It's safe for single-process deployments (typical for this local-first app).
"""
import time
from typing import Any, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Thread-safe in-memory cache with TTL (time-to-live) expiration."""
    
    def __init__(self, name: str, ttl: int = 60):
        """
        Initialize cache.
        
        Args:
            name: Cache name for logging
            ttl: Time-to-live in seconds (default: 60)
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl
        self._lock = Lock()
        self._name = name
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    self._hits += 1
                    logger.debug(f"Cache hit: {self._name}[{key}]")
                    return data
                # Expired - remove it
                del self._cache[key]
                logger.debug(f"Cache expired: {self._name}[{key}]")
            
            self._misses += 1
            logger.debug(f"Cache miss: {self._name}[{key}]")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = (value, time.time())
            logger.debug(f"Cache set: {self._name}[{key}]")
    
    def invalidate(self, key: str) -> None:
        """
        Remove specific key from cache.
        
        Args:
            key: Cache key to remove
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidated: {self._name}[{key}]")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Remove all keys matching pattern (simple prefix match).
        
        Args:
            pattern: Key prefix to match
            
        Returns:
            Number of keys removed
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_remove:
                del self._cache[key]
            
            if keys_to_remove:
                logger.debug(f"Cache invalidated {len(keys_to_remove)} keys matching: {self._name}[{pattern}*]")
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"Cache cleared: {self._name} ({count} keys)")
    
    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, size, and hit rate
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "name": self._name,
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate": f"{hit_rate:.1f}%",
                "ttl": self._ttl,
            }


# Global cache instances
# Profiles change rarely but are accessed on every stream request
profile_cache = SimpleCache(name="profiles", ttl=60)

# Models change only on sync operations, can have longer TTL
model_cache = SimpleCache(name="models", ttl=300)
