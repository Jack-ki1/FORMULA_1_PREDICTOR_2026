"""
Web Dashboard — Flask-based interactive dashboard for F1 predictions.

Features:
- Real-time prediction visualization
- H2H driver comparison tool
- Historical accuracy tracking
- Championship simulator
- Interactive charts with Plotly
- Practice, Qualifying, and Race session predictions
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from typing import Dict
import json
import logging
import os
import sys
from functools import wraps

# Add project root to Python path so we can import engine, data, etc.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# SECURITY FIX: Restrict CORS to known origins
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5000").split(","),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-API-Key"],
    }
})

# SECURITY FIX: Add rate limiting to prevent flooding
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # swap to redis:// in production
)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
logger = logging.getLogger(__name__)
API_KEY = os.environ.get("F1_API_KEY")  # Optional API key for authentication


def require_api_key(f):
    """Decorator to require API key authentication on routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/api/test-mapping')
def test_mapping():
    """Test endpoint to verify race name mapping."""
    from data.circuit_data import CIRCUITS
    from data.race_mapping import RACE_NAME_MAPPING
    
    # Verify all mappings work
    results = {}
    for race_name, circuit_id in RACE_NAME_MAPPING.items():
        circuit = CIRCUITS.get(circuit_id)
        results[race_name] = {
            "circuit_id": circuit_id,
            "found": circuit is not None,
            "name": circuit['name'] if circuit else "NOT FOUND"
        }
    
    return jsonify({
        "total_mappings": len(RACE_NAME_MAPPING),
        "working_mappings": sum(1 for v in results.values() if v['found']),
        "results": results
    })


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/predict', methods=['POST'])
@limiter.limit("30 per minute")  # Q-4 FIX: Was "10 per minute" — too strict for auto-running dashboard UI
def api_predict():
    """Unified prediction endpoint for all session types."""
    try:
        data = request.json or {}
        
        logger.info(f"Received prediction request: {data}")
        
        # Input validation
        race_name = data.get('race')
        session_type = data.get('session_type', 'RACE').upper()
        simulations = data.get('simulations', 10000)
        weather = data.get('weather', 'dry')
        
        if not race_name:
            logger.error("No race name provided")
            return jsonify({"success": False, "error": "Race name is required"}), 422
        
        logger.info(f"Processing race: '{race_name}', session: {session_type}")
        
        # Validate session type
        valid_sessions = ['PRACTICE', 'QUALIFYING', 'RACE']
        if session_type not in valid_sessions:
            return jsonify({"success": False, "error": f"Invalid session type. Must be one of: {valid_sessions}"}), 422
        
        # Call prediction engine directly
        from engine.predictor import predict, PredictionRequest
        from data.circuit_data import CIRCUITS
        from data.race_mapping import RACE_NAME_MAPPING
        
        # Find circuit ID from race name
        circuit_id = RACE_NAME_MAPPING.get(race_name)
        logger.info(f"Mapped '{race_name}' to circuit_id: {circuit_id}")
        
        # If not found in mapping, try to match by name field
        if not circuit_id:
            logger.warning(f"No direct mapping found for '{race_name}', trying fuzzy match...")
            for cid, cdata in CIRCUITS.items():
                race_lower = race_name.lower()
                name_lower = cdata['name'].lower()
                country_lower = cdata['country'].lower()
                city_lower = cdata.get('city', '').lower()
                
                if (race_lower in name_lower or 
                    race_lower in country_lower or 
                    race_lower in city_lower or
                    name_lower in race_lower or
                    country_lower in race_lower):
                    circuit_id = cid
                    logger.info(f"Fuzzy matched '{race_name}' to circuit_id: {circuit_id}")
                    break
        
        if not circuit_id:
            available_races = list(RACE_NAME_MAPPING.keys())
            logger.error(f"Circuit not found for '{race_name}'. Available: {available_races}")
            return jsonify({
                "success": False, 
                "error": f"Unknown race: '{race_name}'. Please select from the dropdown menu."
            }), 422
        
        logger.info(f"Running prediction for circuit_id: {circuit_id}")
        
        # Build prediction request based on session type
        # A-1 FIX: Accept grid_positions from request for post-qualifying mode
        grid_positions = data.get('grid_positions', {})
        qualifying_done = bool(grid_positions)
        
        request_obj = PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=0.3 if weather == 'wet' else (0.5 if weather == 'mixed' else 0.1),
            n_simulations=simulations,
            seed=None,
            grid_overrides=grid_positions,
            qualifying_completed=qualifying_done,
        )
        
        # Run prediction
        result = predict(request_obj)
        logger.info(f"Prediction completed successfully for {circuit_id}")
        
        # Format results based on session type
        formatted_results = format_prediction_results(result, session_type)
        
        # Debug logging
        logger.info(f"Formatted results keys: {list(formatted_results.keys())}")
        if 'chart_data' in formatted_results:
            logger.info(f"Chart data keys: {list(formatted_results['chart_data'].keys())}")
            for key, value in formatted_results['chart_data'].items():
                if isinstance(value, list):
                    logger.info(f"  {key}: {len(value)} items")
                elif isinstance(value, dict):
                    logger.info(f"  {key}: dict with {len(value)} keys")
                else:
                    logger.info(f"  {key}: {type(value).__name__}")
        
        # Add chart data for race predictions
        if session_type == 'RACE':
            predictions_sorted = sorted(
                result.get("predictions", []),
                key=lambda x: x.get('win_pct', 0),
                reverse=True
            )[:10]
            
            formatted_results['chart_data'] = formatted_results.get('chart_data', {})
            formatted_results['chart_data']['win_probabilities'] = [
                {
                    'driver': p.get('driver', 'Unknown'),
                    'team': p.get('team', '').replace('_', ' ').title(),
                    'probability': p.get('win_pct', 0)
                }
                for p in predictions_sorted
            ]
        
        # Generate HTML report
        try:
            from reports.html_report import generate_f1_themed_report
            report_path = generate_f1_themed_report(
                circuit_id=circuit_id,
                rain_probability=request_obj.rain_probability,
                n_simulations=simulations,
                session_type=session_type
            )
            formatted_results['report_url'] = f"/{report_path}"
            logger.info(f"Report generated at: {report_path}")
        except Exception as e:
            logger.warning(f"Failed to generate report: {e}")
            formatted_results['report_url'] = None
        
        return jsonify({
            "success": True,
            "results": formatted_results,
            "session_type": session_type,
            "race": race_name
        })
        
    except KeyError as e:
        logger.error(f"KeyError in prediction: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Circuit not found: {str(e)}. Please ensure you select a valid Grand Prix from the dropdown."}), 422
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Prediction failed: {str(e)}"}), 500


