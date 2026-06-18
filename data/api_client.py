"""
Base API Client — Unified HTTP client with retry, caching, and rate limiting.

Provides a shared foundation for all F1 API integrations:
  - Automatic retry with exponential backoff
  - Local file-based response caching with configurable TTL
  - Token-bucket rate limiter (per-API)
  - Structured error handling and logging
  - JSON/CSV response parsing
"""

import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from urllib.parse import urlencode, urljoin

logger = logging.getLogger(__name__)

# Use urllib (stdlib) to avoid adding requests as a hard dependency
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class RateLimiter:
    """
    Token-bucket rate limiter.
    
    Ensures we don't exceed the API's rate limits by tracking
    request timestamps and enforcing minimum intervals.
    """

    def __init__(self, requests_per_second: float = 3, requests_per_minute: float = 30):
        self.rps = requests_per_second
        self.rpm = requests_per_minute
        self.min_interval_s = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.min_interval_m = 60.0 / requests_per_minute if requests_per_minute > 0 else 0
        self._last_request_time = 0.0
        self._minute_requests: List[float] = []

    def wait_if_needed(self):
        """Block until it's safe to make the next request."""
        now = time.time()

        # Enforce per-second interval
        elapsed_since_last = now - self._last_request_time
        if elapsed_since_last < self.min_interval_s:
            sleep_time = self.min_interval_s - elapsed_since_last
            logger.debug(f"Rate limiter: sleeping {sleep_time:.3f}s (per-second limit)")
            time.sleep(sleep_time)

        # Enforce per-minute window
        self._minute_requests = [t for t in self._minute_requests if now - t < 60.0]
        if len(self._minute_requests) >= self.rpm:
            oldest = self._minute_requests[0]
            sleep_time = 60.0 - (now - oldest) + 0.1
            if sleep_time > 0:
                logger.debug(f"Rate limiter: sleeping {sleep_time:.3f}s (per-minute limit)")
                time.sleep(sleep_time)

        now = time.time()
        self._last_request_time = now
        self._minute_requests.append(now)


