from flask import Blueprint, jsonify, request, g
import uuid, logging
from backend.app.services.standings_service import standings_service
logger=logging.getLogger(__name__)
standings_bp=Blueprint("standings_v1", __name__)
def _error(code,msg,status,details=None):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status
@standings_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@standings_bp.route("/api/v1/standings/drivers")
def driver_standings():
    try:
        data=standings_service.get_driver_standings()
        resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; resp.headers["Cache-Control"]="public, max-age=60"; return resp
    except Exception as e:
        logger.exception("driver_standings failed"); return _error("STANDINGS_FAILED", str(e), 500)
@standings_bp.route("/api/v1/standings/constructors")
def constructor_standings():
    try:
        data=standings_service.get_constructor_standings()
        resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; resp.headers["Cache-Control"]="public, max-age=60"; return resp
    except Exception as e:
        logger.exception("constructor_standings failed"); return _error("STANDINGS_FAILED", str(e), 500)
