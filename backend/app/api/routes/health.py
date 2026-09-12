from flask import Blueprint, jsonify
from datetime import datetime
health_bp = Blueprint("health", __name__)
@health_bp.route("/api/v1/health")
def health_v1(): return jsonify({"status":"healthy","version":"1.0.0","timestamp": datetime.utcnow().isoformat()})