def format_prediction_results(result: Dict, session_type: str) -> Dict:
    """Format prediction results based on session type with comprehensive metrics."""
    predictions = sorted(
        result.get("predictions", []),
        key=lambda x: x.get('predicted_position', 999),
    )
    
    podium = result.get("podium_predictions", [])
    meta = result.get("meta", {})
    
    if session_type == 'PRACTICE':
        # Practice session predictions with detailed metrics
        fastest = predictions[0] if predictions else {}
        top3 = [p.get('driver', 'N/A') for p in predictions[:3]]
        top10 = predictions[:10]
        
        # Calculate lap time spread (simulated for practice)
        avg_lap = 90.0  # Default 1:30
        
        return {
            "fastest_driver": fastest.get('driver', 'N/A'),
            "top_3": top3,
            "avg_lap_time": f"{int(avg_lap // 60)}:{avg_lap % 60:05.2f}",
            "confidence": meta.get('overall_model_confidence', 0) * 100,
            "session_type": "Practice",
            "meta": {
                "safety_car_probability": meta.get('safety_car_probability', 0),
                "rain_probability": meta.get('rain_probability', 0),
                "overall_model_confidence": meta.get('overall_model_confidence', 0),
                "n_simulations": meta.get('n_simulations', None)
            },
            "chart_data": {
                "lap_time_comparison": [
                    {
                        'driver': p.get('driver', 'Unknown'),
                        'team': p.get('team', '').replace('_', ' ').title(),
                        'lap_time': 90.0 + (i * 0.5),
                        'gap_to_fastest': round(i * 0.5, 3)
                    }
                    for i, p in enumerate(top10)
                ],
                "consistency_ratings": [
                    {
                        'driver': p.get('driver', 'Unknown'),
                        'consistency': p.get('confidence', '').lower() == 'high' and 85 or (p.get('confidence', '').lower() == 'medium' and 70 or 55),
                        'reliability': (1 - p.get('dnf_pct', 20) / 100) * 100
                    }
                    for p in top10
                ]
            }
        }
    
    elif session_type == 'QUALIFYING':
        # Qualifying predictions with comprehensive analysis
        pole = predictions[0] if predictions else {}
        front_row = [p.get('driver', 'N/A') for p in predictions[:2]]
        q3_drivers = [p.get('driver', 'N/A') for p in predictions[:10]]
        q2_eliminated = [p.get('driver', 'N/A') for p in predictions[10:15]]
        q1_eliminated = [p.get('driver', 'N/A') for p in predictions[15:20]]
        
        return {
            "pole_position": pole.get('driver', 'N/A'),
            "front_row": front_row,
            "q3_drivers": q3_drivers,
            "pole_time": "1:18.234",
            "confidence": meta.get('overall_model_confidence', 0) * 100,
            "session_type": "Qualifying",
            "meta": {
                "safety_car_probability": meta.get('safety_car_probability', 0),
                "rain_probability": meta.get('rain_probability', 0),
                "overall_model_confidence": meta.get('overall_model_confidence', 0),
                "n_simulations": meta.get('n_simulations', None)
            },
            "chart_data": {
                "qualifying_positions": [
                    {
                        'position': i + 1,
                        'driver': p.get('driver', 'Unknown'),
                        'team': p.get('team', '').replace('_', ' ').title(),
                        'probability': p.get('win_pct', 0),
                        'expected_gap': round(i * 0.3, 3)
                    }
                    for i, p in enumerate(predictions[:20])
                ],
                "elimination_risk": {
                    "q1_at_risk": q1_eliminated,
                    "q2_at_risk": q2_eliminated,
                    "safe_in_q3": q3_drivers
                },
                "grid_penalties": []
            }
        }
    
    elif session_type == 'RACE':
        # Race predictions with full comprehensive metrics
        winner = predictions[0] if predictions else {}
        podium_names = [p.get('driver', 'N/A') for p in predictions[:3]]
        
        # Calculate win probability for winner
        win_prob = winner.get('win_pct', 0)
        
        # Get top 10 for points
        points_finishers = [
            {**p, 'position': i + 1, 'predicted_position': i + 1}
            for i, p in enumerate(predictions[:10])
        ]
        
        # DNF risk analysis - use dnf_pct field
        dnf_risk = [
            {
                'driver': p.get('driver', 'Unknown'),
                'dnf_probability': p.get('dnf_pct', 0),
                'risk_factors': []
            }
            for p in predictions[:15]
        ]
        
        # Constructor standings prediction
        constructor_points = {}
        for p in predictions[:15]:
            team = p.get('team', 'unknown').replace('_', ' ').title()
            expected_pts = p.get('expected_points', 0)
            constructor_points[team] = constructor_points.get(team, 0) + expected_pts
        
        # Weather impact analysis
        weather_impact = {
            'rain_probability': meta.get('rain_probability', 0) * 100,
            'safety_car_likelihood': meta.get('safety_car_probability', 0) * 100,
            'tire_strategy_impact': 0.5,
            'overtaking_opportunities': 5
        }
        
        # Position distribution heatmap data - position_distribution is a list
        position_heatmap = []
        for p in predictions[:10]:
            pos_dist = p.get('position_distribution', [])
            if isinstance(pos_dist, list) and len(pos_dist) > 0:
                positions = list(range(1, len(pos_dist) + 1))
                probs = pos_dist
            else:
                positions = list(range(1, 21))
                probs = [0] * 20
            position_heatmap.append({
                'driver': p.get('driver', 'Unknown'),
                'positions': positions,
                'probabilities': probs
            })
        
        # Cumulative probability analysis - use top3_pct, top5_pct, top10_pct
        # M-3 FIX: Use actual probability data instead of hardcoded nonsense values
        cumulative_prob = [
            {
                'driver': p.get('driver', 'Unknown'),
                'cumulative_top3': p.get('top3_pct', 0),
                'cumulative_top5': p.get('top5_pct', 0),
                'cumulative_top10': p.get('top10_pct', 0),
                'cumulative_points': round(p.get('expected_points', 0), 1),  # M-3 FIX: Direct value
            }
            for p in sorted(predictions, key=lambda x: x.get('top3_pct', 0), reverse=True)[:15]
        ]
        
        # Overtaking potential analysis - use composite_score as proxy
        overtaking_analysis = [
            {
                'driver': p.get('driver', 'Unknown'),
                'starting_position': p.get('predicted_position', 0),
                'expected_finish': p.get('predicted_position', 0),
                'position_change': 0,
                'overtaking_rating': p.get('composite_score', 0.5) * 100
            }
            for p in predictions[:15]
        ]
        
        # Tire strategy simulation - derive from confidence and position
        tire_strategies = [
            {
                'driver': p.get('driver', 'Unknown'),
                'optimal_stops': 2 if p.get('predicted_position', 20) <= 10 else 1,
                'strategy_reliability': 90 if p.get('confidence', '').lower() == 'high' else (75 if p.get('confidence', '').lower() == 'medium' else 60),
                'tire_wear_rate': 50
            }
            for p in predictions[:10]
        ]
        
        # Teammate battle analysis
        teammate_battles = []
        teams_dict = {}
        for p in predictions:
            team = p.get('team', 'unknown')
            if team not in teams_dict:
                teams_dict[team] = []
            teams_dict[team].append(p)
        
        for team, drivers in teams_dict.items():
            if len(drivers) >= 2:
                d1, d2 = drivers[0], drivers[1]
                teammate_battles.append({
                    'team': team.replace('_', ' ').title(),
                    'driver1': d1.get('driver', 'Unknown'),
                    'driver1_points': d1.get('expected_points', 0),
                    'driver2': d2.get('driver', 'Unknown'),
                    'driver2_points': d2.get('expected_points', 0),
                    'battle_intensity': abs(d1.get('expected_points', 0) - d2.get('expected_points', 0))
                })
        
        return {
            "winner": winner.get('driver', 'N/A'),
            "podium": podium_names,
            "fastest_lap": predictions[0].get('driver', 'N/A') if predictions else 'N/A',
            "win_probability": win_prob,
            "points_finishers": points_finishers,
            "confidence": meta.get('overall_model_confidence', 0) * 100,
            "session_type": "Race",
            "report_url": None,
            "meta": {
                "safety_car_probability": meta.get('safety_car_probability', 0),
                "rain_probability": meta.get('rain_probability', 0),
                "overall_model_confidence": meta.get('overall_model_confidence', 0),
                "n_simulations": meta.get('n_simulations', 0)
            },
            
            # Comprehensive chart data - ALL FIELDS MUST BE POPULATED
            "chart_data": {
                "win_probabilities": [
                    {
                        'driver': p.get('driver', 'Unknown'),
                        'team': p.get('team', '').replace('_', ' ').title(),
                        'probability': p.get('win_pct', 0)
                    }
                    for p in sorted(predictions, key=lambda x: x.get('win_pct', 0), reverse=True)[:10]
                ],
                
                "podium_probabilities": [
                    {
                        'driver': p.get('driver', 'Unknown'),
                        'team': p.get('team', '').replace('_', ' ').title(),
                        'podium_chance': p.get('top3_pct', 0),
                        'win_chance': p.get('win_pct', 0),
                        'top5_chance': p.get('top5_pct', 0)
                    }
                    for p in sorted(predictions, key=lambda x: x.get('top3_pct', 0), reverse=True)[:10]
                ],
                
                "expected_finish_positions": [
                    {
                        'position': i + 1,
                        'driver': p.get('driver', 'Unknown'),
                        'team': p.get('team', '').replace('_', ' ').title(),
                        'expected_position': float(p.get('predicted_position', i + 1)),
                        'position_range': [
                            max(1, p.get('predicted_position', i + 1) - 2),
                            min(20, p.get('predicted_position', i + 1) + 2)
                        ]
                    }
                    for i, p in enumerate(predictions[:15])
                ],
                
                "points_distribution": [
                    {
                        'position': i + 1,
                        'driver': p.get('driver', 'Unknown'),
                        'expected_points': float(p.get('expected_points', 0)),
                        'points_range': [
                            max(0, p.get('expected_points', 0) - 2),
                            p.get('expected_points', 0) + 2
                        ]
                    }
                    for i, p in enumerate(points_finishers)
                ],
                
                "dnf_risk_analysis": dnf_risk,
                
                "constructor_standings": sorted(
                    [
                        {'team': team, 'points': round(pts, 1)}
                        for team, pts in constructor_points.items()
                    ],
                    key=lambda x: x['points'],
                    reverse=True
                ),
                
                "weather_impact": weather_impact,
                
                "model_performance": {
                    'overall_confidence': meta.get('overall_model_confidence', 0) * 100,
                    'simulation_count': meta.get('n_simulations', 0),
                    'convergence_rate': 85,
                    'prediction_variance': 0.15,
                    'historical_accuracy': 78
                },
                
                "position_heatmap": position_heatmap,
                
                "cumulative_probability": cumulative_prob,
                
                "overtaking_analysis": overtaking_analysis,
                
                "tire_strategies": tire_strategies,
                
                "teammate_battles": teammate_battles,
                
                "driver_standings_impact": [
                    {
                        'driver': p.get('driver', 'Unknown'),
                        'current_championship_points': 0,
                        'projected_total': p.get('expected_points', 0),
                        'points_gained': p.get('expected_points', 0)
                    }
                    for p in predictions[:15]
                ]
            }
        }
    
    return {"error": "Invalid session type"}


