import uuid
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.h2h_service import h2h_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.get("/api/v1/h2h/drivers", tags=["h2h"])
async def drivers(request: Request):
    try:
        data = h2h_service.list_drivers()
        return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=3600"})
    except Exception as e:
        return _error("H2H_FAILED", str(e), 500, request)

@router.post("/api/v1/h2h/compare", tags=["h2h"])
async def compare(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    a = data.get("driver_a") or data.get("driverA") or ""
    b = data.get("driver_b") or data.get("driverB") or ""
    try:
        res = h2h_service.compare(a, b)
        return res
    except ValueError as e:
        return _error("VALIDATION_ERROR", str(e), 400, request)
    except LookupError as e:
        return _error("DRIVER_NOT_FOUND", str(e), 404, request)
    except Exception as e:
        logger.exception("h2h compare failed")
        return _error("H2H_FAILED", str(e), 500, request)
