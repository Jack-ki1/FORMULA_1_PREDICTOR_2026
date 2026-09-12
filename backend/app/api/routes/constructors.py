from flask import Blueprint, jsonify, request, g
import uuid
from backend.app.services.constructor_service import constructor_service
constructors_bp=Blueprint("constructors_v1", __name__)
def _error(code,msg,status):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"request_id": rid}}), status
@constructors_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@constructors_bp.route("/api/v1/constructors/teams")
def teams():
    try: data=constructor_service.get_teams(); resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("CONSTRUCTORS_FAILED", str(e), 500)
@constructors_bp.route("/api/v1/constructors/power-rankings")
def rankings():
    try: data=constructor_service.get_power_rankings(); resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("CONSTRUCTORS_FAILED", str(e), 500)
