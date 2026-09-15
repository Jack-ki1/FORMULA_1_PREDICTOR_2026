import uuid
import re
import io
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from backend.app.services.report_service import report_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _sanitize_filename(name: str) -> str:
    # Tier 6: sanitize filenames — prevent path traversal and injection
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', name or "report")
    if not name or name.startswith("."):
        name = "report" + name
    # enforce safe extension
    if "." not in name:
        name += ".pdf"
    # max length
    return name[:80]

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

@router.post("/api/v1/reports/export", tags=["reports"])
async def export_report(request: Request):
    # Tier 6: body size limit for reports (PDF gen is expensive)
    raw = await request.body()
    if len(raw) > 128 * 1024:
        return _error("PAYLOAD_TOO_LARGE", "Report request too large (max 128KB)", 413, request)
    try:
        import json as _json
        data = _json.loads(raw) if raw else {}
    except Exception:
        data = {}
    try:
        kind, payload, mimetype, filename = report_service.export(data)
        filename = _sanitize_filename(filename)
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
