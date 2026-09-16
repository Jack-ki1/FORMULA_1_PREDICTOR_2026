import uuid
import logging
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from backend.app.services.standings_service import standings_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.get("/api/v1/standings/drivers", tags=["standings"])
async def driver_standings(request: Request, response: Response):
    try:
        data = standings_service.get_driver_standings()
        return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=60"})
    except Exception as e:
        logger.exception("driver_standings failed")
        return _error("STANDINGS_FAILED", str(e), 500, request)

@router.get("/api/v1/standings/constructors", tags=["standings"])
async def constructor_standings(request: Request, response: Response):
    try:
        data = standings_service.get_constructor_standings()
        return JSONResponse(content=data, headers={"Cache-Control": "public, max-age=60"})
    except Exception as e:
        logger.exception("constructor_standings failed")
        return _error("STANDINGS_FAILED", str(e), 500, request)

@router.get("/api/v1/standings/championship-projection", tags=["standings"])
async def championship_projection(request: Request, simulations: int = 2000):
    # P(driver wins the title) from simulating every remaining round.
    # Reuses the production Monte Carlo engine across the rest of the calendar
    # rather than one race (modify.md section 5).
    try:
        from backend.app.services.projection_service import project_championship
        return project_championship(simulations=simulations)
    except Exception as e:
        logger.exception("championship projection failed")
        return _error("PROJECTION_FAILED", str(e), 500, request)