class APICache:
    """
    File-based response cache with TTL support.
    
    Caches API responses as JSON files in a local directory.
    Each cache key maps to a file; expired files are skipped.
    """

    def __init__(self, cache_dir: Path, enabled: bool = True):
        self.cache_dir = cache_dir
        self.enabled = enabled
        if enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Convert a cache key to a file path."""
        safe_name = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def get(self, key: str, ttl_seconds: int = 300) -> Optional[Any]:
        """Retrieve cached response if it exists and hasn't expired."""
        if not self.enabled:
            return None

        path = self._key_to_path(key)
        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as f:
                entry = json.load(f)

            cached_at = datetime.fromisoformat(entry["cached_at"])
            age = (datetime.now() - cached_at).total_seconds()

            if age > ttl_seconds:
                logger.debug(f"Cache expired for key {key} (age: {age:.0f}s > TTL: {ttl_seconds}s)")
                return None

            logger.debug(f"Cache hit for key {key} (age: {age:.0f}s)")
            return entry["data"]

        except Exception as e:
            logger.debug(f"Cache read error for {key}: {e}")
            return None

    def set(self, key: str, data: Any):
        """Store a response in the cache."""
        if not self.enabled:
            return

        path = self._key_to_path(key)
        try:
            entry = {
                "cached_at": datetime.now().isoformat(),
                "key": key,
                "data": data,
            }
            with path.open("w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, default=str)
            logger.debug(f"Cached response for key {key}")
        except Exception as e:
            logger.debug(f"Cache write error for {key}: {e}")

    def clear(self, older_than_seconds: Optional[int] = None):
        """Clear cache entries. If older_than_seconds is set, only clear old entries."""
        if not self.enabled:
            return

        cleared = 0
        for path in self.cache_dir.glob("*.json"):
            if older_than_seconds is not None:
                try:
                    with path.open("r", encoding="utf-8") as f:
                        entry = json.load(f)
                    cached_at = datetime.fromisoformat(entry["cached_at"])
                    age = (datetime.now() - cached_at).total_seconds()
                    if age <= older_than_seconds:
                        continue
                except Exception:
                    pass
            path.unlink(missing_ok=True)
            cleared += 1

        logger.info(f"Cleared {cleared} cache entries")


class BaseAPIClient:
    """
    Base HTTP client for F1 APIs.
    
    Features:
      - Configurable base URL and timeout
      - Per-client rate limiter
      - File-based response caching
      - Automatic retry with exponential backoff
      - Structured error handling
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        rate_limit_rps: float = 3,
        rate_limit_rpm: float = 30,
        timeout: int = 15,
        cache_dir: Optional[Path] = None,
        cache_enabled: bool = True,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.default_headers = default_headers or {}

        self.rate_limiter = RateLimiter(rate_limit_rps, rate_limit_rpm)
        self.cache = APICache(
            cache_dir or Path(__file__).resolve().parents[1] / "cache" / "api_responses",
            enabled=cache_enabled,
        )

        # Stats
        self._request_count = 0
        self._cache_hits = 0
        self._errors = 0

    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL from endpoint and query parameters."""
        url = f"{self.base_url}{endpoint}"
        if params:
            # Filter out None values
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url += "?" + urlencode(clean_params)
        return url

    def _cache_key(self, url: str) -> str:
        """Generate a cache key from a URL."""
        return f"{self.name}:{url}"

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 300,
        use_cache: bool = True,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Any]:
        """
        Make a GET request with caching and rate limiting.
        
        Args:
            endpoint: API endpoint path (appended to base_url)
            params: Query parameters
            ttl_seconds: Cache time-to-live in seconds
            use_cache: Whether to use caching for this request
            headers: Additional HTTP headers
        
        Returns:
            Parsed JSON response, or None on failure
        """
        url = self._build_url(endpoint, params)
        cache_key = self._cache_key(url)

        # Check cache first
        if use_cache:
            cached = self.cache.get(cache_key, ttl_seconds=ttl_seconds)
            if cached is not None:
                self._cache_hits += 1
                return cached

        # Make the request with retry
        merged_headers = {**self.default_headers, **(headers or {})}
        last_error = None

        for attempt in range(self.max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                self._request_count += 1

                request = Request(url, headers=merged_headers, method="GET")
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    data = json.loads(raw)

                # Cache the response
                if use_cache:
                    self.cache.set(cache_key, data)

                logger.debug(f"[{self.name}] GET {endpoint} → 200 OK ({len(raw)} bytes)")
                return data

            except HTTPError as e:
                last_error = e
                status = e.code
                logger.warning(f"[{self.name}] GET {endpoint} → HTTP {status} (attempt {attempt + 1}/{self.max_retries})")

                # Don't retry client errors (4xx) except 429 (rate limit)
                if 400 <= status < 500 and status != 429:
                    self._errors += 1
                    return None

                # Wait before retrying (exponential backoff)
                if attempt < self.max_retries - 1:
                    wait = self.retry_backoff ** attempt
                    logger.debug(f"[{self.name}] Retrying in {wait:.1f}s...")
                    time.sleep(wait)

            except URLError as e:
                last_error = e
                logger.warning(f"[{self.name}] GET {endpoint} → Connection error: {e} (attempt {attempt + 1}/{self.max_retries})")

                if attempt < self.max_retries - 1:
                    wait = self.retry_backoff ** attempt
                    time.sleep(wait)

            except json.JSONDecodeError as e:
                logger.error(f"[{self.name}] GET {endpoint} → JSON parse error: {e}")
                self._errors += 1
                return None

            except Exception as e:
                last_error = e
                logger.error(f"[{self.name}] GET {endpoint} → Unexpected error: {e}")
                self._errors += 1
                return None

        logger.error(f"[{self.name}] GET {endpoint} → All {self.max_retries} retries exhausted. Last error: {last_error}")
        self._errors += 1
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Return client usage statistics."""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "total_requests": self._request_count,
            "cache_hits": self._cache_hits,
            "errors": self._errors,
            "cache_hit_rate": f"{self._cache_hits / max(1, self._request_count + self._cache_hits) * 100:.1f}%",
        }

    def clear_cache(self):
        """Clear all cached responses for this client."""
        self.cache.clear()
        logger.info(f"[{self.name}] Cache cleared")


# ── EXPORT ────────────────────────────────────────────────────────────────────

__all__ = [
    "RateLimiter",
    "APICache",
    "BaseAPIClient",
]
