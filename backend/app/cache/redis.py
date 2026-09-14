import logging
import json
from typing import Any, Optional, Dict
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class CacheError(Exception):
    """Custom exception for cache errors."""
    pass


class DictCache:
    """In-memory dict-based cache fallback when Redis is unavailable."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        logger.info("Using in-memory DictCache (Redis unavailable)")

    def get(self, key: str) -> Optional[Any]:
        import time
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        import time
        ttl = ttl or settings.CACHE_TTL_SECONDS
        expires_at = time.time() + ttl if ttl else None
        if isinstance(value, (dict, list, bool, int, float)):
            value = json.dumps(value)
        self._store[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear(self) -> bool:
        self._store.clear()
        return True


class RedisCache:
    """Redis-based caching implementation. Exposes .redis_client alias for rate limiting."""

    def __init__(self):
        self.client = None
        self.redis_client = None  # alias used by rate_limit_check_fastapi
        self._connect()
        self.redis_client = self.client

    def _connect(self):
        """Connect to Redis server."""
        import socket
        try:
            # Quick TCP connectivity check before attempting Redis connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((settings.REDIS_HOST, settings.REDIS_PORT))
            sock.close()
            if result != 0:
                raise CacheError(f"Redis host {settings.REDIS_HOST}:{settings.REDIS_PORT} unreachable")
            
            import redis
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3
            )
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis cache")
        except CacheError:
            raise
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory cache.")
            self.client = None
            raise CacheError(f"Redis connection failed: {str(e)}") from e

    def get(self, key: str) -> Optional[Any]:
        """Get value from backend.app.cache."""
        try:
            if not self.client:
                return None

            value = self.client.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache."""
        try:
            if not self.client:
                return False

            if ttl is None:
                ttl = settings.CACHE_TTL_SECONDS

            # Convert value to string if needed
            if isinstance(value, (dict, list, bool, int, float)):
                value = json.dumps(value)

            result = self.client.setex(key, ttl, value)
            if result:
                logger.debug(f"Cached value for key: {key} (ttl: {ttl}s)")
            return result
        except Exception as e:
            logger.error(f"Error setting in cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from backend.app.cache."""
        try:
            if not self.client:
                return False

            result = self.client.delete(key)
            if result:
                logger.debug(f"Deleted cache key: {key}")
            return result
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            if not self.client:
                return False

            result = self.client.flushdb()
            logger.info("Cleared all cache entries")
            return result
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global cache instance
_cache_instance = None


def get_cache():
    """Get singleton cache instance. Falls back to in-memory cache if Redis is unavailable.
    In production with REDIS_REQUIRED=true, raises instead of silent fallback.
    """
    global _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = RedisCache()
        except CacheError as e:
            if getattr(settings, 'REDIS_REQUIRED', False):
                logger.error(f"REDIS_REQUIRED=true but Redis unavailable: {e}")
                raise
            if not getattr(settings, 'ENABLE_IN_MEMORY_FALLBACK', True):
                logger.error("In-memory fallback disabled and Redis unavailable")
                raise CacheError("Cache unavailable and fallback disabled") from e
            _cache_instance = DictCache()
    return _cache_instance

def reset_cache():
    """Reset singleton — for tests."""
    global _cache_instance
    _cache_instance = None
