import uuid
import io
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from backend.app.services.report_service import report_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.post("/api/v1/reports/export", tags=["reports"])
async def export_report(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        kind, payload, mimetype, filename = report_service.export(data)
        if kind in ("csv", "pdf"):
            payload_bytes = payload if isinstance(payload, bytes) else payload.encode()
            return StreamingResponse(io.BytesIO(payload_bytes), media_type=mimetype, headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Request-ID": getattr(request.state, "request_id", "")})
        else:
            return {"data": payload}
    except ValueError as e:
        return _error("VALIDATION_ERROR", str(e), 400, request)
    except Exception as e:
        logger.exception("export failed")
        return _error("EXPORT_FAILED", str(e), 500, request)
