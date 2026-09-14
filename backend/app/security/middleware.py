"""Middleware: request_id, security headers, rate limiting — Flask compat + FastAPI."""
import time
import uuid
import logging
from fastapi import Request
from fastapi.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Flask compat (kept for shim, not used after FastAPI migration)
try:
    from flask import request as flask_request, g as flask_g  # type: ignore
except Exception:
    flask_request = None
    flask_g = None

def add_security_headers(response):
    """Flask compat — adds headers to Flask response."""
    from backend.app.config.settings import settings
    for k, v in settings.SECURITY_HEADERS.items():
        response.headers[k] = v
    if flask_g and hasattr(flask_g, "request_id"):
        response.headers["X-Request-ID"] = flask_g.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

_rate_store: dict = {}

def rate_limit_check():
    """Flask compat stub."""
    if flask_request is None:
        return None
    from backend.app.config.settings import settings
    if not settings.RATE_LIMIT_ENABLED:
        return None
    ip = getattr(flask_request, "remote_addr", None) or "unknown"
    key = f"rl:{ip}:{getattr(flask_request, 'path', '/')}"
    now = time.time()
    if key in _rate_store:
        _rate_store[key] = [t for t in _rate_store[key] if now - t < 3600]
    else:
        _rate_store[key] = []
    _rate_store[key].append(now)
    if len(_rate_store[key]) > 100:
        return JSONResponse({"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "request_id": getattr(flask_g, "request_id", "")}}, status_code=429)  # type: ignore
    return None

# FastAPI native

def add_security_headers_fastapi(response: Response, request: Request):
    from backend.app.config.settings import settings
    for k, v in settings.SECURITY_HEADERS.items():
        response.headers[k] = v
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

def _parse_rate_limit(limit_str: str) -> tuple[int, int]:
    """Parse '100/hour' -> (100, 3600). Supports /hour, /minute, /second."""
    try:
        count_s, window_s = limit_str.split('/')
        count = int(count_s)
        window = {'second': 1, 'minute': 60, 'hour': 3600, 'day': 86400}.get(window_s.strip().lower(), 3600)
        return count, window
    except Exception:
        return 100, 3600

def _get_route_limit(path: str) -> str:
    from backend.app.config.settings import settings
    if path.startswith('/api/v1/predictions'):
        return settings.RATE_LIMIT_PREDICTIONS
    if path.startswith('/api/v1/ai/'):
        return settings.RATE_LIMIT_AI
    if path.startswith('/api/v1/live'):
        return settings.RATE_LIMIT_LIVE
    if path.startswith('/api/v1/reports'):
        return settings.RATE_LIMIT_EXPORTS
    return settings.RATE_LIMIT_DEFAULT

def rate_limit_check_fastapi(request: Request):
    from backend.app.config.settings import settings
    if not settings.RATE_LIMIT_ENABLED:
        return None
    ip = request.client.host if request.client else "unknown"
    # per-route limit
    limit_str = _get_route_limit(request.url.path)
    limit, window = _parse_rate_limit(limit_str)
    key = f"rl:{ip}:{request.url.path}"

    # Try Redis-backed distributed limit first
    try:
        from backend.app.cache.redis import get_cache
        cache = get_cache()
        # RedisCache has underlying client; use incr+expire if available
        if hasattr(cache, 'redis_client') and getattr(cache, 'redis_client', None) is not None:
            r = cache.redis_client  # type: ignore
            count = r.incr(key)
            if count == 1:
                r.expire(key, window)
            ttl = r.ttl(key)
            if count > limit:
                rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
                resp = JSONResponse({"error": {"code": "RATE_LIMITED", "message": f"Rate limit {limit_str} exceeded", "request_id": rid}}, status_code=429)
                resp.headers["Retry-After"] = str(ttl if ttl > 0 else window)
                resp.headers["X-RateLimit-Limit"] = str(limit)
                resp.headers["X-RateLimit-Remaining"] = "0"
                return resp
            return None
    except Exception:
        pass

    # Fallback: process-local (dev) — still honors per-route limits
    now = time.time()
    if key in _rate_store:
        _rate_store[key] = [t for t in _rate_store[key] if now - t < window]
    else:
        _rate_store[key] = []
    _rate_store[key].append(now)
    if len(_rate_store[key]) > limit:
        rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return JSONResponse({"error": {"code": "RATE_LIMITED", "message": f"Rate limit {limit_str} exceeded", "request_id": rid}}, status_code=429)
    return None