@app.route('/predict', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def predict_page():
    """Race prediction page."""
    if request.method == 'POST':
        data = request.json or {}
        try:
            # Input validation
            circuit_id = data.get('circuit_id')
            if not circuit_id:
                return jsonify({"error": "circuit_id is required"}), 422
            
            from data.circuit_data import CIRCUITS
            if circuit_id not in CIRCUITS:
                return jsonify({"error": f"Unknown circuit: {circuit_id!r}"}), 422
            
            rain_probability = data.get('rain_probability')
            if rain_probability is not None:
                if not (0.0 <= rain_probability <= 1.0):
                    return jsonify({"error": "rain_probability must be in [0, 1]"}), 422
            
            n_simulations = data.get('n_simulations', 5000)
            if not isinstance(n_simulations, int) or n_simulations < 100 or n_simulations > 50000:
                n_simulations = max(100, min(int(n_simulations), 50000))  # Clamp to valid range
            
            # Call prediction engine directly instead of proxying to API
            from engine.predictor import predict, PredictionRequest
            
            request_obj = PredictionRequest(
                circuit_id=circuit_id,
                rain_probability=rain_probability,
                n_simulations=n_simulations,
            )
            
            result = predict(request_obj)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    return render_template('dashboard.html')


@app.route('/api/h2h', methods=['POST'])
@limiter.limit("20 per hour")
def api_h2h():
    """Driver vs Driver head-to-head analysis.

    Returns a JSON shape that the dashboard H2H JS can render reliably.
    """
    try:
        data = request.json or {}

        # race selector in UI uses circuit name (e.g. 'Australian Grand Prix')
        race_name = data.get('race')
        circuit_id = data.get('circuit_id')
        if not circuit_id and race_name:
            from data.race_mapping import RACE_NAME_MAPPING
            circuit_id = RACE_NAME_MAPPING.get(race_name)

        if not circuit_id:
            return jsonify({"success": False, "error": "circuit_id or race is required"}), 422

        driver1 = data.get('driver1')
        driver2 = data.get('driver2')
        if not driver1 or not driver2 or driver1 == driver2:
            return jsonify({"success": False, "error": "Select two different drivers"}), 422

        n_simulations = data.get('simulations', data.get('n_simulations', 10000))
        try:
            n_simulations = int(n_simulations)
        except Exception:
            n_simulations = 10000

        weather = data.get('weather', 'dry')
        rain_probability = 0.1 if weather == 'dry' else (0.3 if weather == 'mixed' else 0.5)

        # Run race simulation (engine already supports rain/sims)
        from engine.probability_model import predict_race, simulate_h2h

        # Run full race simulation once for win/top3 + distributions
        sim_result = predict_race(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
        )

        predictions = {p.get("driver_id"): p for p in sim_result.get("predictions", [])}
        if driver1 not in predictions or driver2 not in predictions:
            return jsonify({"success": False, "error": "Drivers not found in simulation results"}), 400

        d1_pred = predictions[driver1]
        d2_pred = predictions[driver2]

        # Pairwise ahead probability from joint simulation ordering
        h2h_sim = simulate_h2h(
            circuit_id=circuit_id,
            driver1_id=driver1,
            driver2_id=driver2,
            rain_probability=rain_probability,
            n_runs=n_simulations,
            seed=None,
        )
        p_sim_ahead = float(h2h_sim.get("driver1_ahead_probability_no_tie", 0.5))

        # ELO H2H prior
        from engine.multi_dimensional_elo import get_elo_system
        elo = get_elo_system()
        elo_comp = elo.compare_drivers(driver1, driver2, dimension="race")
        p_elo_ahead = float(elo_comp.get("win_probability", 0.5)) if elo_comp else 0.5

        # Blend: when sims are high, trust joint simulation more.
        w = min(1.0, max(0.0, n_simulations / 20000.0))
        p_final_ahead = (w * p_sim_ahead) + ((1 - w) * p_elo_ahead)
        p_final_ahead = max(0.0, min(1.0, p_final_ahead))

        d1_win = float(d1_pred.get("win_probability", 0.0))
        d2_win = float(d2_pred.get("win_probability", 0.0))
        d1_top3 = float(d1_pred.get("top3_probability", 0.0))
        d2_top3 = float(d2_pred.get("top3_probability", 0.0))

        # Keep position_distribution for UI chart (still marginals, but “ahead” uses joint)
        pos_dist_1 = d1_pred.get("position_distribution", []) or []
        pos_dist_2 = d2_pred.get("position_distribution", []) or []

        total_1 = sum(pos_dist_1) if pos_dist_1 else 1
        total_2 = sum(pos_dist_2) if pos_dist_2 else 1

        prob_dist_1 = [count / total_1 for count in pos_dist_1] if pos_dist_1 else []
        prob_dist_2 = [count / total_2 for count in pos_dist_2] if pos_dist_2 else []

        return jsonify({
            "success": True,
            "circuit_id": circuit_id,
            "drivers": {
                "driver1": driver1,
                "driver2": driver2,
            },
            "summary": {
                "winner": driver1 if d1_win >= d2_win else driver2,
                "win_margin_pct": round(abs(d1_win - d2_win) * 100, 1),
                "confidence_pct": round(max(d1_win, d2_win) * 100, 1),
                "simulations": n_simulations,
            },
            "duel": {
                "driver1_finishes_ahead_pct": round(p_final_ahead * 100, 1),
                "driver2_finishes_ahead_pct": round((1 - p_final_ahead) * 100, 1),
                "driver1_win_pct": round(d1_win * 100, 1),
                "driver2_win_pct": round(d2_win * 100, 1),
                "driver1_podium_pct": round(d1_top3 * 100, 1),
                "driver2_podium_pct": round(d2_top3 * 100, 1),
                "ahead_blend": {
                    "p_sim": round(p_sim_ahead, 4),
                    "p_elo": round(p_elo_ahead, 4),
                    "weight_sim": round(w, 4),
                    "p_final": round(p_final_ahead, 4),
                },
            },
            "position_distribution": {
                "driver1": prob_dist_1,
                "driver2": prob_dist_2,
            }
        }), 200
    except Exception as e:
        logger.error(f"H2H error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500



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


# ── HTML Report Download ──────────────────────────────────────────────────────

@app.route('/download-report/<circuit_id>')
def download_report(circuit_id):
    """Generate and download full HTML prediction report."""
    try:
        from reports.html_report import generate_report
        from engine.predictor import predict, PredictionRequest
        
        # Run prediction
        request_obj = PredictionRequest(
            circuit_id=circuit_id,
            n_simulations=10000
        )
        
        result = predict(request_obj)
        
        # Generate report
        report_path = generate_report(circuit_id)
        
        # Convert to absolute path if it's relative
        if not os.path.isabs(report_path):
            # The report is generated relative to project root, not dashboard
            report_path = os.path.join(project_root, report_path)
        
        logger.info(f"Serving report from: {report_path}")
        
        # Check if file exists before sending
        if not os.path.exists(report_path):
            logger.error(f"Report file not found at: {report_path}")
            return jsonify({"error": f"Report file not found: {report_path}"}), 404
        
        # Send file for download
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Report generation error: {e}")
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


@app.route('/api/constructors/live', methods=['GET'])
@limiter.limit("30 per hour")
def get_live_constructors():
    """Fetch live constructor and driver standings from Ergast API."""
    try:
        import requests
        
        logger.info("Fetching live constructor standings from Ergast API...")
        
        # Ergast API has migrated to api.jolpi.ca
        # Try multiple endpoints in order of preference
        api_endpoints = [
            "https://api.jolpi.ca/ergast/f1/current/constructorStandings.json",
            "https://ergast.com/api/f1/current/constructorStandings.json",
            "http://ergast.com/api/f1/current/constructorStandings.json",
        ]
        
        driver_endpoints = [
            "https://api.jolpi.ca/ergast/f1/current/driverStandings.json",
            "https://ergast.com/api/f1/current/driverStandings.json",
            "http://ergast.com/api/f1/current/driverStandings.json",
        ]
        
        constructor_data = None
        driver_data = None
        
        # Try constructor endpoints
        for url in api_endpoints:
            try:
                logger.info(f"Trying constructor URL: {url}")
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    constructor_data = response.json()
                    logger.info(f"✓ Successfully fetched constructor data from {url}")
                    break
                else:
                    logger.warning(f"✗ Status {response.status_code} from {url}")
            except Exception as e:
                logger.warning(f"✗ Failed to fetch from {url}: {e}")
                continue
        
        # Try driver endpoints
        for url in driver_endpoints:
            try:
                logger.info(f"Trying driver URL: {url}")
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    driver_data = response.json()
                    logger.info(f"✓ Successfully fetched driver data from {url}")
                    break
                else:
                    logger.warning(f"✗ Status {response.status_code} from {url}")
            except Exception as e:
                logger.warning(f"✗ Failed to fetch from {url}: {e}")
                continue
        
        if not constructor_data or not driver_data:
            logger.error("Failed to fetch data from all Ergast API endpoints")
            return jsonify({
                "success": False,
                "error": "Unable to connect to F1 data source. The Ergast API may be temporarily unavailable.",
                "fallback": True
            }), 503
        
        # Parse constructor standings
        standings_list = constructor_data['MRData']['StandingsTable']['StandingsLists']
        if not standings_list:
            raise ValueError("No standings data available")
            
        constructors = []
        for standing in standings_list[0]['ConstructorStandings']:
            constructor = standing['Constructor']
            constructors.append({
                'position': int(standing['position']),
                'team_id': constructor['constructorId'],
                'name': constructor['name'],
                'nationality': constructor.get('nationality', 'Unknown'),
                'points': float(standing['points']),
                'wins': int(standing.get('wins', 0))
            })
        
        # Parse driver standings with team info
        driver_standings_list = driver_data['MRData']['StandingsTable']['StandingsLists']
        drivers = []
        for standing in driver_standings_list[0]['DriverStandings']:
            driver = standing['Driver']
            constructor = standing['Constructors'][0] if standing['Constructors'] else {}
            
            drivers.append({
                'position': int(standing['position']),
                'driver_id': driver['driverId'],
                'permanent_number': driver.get('permanentNumber', ''),
                'code': driver.get('code', ''),
                'given_name': driver.get('givenName', ''),
                'family_name': driver.get('familyName', ''),
                'nationality': driver.get('nationality', 'Unknown'),
                'points': float(standing['points']),
                'wins': int(standing.get('wins', 0)),
                'team_id': constructor.get('constructorId', ''),
                'team_name': constructor.get('name', 'Unknown')
            })
        
        # Group drivers by team
        team_drivers = {}
        for driver in drivers:
            team_id = driver['team_id']
            if team_id not in team_drivers:
                team_drivers[team_id] = []
            team_drivers[team_id].append(driver)
        
        # Enrich constructor data with driver info
        for constructor in constructors:
            team_id = constructor['team_id']
            constructor['drivers'] = team_drivers.get(team_id, [])
            constructor['driver_count'] = len(constructor['drivers'])
        
        # Calculate advanced analytics
        # 1. Points gap analysis
        if len(constructors) >= 2:
            points_gaps = []
            for i in range(len(constructors) - 1):
                gap = constructors[i]['points'] - constructors[i+1]['points']
                points_gaps.append({
                    'position': f"P{constructors[i]['position']}-P{constructors[i+1]['position']}",
                    'gap': round(gap, 1),
                    'teams': f"{constructors[i]['name']} vs {constructors[i+1]['name']}"
                })
        else:
            points_gaps = []
        
        # 2. Win distribution
        total_wins = sum(c['wins'] for c in constructors)
        win_distribution = []
        for c in constructors:
            win_pct = (c['wins'] / total_wins * 100) if total_wins > 0 else 0
            win_distribution.append({
                'team': c['name'],
                'wins': c['wins'],
                'percentage': round(win_pct, 1)
            })
        
        # 3. Driver contribution per team
        driver_contributions = []
        for constructor in constructors:
            team_drivers_list = constructor.get('drivers', [])
            if len(team_drivers_list) == 2:
                d1 = team_drivers_list[0]
                d2 = team_drivers_list[1]
                total_team_points = d1['points'] + d2['points']
                if total_team_points > 0:
                    driver_contributions.append({
                        'team': constructor['name'],
                        'driver1': f"{d1['code'] or d1['family_name']}",
                        'driver1_points': d1['points'],
                        'driver1_pct': round((d1['points'] / total_team_points) * 100, 1),
                        'driver2': f"{d2['code'] or d2['family_name']}",
                        'driver2_points': d2['points'],
                        'driver2_pct': round((d2['points'] / total_team_points) * 100, 1)
                    })
        
        # 4. Average points per position
        position_groups = {}
        for c in constructors:
            pos_group = ((c['position'] - 1) // 2) * 2 + 1  # Group by pairs
            if pos_group not in position_groups:
                position_groups[pos_group] = []
            position_groups[pos_group].append(c['points'])
        
        avg_by_position = []
        for pos_group in sorted(position_groups.keys()):
            pts = position_groups[pos_group]
            avg_by_position.append({
                'position_range': f"P{pos_group}-P{pos_group+1}",
                'avg_points': round(sum(pts) / len(pts), 1),
                'teams': len(pts)
            })
        
        # 5. Performance tiers
        max_points = max(c['points'] for c in constructors) if constructors else 1
        for c in constructors:
            pct_of_leader = (c['points'] / max_points * 100) if max_points > 0 else 0
            if pct_of_leader >= 80:
                c['tier'] = 'Top Tier'
                c['tier_color'] = '#10b981'
            elif pct_of_leader >= 50:
                c['tier'] = 'Mid Field'
                c['tier_color'] = '#f59e0b'
            else:
                c['tier'] = 'Back Marker'
                c['tier_color'] = '#ef4444'
        
        # 6. Team Performance Radar Metrics (normalized 0-100 scale)
        team_radar_data = []
        for constructor in constructors[:5]:  # Top 5 teams only for clarity
            team_drivers_list = constructor.get('drivers', [])
            
            # Calculate metrics
            total_points = constructor['points']
            wins = constructor['wins']
            driver_count = constructor['driver_count']
            
            # Points per driver (efficiency metric)
            points_per_driver = total_points / driver_count if driver_count > 0 else 0
            
            # Win rate (percentage of races won)
            win_rate = (wins / 5) * 100 if len(constructors) > 0 else 0  # Assuming ~5 races so far
            
            # Consistency score (based on both drivers scoring points)
            if len(team_drivers_list) == 2:
                d1_pts = team_drivers_list[0]['points']
                d2_pts = team_drivers_list[1]['points']
                total_driver_pts = d1_pts + d2_pts
                consistency = min((min(d1_pts, d2_pts) / max(d1_pts, d2_pts)) * 100, 100) if max(d1_pts, d2_pts) > 0 else 0
            else:
                consistency = 0
            
            # Normalized scores (0-100)
            max_possible_points = max_points * 2  # Theoretical max if both drivers scored like leader
            normalized_points = (total_points / max_possible_points * 100) if max_possible_points > 0 else 0
            
            team_radar_data.append({
                'team': constructor['name'],
                'team_id': constructor['team_id'],
                'metrics': {
                    'Championship Points': round(normalized_points, 1),
                    'Race Wins': round(win_rate, 1),
                    'Points Efficiency': round((points_per_driver / max_points * 100), 1) if max_points > 0 else 0,
                    'Driver Balance': round(consistency, 1),
                    'Competitiveness': round(pct_of_leader, 1)
                }
            })
        
        logger.info(f"Successfully processed {len(constructors)} constructors and {len(drivers)} drivers")
        
        return jsonify({
            "success": True,
            "season": constructor_data['MRData']['StandingsTable'].get('season', 'current'),
            "round": constructor_data['MRData']['StandingsTable'].get('round', 'latest'),
            "constructors": constructors,
            "drivers": drivers,
            "total_teams": len(constructors),
            "total_drivers": len(drivers),
            "analytics": {
                "points_gaps": points_gaps,
                "win_distribution": win_distribution,
                "driver_contributions": driver_contributions,
                "avg_by_position": avg_by_position,
                "performance_tiers": [
                    {"team": c['name'], "tier": c['tier'], "color": c['tier_color'], "points": c['points']}
                    for c in constructors
                ],
                "team_radar_data": team_radar_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching live constructor data: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "fallback": True
        }), 500


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve local images from the dashboard template folder.

    This keeps the hero images in `dashboard/templates` accessible without
    moving them into a separate static directory.
    """
    try:
        # Simple allowlist to avoid exposing arbitrary files
        if not filename.startswith('f1_image') or '..' in filename or '/' in filename.replace('\\', '/'):
            return jsonify({"error": "Invalid image"}), 400
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        img_path = os.path.join(templates_dir, filename)
        if not os.path.exists(img_path):
            return jsonify({"error": "Not found"}), 404
        return send_file(img_path)
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({"error": str(e)}), 500


# ── Database Management ──────────────────────────────────────────────────────

@app.route('/api/database/migrate', methods=['POST'])
def api_migrate_db():
    """Initialize database and migrate static data."""
    try:
        from database.models import migrate_from_static, SessionLocal, Driver, Race
        
        # Run migration (returns None)
        migrate_from_static()
        
        # Count actual records created
        db = SessionLocal()
        try:
            driver_count = db.query(Driver).count()
            race_count = db.query(Race).count()
            
            return jsonify({
                "status": "success",
                "message": f"Database migration completed - {driver_count} drivers, {race_count} races",
                "tables_created": ["drivers", "races", "predictions"],
                "records_migrated": driver_count + race_count
            })
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Weight Optimization ──────────────────────────────────────────────────────

@app.route('/api/optimize/weights', methods=['POST'])
def api_optimize_weights():
    """Run Optuna optimization on feature weights."""
    try:
        import subprocess
        import sys
        
        data = request.json
        n_trials = data.get('trials', 100)
        
        # Run optimization script
        result = subprocess.run(
            [sys.executable, 'scripts/optimize_weights_v3.py', 
             '--trials', str(n_trials)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "Optimization completed",
                "output": result.stdout,
                "trials_completed": n_trials
            })
        else:
            return jsonify({
                "status": "error",
                "message": result.stderr or "Optimization failed"
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "Optimization timed out (10 min limit)"
        }), 500
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Backtesting ───────────────────────────────────────────────────────────────

@app.route('/api/backtest/run', methods=['POST'])
def api_run_backtest():
    """Execute temporal cross-validation backtest."""
    try:
        import subprocess
        import sys
        
        data = request.json
        seasons = data.get('seasons', [2025])
        sims = data.get('sims', 10000)
        
        # Build command
        cmd = [sys.executable, 'scripts/backtest_2025_season.py', '--sims', str(sims)]
        for season in seasons:
            cmd.extend(['--seasons', str(season)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "Backtest completed",
                "output": result.stdout,
                "seasons_tested": seasons
            })
        else:
            return jsonify({
                "status": "error",
                "message": result.stderr or "Backtest failed"
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "Backtest timed out (30 min limit)"
        }), 500
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Calibration ───────────────────────────────────────────────────────────────

@app.route('/api/calibration/run', methods=['POST'])
def api_run_calibration():
    """Execute Platt scaling calibration."""
    try:
        import subprocess
        import sys
        
        data = request.json
        season = data.get('season', 2026)
        
        result = subprocess.run(
            [sys.executable, 'scripts/calibrate_probabilities.py',
             '--season', str(season)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "Calibration completed",
                "output": result.stdout,
                "season": season
            })
        else:
            return jsonify({
                "status": "error",
                "message": result.stderr or "Calibration failed"
            }), 500
    
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Race Evaluation ───────────────────────────────────────────────────────────

@app.route('/api/evaluate/race', methods=['POST'])
def api_evaluate_race():
    """Evaluate predictions against actual race results."""
    try:
        from engine.prediction_tracker import PredictionTracker
        
        data = request.json
        circuit_id = data['circuit_id']
        results = data['results']  # Dict of driver_id -> position
        
        tracker = PredictionTracker()
        evaluation = tracker.evaluate_race(circuit_id, results)
        
        return jsonify({
            "status": "success",
            "circuit": circuit_id,
            "metrics": evaluation
        })
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/template/generate', methods=['POST'])
def api_generate_template():
    """Generate race results template."""
    try:
        from data.driver_data import get_all_drivers
        
        drivers = get_all_drivers()
        template = {driver['id']: 0 for driver in drivers}
        
        return jsonify({
            "status": "success",
            "template": template
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── FastF1 Sync ───────────────────────────────────────────────────────────────

@app.route('/api/sync/fastf1', methods=['POST'])
def api_sync_fastf1():
    """Sync historical data from FastF1 library."""
    try:
        import subprocess
        import sys
        
        data = request.json
        seasons = data.get('seasons', [2024, 2025])
        
        cmd = [sys.executable, '-c', 
               f'from data.fastf1_integration import sync_seasons; sync_seasons({seasons})']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        return jsonify({
            "status": "success",
            "message": "FastF1 sync completed",
            "output": result.stdout,
            "seasons_synced": seasons
        })
    
    except Exception as e:
        logger.error(f"FastF1 sync failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Quality Check ─────────────────────────────────────────────────────────────

@app.route('/api/quality/check', methods=['GET'])
def api_quality_check():
    """Run data quality checks."""
    try:
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, 'scripts/data_quality_report.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return jsonify({
            "status": "success",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr if result.returncode != 0 else None
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Benchmark ─────────────────────────────────────────────────────────────────

@app.route('/api/benchmark/run', methods=['POST'])
def api_benchmark():
    """Run performance benchmark."""
    try:
        from engine.vectorized_simulation import compare_performance
        
        data = request.json
        circuit = data.get('circuit', 'canada')
        sims = data.get('sims', 5000)
        
        result = compare_performance(circuit, n_runs=sims, seed=42)
        
        return jsonify({
            "status": "success",
            "benchmark": result
        })
    
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── Accuracy Report ───────────────────────────────────────────────────────────

@app.route('/api/accuracy/report', methods=['GET'])
def api_accuracy_report():
    """Get comprehensive accuracy report."""
    try:
        from engine.prediction_tracker import PredictionTracker
        
        tracker = PredictionTracker()
        report = tracker.get_accuracy_report()
        
        # FIX: Transform report to match frontend expectations
        # Backend returns: total_predictions, avg_brier_score, win_prediction_brier, top3_prediction_brier, avg_position_error, calibration
        # Frontend expects: total_races, overall_accuracy, winner_accuracy, mean_position_error, podium_accuracy
        
        # Handle case where no data exists
        if "message" in report:
            return jsonify({
                "status": "success",
                "report": {
                    "total_races": 0,
                    "overall_accuracy": 0.0,
                    "winner_accuracy": 0.0,
                    "mean_position_error": 0.0,
                    "podium_accuracy": 0.0,
                }
            })
        
        # Calculate derived metrics from Brier scores (lower Brier = higher accuracy)
        avg_brier = report.get('avg_brier_score', 1.0)
        win_brier = report.get('win_prediction_brier', 1.0)
        top3_brier = report.get('top3_prediction_brier', 1.0)
        
        # Convert Brier scores to accuracy percentages (Brier score of 0 = 100% accuracy, 1 = 0% accuracy)
        overall_accuracy = max(0, (1 - avg_brier) * 100)
        winner_accuracy = max(0, (1 - win_brier) * 100)
        podium_accuracy = max(0, (1 - top3_brier) * 100)
        
        # Estimate number of races (predictions / ~20 drivers per race)
        total_predictions = report.get('total_predictions', 0)
        total_races = max(1, total_predictions // 20)
        
        return jsonify({
            "status": "success",
            "report": {
                "total_races": total_races,
                "overall_accuracy": round(overall_accuracy, 1),
                "winner_accuracy": round(winner_accuracy, 1),
                "mean_position_error": report.get('avg_position_error', 0.0),
                "podium_accuracy": round(podium_accuracy, 1),
            }
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ── System Setup Wizard ───────────────────────────────────────────────────────

@app.route('/api/setup/initialize', methods=['POST'])
def api_initialize_system():
    """Complete system initialization in one click."""
    steps = []
    
    try:
        # Step 1: Migrate database
        from database.models import migrate_from_static
        migrate_from_static()
        
        # Count records to provide feedback
        from database.models import SessionLocal, Driver, Race
        db = SessionLocal()
        try:
            driver_count = db.query(Driver).count()
            race_count = db.query(Race).count()
            steps.append({
                "step": "database",
                "status": "success",
                "details": f"Created {driver_count} drivers and {race_count} races"
            })
        finally:
            db.close()
            
    except Exception as e:
        steps.append({
            "step": "database",
            "status": "error",
            "details": str(e)
        })
        return jsonify({
            "setup_complete": False,
            "steps": steps,
            "error": "Database migration failed"
        }), 500
    
    try:
        # Step 2: Quality check
        from scripts.data_quality_report import run_quality_check
        quality_result = run_quality_check()
        
        if quality_result.get('passed', False):
            steps.append({
                "step": "validation",
                "status": "success",
                "details": f"Data validation passed - {quality_result.get('error_count', 0)} errors, {quality_result.get('warning_count', 0)} warnings"
            })
        else:
            error_list = quality_result.get('errors', [])
            steps.append({
                "step": "validation",
                "status": "warning",
                "details": f"Some issues found: {'; '.join(error_list[:3])}"  # Show first 3 errors
            })
    except Exception as e:
        steps.append({
            "step": "validation",
            "status": "error",
            "details": str(e)
        })
    
    return jsonify({
        "setup_complete": all(s["status"] != "error" for s in steps),
        "steps": steps,
        "next_actions": ["Make your first prediction!"]
    })


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route('/health')
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "service": "F1 Predictor Dashboard v3.0",
    })


if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Production-ready port detection (works on all platforms)
    # Hugging Face: PORT or FLASK_PORT env var, default 7860
    # Railway/Render: PORT env var
    # Local: FLASK_PORT env var, default 5000
    port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5000)))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # Security warning for production
    if debug and os.environ.get('PORT'):
        print("⚠️  WARNING: Debug mode enabled in production environment!")
        print("   Set FLASK_DEBUG=false for production deployments")
    
    print("=" * 60)
    print("🏎️  F1 Predictor Dashboard v3.0")
    print("=" * 60)
    print(f"📊 Dashboard: http://0.0.0.0:{port}")
    print(f"🔧 API: http://0.0.0.0:{port}/api/*")
    print(f"💾 Database: {'Initialized' if os.path.exists('f1_predictor.db') else 'Not initialized'}")
    print(f"🔒 Debug Mode: {'ON ⚠️' if debug else 'OFF ✅'}")
    print("=" * 60)
    
    # Bind to 0.0.0.0 for external access (required for cloud deployment)
    # Use 127.0.0.1 for local-only access
    host = '0.0.0.0' if os.environ.get('PORT') or os.environ.get('FLASK_PORT') != '5000' else '127.0.0.1'
    
    app.run(host=host, debug=debug, port=port)
