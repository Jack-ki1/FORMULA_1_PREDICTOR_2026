import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.ai_service import ai_service

router = APIRouter()

def _error(code, msg, status, request: Request):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "request_id": rid}}, status_code=status)

@router.post("/api/v1/ai/chat", tags=["ai"])
async def chat(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not data.get("message"):
        return _error("MISSING_MESSAGE", "message is required", 400, request)
    res = ai_service.chat(data.get("message"), data.get("model", "gemini-2.0-flash-exp"), data.get("api_key", "") or data.get("apiKey", ""), float(data.get("temperature", 0.7)))
    return res
