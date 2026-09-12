from flask import Blueprint, request, jsonify, g
import uuid
from backend.app.services.ai_service import ai_service
ai_bp=Blueprint("ai_v1", __name__)
def _error(code,msg,status):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"request_id": rid}}), status
@ai_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@ai_bp.route("/api/v1/ai/chat", methods=["POST"])
def chat():
    data=request.get_json(silent=True) or {}
    if not data.get("message"): return _error("MISSING_MESSAGE","message is required",400)
    res=ai_service.chat(data.get("message"), data.get("model","gemini-2.0-flash-exp"), data.get("api_key","") or data.get("apiKey",""), float(data.get("temperature",0.7)))
    resp=jsonify(res); resp.headers["X-Request-ID"]=g.request_id; return resp
