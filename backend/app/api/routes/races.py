from flask import Blueprint, jsonify, request, g
import time, uuid, logging
from backend.app.services.race_service import race_service
logger = logging.getLogger(__name__)
races_bp = Blueprint("races", __name__)

def _error(code, msg, status, details=None):
    rid = getattr(g, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status

@races_bp.before_request
def _rid():
    g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

@races_bp.route("/api/v1/races")
def list_races():
    start=time.time()
    try:
        data = race_service.list_races()
        resp=jsonify(data)
        resp.headers["X-Request-ID"]=g.request_id
        resp.headers["Cache-Control"]="public, max-age=300"
        logger.info("list_races latency=%.3f rid=%s", time.time()-start, g.request_id)
        return resp
    except Exception as e:
        logger.exception("list_races failed")
        return _error("RACES_FAILED","Failed to list races",500,{"exception":str(e)})

@races_bp.route("/api/v1/races/<race_id>/result")
@races_bp.route("/api/v1/race-result/<race_id>")
def race_result(race_id):
    try:
        data=race_service.get_race_result(race_id)
        return jsonify(data)
    except LookupError as e:
        return _error("RACE_NOT_FOUND", str(e), 404)
    except ValueError as e:
        return _error("RACE_NOT_COMPLETED", str(e), 404)
    except Exception as e:
        return _error("RACE_RESULT_FAILED", str(e), 500)
