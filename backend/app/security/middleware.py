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

def rate_limit_check_fastapi(request: Request):
    from backend.app.config.settings import settings
    if not settings.RATE_LIMIT_ENABLED:
        return None
    ip = request.client.host if request.client else "unknown"
    key = f"rl:{ip}:{request.url.path}"
    now = time.time()
    if key in _rate_store:
        _rate_store[key] = [t for t in _rate_store[key] if now - t < 3600]
    else:
        _rate_store[key] = []
    _rate_store[key].append(now)
    if len(_rate_store[key]) > 100:
        rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return JSONResponse({"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "request_id": rid}}, status_code=429)
    return None
