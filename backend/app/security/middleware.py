"""Middleware: request_id, security headers, rate limiting stub, observability."""
import time, uuid, logging
from flask import request, g

logger = logging.getLogger(__name__)

def attach_request_id():
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = rid

def add_security_headers(response):
    from config.settings import settings
    for k,v in settings.SECURITY_HEADERS.items():
        response.headers[k]=v
    # request id echo
    if hasattr(g, "request_id"):
        response.headers["X-Request-ID"]=g.request_id
    response.headers["X-Content-Type-Options"]="nosniff"
    return response

# simple in-memory rate limiter stub (100/hour default)
_rate_store={}
def rate_limit_check():
    # Only if enabled
    from config.settings import settings
    if not settings.RATE_LIMIT_ENABLED:
        return None
    ip = request.remote_addr or "unknown"
    key = f"rl:{ip}:{request.path}"
    now=time.time()
    window=3600
    # clean old
    if key in _rate_store:
        timestamps=[t for t in _rate_store[key] if now-t < window]
        _rate_store[key]=timestamps
    else:
        _rate_store[key]=[]
    _rate_store[key].append(now)
    if len(_rate_store[key]) > 100:
        from flask import jsonify
        return jsonify({"error":{"code":"RATE_LIMITED","message":"Rate limit exceeded","request_id": getattr(g,"request_id","")}}), 429
    return None
