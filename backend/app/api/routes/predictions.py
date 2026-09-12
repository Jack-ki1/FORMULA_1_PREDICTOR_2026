from flask import Blueprint, request, jsonify, g
import time, uuid, logging
from backend.app.services.prediction_service import prediction_service
logger = logging.getLogger(__name__)
predictions_bp = Blueprint("predictions_v1", __name__)

def _error(code,msg,status,details=None):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status

@predictions_bp.before_request
def _rid(): g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

def _handle_predict():
    data = request.get_json(silent=True)
    if not data: return _error("INVALID_JSON","Request body must be JSON",400)
    if not data.get("race_id"): return _error("MISSING_RACE_ID","race_id is required",400)
    start=time.time()
    try:
        result = prediction_service.generate(data)
        # prediction latency metric
        latency=time.time()-start
        logger.info("predict race=%s latency=%.3f rid=%s", data.get("race_id"), latency, g.request_id)
        resp=jsonify(result)
        resp.headers["X-Request-ID"]=g.request_id
        resp.headers["X-Prediction-Latency"]=f"{latency:.3f}"
        return resp, 200
    except ValueError as e:
        return _error("VALIDATION_ERROR", str(e), 400)
    except Exception as e:
        logger.exception("prediction failed")
        return _error("PREDICTION_FAILED","Prediction generation failed",500,{"exception": str(e)})

@predictions_bp.route("/api/v1/predictions", methods=["POST"])
@predictions_bp.route("/api/v1/predict", methods=["POST"])
@predictions_bp.route("/api/v1/predict-session", methods=["POST"])
def predict(): return _handle_predict()


