"""
Query cache manager for Voice2Note.

Implements a two-level caching strategy:
1. In-memory LRU cache for frequently accessed queries
2. Redis cache for distributed caching across workers

Usage:
    cache = QueryCache()
    
    # With decorator
    @cache.cached(timeout=300)
    def get_user_notes(user_id):
        ...
        
    # Or manually
    cache_key = cache.make_key("notes", user_id)
    result = cache.get(cache_key)
    if result is None:
        result = execute_query()
        cache.set(cache_key, result)
"""

import hashlib
import json
from functools import wraps
from typing import Any, Optional
import redis
from cachetools import TTLCache
import logging
import datetime

logger = logging.getLogger(__name__)


class QueryCache:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        memory_maxsize: int = 100,
        memory_ttl: int = 60,
    ):
        """Initialize cache with fallback to memory-only if Redis is unavailable."""
        # Setup Redis connection
        self.redis = None
        try:
            self.redis = redis.from_url(redis_url)
            self.redis.ping()  # Test connection
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to memory-only cache: {e}")

        # Setup in-memory TTL cache
        self.memory_cache = TTLCache(maxsize=memory_maxsize, ttl=memory_ttl)
        self.default_timeout = 300

    def make_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, using memory-only if Redis is unavailable."""
        # Try memory cache first
        try:
            value = self.memory_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit (memory): {key}")
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Error accessing memory cache: {e}")

        # Try Redis only if available
        if self.redis:
            try:
                value = self.redis.get(key)
                if value is not None:
                    self.memory_cache[key] = value
                    logger.debug(f"Cache hit (redis): {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Error accessing Redis cache: {e}")

        return None

    def _serialize(self, obj):
        """Custom JSON serializer that handles datetime objects."""
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache(s)."""
        timeout = timeout or self.default_timeout
        try:
            serialized = json.dumps(value, default=self._serialize)
        except Exception as e:
            logger.error(f"Error serializing cache value: {e}")
            return False

        success = True

        # Always try memory cache
        try:
            self.memory_cache[key] = serialized
        except Exception as e:
            logger.warning(f"Error setting memory cache: {e}")
            success = False

        # Try Redis only if available
        if self.redis:
            try:
                self.redis.setex(key, timeout, serialized)
            except Exception as e:
                logger.warning(f"Error setting Redis cache: {e}")
                success = False

        return success

    def delete(self, key: str) -> bool:
        """
        Delete key from both caches.

        Args:
            key: Cache key to delete

        Returns:
            True if deletion was successful
        """
        success = True

        # Delete from memory
        try:
            del self.memory_cache[key]
        except Exception as e:
            logger.warning(f"Error deleting from memory cache: {e}")
            success = False

        # Delete from Redis
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Error deleting from Redis cache: {e}")
            success = False

        return success

    def cached(self, timeout: Optional[int] = None):
        """
        Decorator for caching function results.

        Args:
            timeout: Cache timeout in seconds

        Returns:
            Decorated function
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key = self.make_key(func.__name__, *args, **kwargs)

                # Try to get from cache
                result = self.get(key)
                if result is not None:
                    return result

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(key, result, timeout)
                return result

            return wrapper

        return decorator

    def clear(self, pattern: str = "*") -> bool:
        """
        Clear all cached items matching pattern.

        Args:
            pattern: Redis key pattern to match

        Returns:
            True if clearing was successful
        """
        success = True

        # Clear memory cache
        try:
            self.memory_cache.clear()
        except Exception as e:
            logger.warning(f"Error clearing memory cache: {e}")
            success = False

        # Clear Redis cache
        try:
            for key in self.redis.scan_iter(pattern):
                self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {e}")
            success = False

        return success
