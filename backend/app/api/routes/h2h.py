from flask import Blueprint, jsonify, request, g
import uuid, logging
from backend.app.services.h2h_service import h2h_service
logger=logging.getLogger(__name__)
h2h_bp=Blueprint("h2h_v1", __name__)
def _error(code,msg,status,details=None):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status
@h2h_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@h2h_bp.route("/api/v1/h2h/drivers")
def drivers():
    try:
        data=h2h_service.list_drivers(); resp=jsonify(data); resp.headers["Cache-Control"]="public, max-age=3600"; resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("H2H_FAILED", str(e), 500)
@h2h_bp.route("/api/v1/h2h/compare", methods=["POST"])
def compare():
    data=request.get_json(silent=True) or {}
    a=data.get("driver_a") or data.get("driverA") or ""
    b=data.get("driver_b") or data.get("driverB") or ""
    try:
        res=h2h_service.compare(a,b); resp=jsonify(res); resp.headers["X-Request-ID"]=g.request_id; return resp
    except ValueError as e: return _error("VALIDATION_ERROR", str(e), 400)
    except LookupError as e: return _error("DRIVER_NOT_FOUND", str(e), 404)
    except Exception as e:
        logger.exception("h2h compare failed"); return _error("H2H_FAILED", str(e), 500)
