import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.constructor_service import constructor_service

router = APIRouter()

def _error(code, msg, status, request: Request):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "request_id": rid}}, status_code=status)

@router.get("/api/v1/constructors/teams", tags=["constructors"])
async def teams(request: Request):
    try:
        data = constructor_service.get_teams()
        return data
    except Exception as e:
        return _error("CONSTRUCTORS_FAILED", str(e), 500, request)

@router.get("/api/v1/constructors/power-rankings", tags=["constructors"])
async def rankings(request: Request):
    try:
        data = constructor_service.get_power_rankings()
        return data
    except Exception as e:
        return _error("CONSTRUCTORS_FAILED", str(e), 500, request)
