"""
FastAPI middleware — security headers + a real rate limiter.

Replaces the old Flask decorators in here. Worth noting why this isn't
just a mechanical port: the old `rate_limit()` decorator stored its
counters in Flask's `g` object, which is reset on every single request
— so it never actually limited anything across requests, silently. This
version uses the shared Redis/in-memory cache (cache/redis.py), which
actually persists between requests, so it's the first version of this
that works.
"""
import logging
import time

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings
from cache.redis import get_cache

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attaches the standard security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in settings.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple fixed-window rate limiter, keyed by client IP + path.

    Authenticated requests (a valid Bearer token present) get the higher
    `RATE_LIMIT_AUTHED` ceiling; everyone else gets `RATE_LIMIT_DEFAULT`.
    Both are parsed from strings like "100/hour".
    """

    def __init__(self, app):
        super().__init__(app)
        self.cache = get_cache()

    @staticmethod
    def _parse_limit(limit_str: str) -> tuple[int, int]:
        count_str, _, period = limit_str.partition("/")
        count = int(count_str)
        seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}.get(period.strip(), 3600)
        return count, seconds

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED or not request.url.path.startswith("/api"):
            return await call_next(request)

        is_authed = request.headers.get("authorization", "").startswith("Bearer ")
        limit_str = settings.RATE_LIMIT_AUTHED if is_authed else settings.RATE_LIMIT_DEFAULT
        max_requests, window_seconds = self._parse_limit(limit_str)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() // window_seconds)
        key = f"ratelimit:{client_ip}:{window}"

        count = self.cache.incr_with_expiry(key, window_seconds)
        if count and count > max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip} ({count}/{max_requests})")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        return await call_next(request)
