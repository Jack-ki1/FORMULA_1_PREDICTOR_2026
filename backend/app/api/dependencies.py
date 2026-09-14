"""Shared dependencies: request_id, auth optional, cache key helpers."""
import uuid
import hashlib
import json
from fastapi import Request

def get_request_id(request: Request) -> str:
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid
    return rid

def grid_hash(grid):
    if not grid:
        return "nogrid"
    return hashlib.md5(json.dumps(grid, sort_keys=True).encode()).hexdigest()[:8]
