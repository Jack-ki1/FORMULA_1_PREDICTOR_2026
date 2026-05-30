"""
Web Dashboard — Flask-based interactive dashboard for F1 predictions.

Features:
- Real-time prediction visualization
- H2H driver comparison tool
- Historical accuracy tracking
- Championship simulator
- Interactive charts with Plotly
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
import os
import sys

# Add project root to Python path so we can import engine, data, etc.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
logger = logging.getLogger(__name__)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict_page():
    """Race prediction page."""
    if request.method == 'POST':
        data = request.json
        try:
            # Call prediction engine directly instead of proxying to API
            from engine.predictor import predict, PredictionRequest
            
            request_obj = PredictionRequest(
                circuit_id=data.get('circuit_id'),
                rain_probability=data.get('rain_probability'),
                n_simulations=data.get('n_simulations', 5000),
            )
            
            result = predict(request_obj)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    return render_template('predict.html')


@app.route('/h2h', methods=['POST'])
def h2h_page():
    """Head-to-head comparison page."""
    try:
        # Call prediction engine directly
        from engine.probability_model import predict_race
        
        data = request.json
        sim_result = predict_race(
            circuit_id=data.get('circuit_id'),
            rain_probability=data.get('rain_probability'),
            n_simulations=data.get('n_simulations', 10000),
        )
        
        predictions = {p["driver_id"]: p for p in sim_result["predictions"]}
        driver1 = data.get('driver1')
        driver2 = data.get('driver2')
        
        if driver1 not in predictions or driver2 not in predictions:
            return jsonify({"error": "Drivers not found"}), 400
        
        d1_pred = predictions[driver1]
        d2_pred = predictions[driver2]
        
        # Calculate H2H probabilities
        pos_dist_1 = d1_pred.get("position_distribution", [])
        pos_dist_2 = d2_pred.get("position_distribution", [])
        
        total_1 = sum(pos_dist_1) if pos_dist_1 else 1
        total_2 = sum(pos_dist_2) if pos_dist_2 else 1
        
        prob_dist_1 = [count / total_1 for count in pos_dist_1]
        prob_dist_2 = [count / total_2 for count in pos_dist_2]
        
        p_d1_ahead = 0.0
        for pos1 in range(len(prob_dist_1)):
            for pos2 in range(len(prob_dist_2)):
                if pos1 < pos2:
                    p_d1_ahead += prob_dist_1[pos1] * prob_dist_2[pos2]
        
        result = {
            "driver1": driver1,
            "driver2": driver2,
            "driver1_finishes_ahead_pct": round(p_d1_ahead * 100, 1),
            "driver2_finishes_ahead_pct": round((1 - p_d1_ahead) * 100, 1),
            "driver1_avg_position": d1_pred.get("expected_position_float", d1_pred.get("predicted_position", 99)),
            "driver2_avg_position": d2_pred.get("expected_position_float", d2_pred.get("predicted_position", 99)),
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"H2H error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/constructors/<circuit_id>')
def constructors_page(circuit_id):
    """Constructor predictions page."""
    try:
        from engine.probability_model import predict_race
        
        sim_result = predict_race(
            circuit_id=circuit_id,
            rain_probability=None,
            n_simulations=5000,
        )
        
        # Aggregate by constructor
        constructor_results = {}
        for pred in sim_result["predictions"]:
            team = pred["team"]
            if team not in constructor_results:
                constructor_results[team] = {
                    "constructor": team,
                    "win_probability": 0.0,
                    "top3_probability": 0.0,
                    "points_expected": 0.0,
                }
            
            constructor_results[team]["win_probability"] += pred["win_probability"]
            constructor_results[team]["top3_probability"] += pred["top3_probability"]
            
            # Approximate points based on position
            pos = pred.get("predicted_position", 20)
            points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
            constructor_results[team]["points_expected"] += points_map.get(pos, 0) * pred["win_probability"]
        
        result = {
            "circuit_id": circuit_id,
            "constructors": sorted(constructor_results.values(), key=lambda x: x["win_probability"], reverse=True),
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Constructor prediction error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/championship')
def championship_page():
    """Championship simulator page."""
    try:
        from data.season_2026 import get_remaining_races
        
        remaining = request.args.get('remaining', 10, type=int)
        remaining_races = get_remaining_races()[:remaining]
        
        # Simplified championship simulation
        from engine.probability_model import predict_race
        
        driver_points = {}
        constructor_points = {}
        
        for race in remaining_races:
            circuit_id = race["id"]
            sim_result = predict_race(
                circuit_id=circuit_id,
                rain_probability=None,
                n_simulations=1000,
            )
            
            for pred in sim_result["predictions"]:
                driver = pred["driver_id"]
                team = pred["team"]
                pos = pred.get("predicted_position", 20)
                
                points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
                pts = points_map.get(pos, 0)
                
                driver_points[driver] = driver_points.get(driver, 0) + pts
                constructor_points[team] = constructor_points.get(team, 0) + pts
        
        result = {
            "remaining_races": len(remaining_races),
            "driver_standings": sorted([{"driver": k, "points": v} for k, v in driver_points.items()], key=lambda x: x["points"], reverse=True)[:10],
            "constructor_standings": sorted([{"constructor": k, "points": v} for k, v in constructor_points.items()], key=lambda x: x["points"], reverse=True),
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Championship simulation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/accuracy')
def accuracy_page():
    """Prediction accuracy tracking page."""
    try:
        from engine.prediction_tracker import PredictionTracker
        
        tracker = PredictionTracker()
        report = tracker.get_accuracy_report()
        tracker.close()
        
        return jsonify(report), 200
    except Exception as e:
        logger.error(f"Accuracy report error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API Proxy Routes ──────────────────────────────────────────────────────────

@app.route('/api/circuits')
def get_circuits():
    """Get list of all circuits."""
    try:
        # Import from existing data module
        from data.circuit_data import get_all_circuits
        circuits = get_all_circuits()
        return jsonify({"circuits": circuits})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/drivers')
def get_drivers():
    """Get list of all drivers."""
    try:
        from data.driver_data import get_all_drivers
        drivers = get_all_drivers()
        return jsonify({"drivers": drivers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "service": "F1 Predictor Dashboard v3.0",
    })


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get('FLASK_PORT', 5000))
    print("Starting F1 Predictor Dashboard v3.0")
    print(f"Dashboard: http://127.0.0.1:{port}")
    print("API: Direct integration (no external API server needed)")
    app.run(debug=True, port=port)
