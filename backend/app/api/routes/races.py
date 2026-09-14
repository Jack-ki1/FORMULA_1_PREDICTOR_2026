import time
import uuid
import logging
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from backend.app.services.race_service import race_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.get("/api/v1/races", tags=["races"])
async def list_races(request: Request, response: Response):
    start = time.time()
    try:
        data = race_service.list_races()
        response.headers["Cache-Control"] = "public, max-age=300"
        logger.info(f"list_races latency=%.3f rid=%s", time.time() - start, request.state.request_id)
        return JSONResponse(content=data, headers=dict(response.headers))
    except Exception as e:
        logger.exception("list_races failed")
        return _error("RACES_FAILED", "Failed to list races", 500, request, {"exception": str(e)})

@router.get("/api/v1/races/{race_id}/result", tags=["races"])
@router.get("/api/v1/race-result/{race_id}", tags=["races"])
async def race_result(race_id: str, request: Request):
    try:
        data = race_service.get_race_result(race_id)
        return data
    except LookupError as e:
        return _error("RACE_NOT_FOUND", str(e), 404, request)
    except ValueError as e:
        return _error("RACE_NOT_COMPLETED", str(e), 404, request)
    except Exception as e:
        return _error("RACE_RESULT_FAILED", str(e), 500, request)
