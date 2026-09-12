from flask import Blueprint, request, jsonify, g, send_file
import uuid, io, logging
from backend.app.services.report_service import report_service
logger=logging.getLogger(__name__)
reports_bp=Blueprint("reports_v1", __name__)
def _error(code,msg,status,details=None):
    rid=getattr(g,"request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return jsonify({"error":{"code":code,"message":msg,"details":details or {},"request_id": rid}}), status
@reports_bp.before_request
def _rid(): g.request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4())
@reports_bp.route("/api/v1/reports/export", methods=["POST"])
def export():
    data=request.get_json(silent=True) or {}
    try:
        kind, payload, mimetype, filename = report_service.export(data)
        if kind in ("csv","pdf"):
            return send_file(io.BytesIO(payload if isinstance(payload, bytes) else payload.encode()), mimetype=mimetype, as_attachment=True, download_name=filename, headers={"X-Request-ID": g.request_id})
        else:
            resp=jsonify({"data": payload}); resp.headers["X-Request-ID"]=g.request_id; return resp
    except ValueError as e: return _error("VALIDATION_ERROR", str(e), 400)
    except Exception as e:
        logger.exception("export failed"); return _error("EXPORT_FAILED", str(e), 500)
