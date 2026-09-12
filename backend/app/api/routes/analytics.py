from flask import Blueprint, jsonify, request, g
import uuid, logging
from backend.app.services.analytics_service import analytics_service
logger=logging.getLogger(__name__)
analytics_bp=Blueprint("analytics_v1", __name__)
def _error(code,msg,status,details=None):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status
@analytics_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@analytics_bp.route("/api/v1/analytics/accuracy")
def accuracy():
    try: data=analytics_service.get_accuracy(); resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("ANALYTICS_FAILED", str(e), 500)
@analytics_bp.route("/api/v1/analytics/feature-weights")
def get_weights():
    try: data=analytics_service.get_weights(); resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("WEIGHTS_FAILED", str(e), 500)
@analytics_bp.route("/api/v1/analytics/feature-weights", methods=["POST"])
def post_weights():
    data=request.get_json(silent=True) or {}
    try:
        res=analytics_service.update_weights(data); resp=jsonify(res); resp.headers["X-Request-ID"]=g.request_id; return resp
    except ValueError as e: return _error("VALIDATION_ERROR", str(e), 400)
    except Exception as e: return _error("WEIGHTS_FAILED", str(e), 500)
@analytics_bp.route("/api/v1/analytics/targets")
def targets():
    try: data=analytics_service.get_targets(); resp=jsonify(data); resp.headers["X-Request-ID"]=g.request_id; return resp
    except Exception as e: return _error("TARGETS_FAILED", str(e), 500)
