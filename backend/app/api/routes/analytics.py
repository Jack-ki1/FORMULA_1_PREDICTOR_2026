import uuid
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.get("/api/v1/analytics/accuracy", tags=["analytics"])
async def accuracy(request: Request):
    try:
        data = analytics_service.get_accuracy()
        return data
    except Exception as e:
        return _error("ANALYTICS_FAILED", str(e), 500, request)

@router.get("/api/v1/analytics/feature-weights", tags=["analytics"])
async def get_weights(request: Request):
    try:
        data = analytics_service.get_weights()
        return data
    except Exception as e:
        return _error("WEIGHTS_FAILED", str(e), 500, request)

@router.post("/api/v1/analytics/feature-weights", tags=["analytics"])
async def post_weights(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        res = analytics_service.update_weights(data)
        return res
    except ValueError as e:
        return _error("VALIDATION_ERROR", str(e), 400, request)
    except Exception as e:
        return _error("WEIGHTS_FAILED", str(e), 500, request)

@router.get("/api/v1/analytics/targets", tags=["analytics"])
async def targets(request: Request):
    try:
        data = analytics_service.get_targets()
        return data
    except Exception as e:
        return _error("TARGETS_FAILED", str(e), 500, request)
