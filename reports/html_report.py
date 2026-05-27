"""
Enhanced HTML Report Generator — v3.

Features:
  - Modern, responsive design with dark theme
  - Proper position cascading (1,2,3,4,5... not 2,2,3,3...)
  - Interactive charts with Chart.js
  - Driver vs Circuit historical performance cards
  - Probability distribution sparklines
  - Team color coding
  - Mobile-responsive layout
  - Export-ready formatting
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from engine.predictor import predict, PredictionRequest
from config.settings import REPORT_OUTPUT_DIR
from data.driver_traits_database import get_driver_trait

TEMPLATE_DIR = Path(__file__).parent / "templates"

TEAM_COLOURS: dict = {
    "mercedes":     "#00D2BE",
    "mclaren":      "#FF8000",
    "ferrari":      "#E8002D",
    "red_bull":     "#3671C6",
    "alpine":       "#FF87BC",
    "williams":     "#005AFF",
    "haas":         "#B6BABD",
    "racing_bulls": "#6692FF",
    "audi":         "#C00110",
    "aston_martin": "#358C75",
    "cadillac":     "#BE3445",
}


def _assign_positions(predictions: List[Dict]) -> List[Dict]:
    """
    Assign proper sequential positions (1,2,3,4,5...) based on predicted_position.
    
    This ensures no duplicate positions like 2,2,3,3,4,4.
    Ties are broken by win_probability (higher win prob gets better position).
    """
    # Sort by predicted_position, then by win probability as tiebreaker
    sorted_preds = sorted(
        predictions, 
        key=lambda x: (x.get('predicted_position', 999), -x.get('win_probability', 0))
    )
    
    # Assign sequential positions
    for idx, pred in enumerate(sorted_preds, start=1):
        pred['display_position'] = idx
    
    return sorted_preds


def _enrich_with_circuit_data(predictions: List[Dict], circuit_id: str) -> List[Dict]:
    """
    Add circuit-specific historical performance data to each driver's prediction.
    """
    for pred in predictions:
        driver_id = pred.get('driver_id')
        if not driver_id:
            continue
        
        # Get circuit affinity data
        circuit_data = get_driver_trait(driver_id, 'circuit_affinity', circuit_id)
        
        if circuit_data:
            pred['circuit_history'] = {
                'avg_finish': circuit_data.get('avg_finish', None),
                'wins': circuit_data.get('wins', 0),
                'podiums': circuit_data.get('podiums', 0),
                'poles': circuit_data.get('poles', 0),
                'confidence_rating': circuit_data.get('confidence_rating', None),
                'races_completed': circuit_data.get('races_completed', 0),
            }
        else:
            pred['circuit_history'] = None
    
    return predictions


def format_number(value):
    """Format large numbers with comma separators."""
    if isinstance(value, int):
        return f"{value:,}"
    elif isinstance(value, float):
        return f"{value:,.0f}"
    return str(value)


def clamp(value, min_val=None, max_val=None):
    """Clamp a value between min and max bounds."""
    if min_val is not None and value < min_val:
        return min_val
    if max_val is not None and value > max_val:
        return max_val
    return value


def generate_report(
    circuit_id: str,
    rain_probability: float = 0.0,
    n_simulations: int = 50000,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate an enhanced HTML prediction report for a given circuit.
    
    Args:
        circuit_id: Circuit identifier (e.g., 'canada', 'monaco')
        rain_probability: Probability of rain (0.0-1.0)
        n_simulations: Number of Monte Carlo simulations
        output_path: Optional custom output path
    
    Returns:
        Path to the generated HTML file
    """
    
    # Get predictions using the main predict() function
    result = predict(PredictionRequest(
        circuit_id=circuit_id,
        rain_probability=rain_probability,
        n_simulations=n_simulations,
        output_format="full",  # Get raw data too
    ))
    
    meta = result["meta"]
    predictions = result["predictions"]
    
    # Add sc_probability alias for template compatibility
    meta["sc_probability"] = meta.get("safety_car_probability", 0.0)
    
    # Get circuit details from calendar
    from data.calendar_2026 import CALENDAR_2026
    race_info = None
    for race in CALENDAR_2026:
        if race["circuit"] == circuit_id:
            race_info = race
            break
    
    # Enrich meta with additional race details
    if race_info:
        meta["race_name"] = race_info["name"]
        meta["round_number"] = race_info["round"]
        meta["circuit_name"] = meta.get("circuit", "")
    else:
        meta["race_name"] = meta.get("circuit", "").title() + " Grand Prix"
        meta["round_number"] = "?"
        meta["circuit_name"] = meta.get("circuit", "")
    
    # If we have raw data, use it for richer information
    if result.get("raw"):
        raw_predictions = result["raw"]["predictions"]
        # Merge raw data with processed predictions
        for pred in predictions:
            driver_id = pred.get("driver")
            for raw_pred in raw_predictions:
                if raw_pred["driver_name"] == driver_id:
                    pred["driver_id"] = raw_pred["driver_id"]
                    pred["win_probability"] = raw_pred["win_probability"]
                    pred["top3_probability"] = raw_pred["top3_probability"]
                    pred["top10_probability"] = raw_pred["top10_probability"]
                    pred["dnf_probability"] = raw_pred["dnf_probability"]
                    pred["teammate_beat_prob"] = raw_pred["teammate_beat_prob"]
                    pred["composite_score"] = raw_pred["composite_score"]
                    pred["position_distribution"] = raw_pred.get("position_distribution", [0] * 22)
                    break
    
    # FIX: Assign proper sequential positions
    predictions = _assign_positions(predictions)
    
    # ENHANCEMENT: Add circuit-specific historical data
    predictions = _enrich_with_circuit_data(predictions, circuit_id)
    
    # Attach team colour for template use
    for p in predictions:
        p["team_colour"] = TEAM_COLOURS.get(p.get("team", "").lower(), "#888888")
    
    # Prepare chart data (top 10 drivers)
    top10 = predictions[:10]
    chart_data = {
        "labels": [p["driver"].split()[-1] if " " in p.get("driver", "") else p.get("driver", "") for p in top10],
        "full_names": [p.get("driver", "") for p in top10],
        "win_probs": [round(p.get("win_probability", 0) * 100, 1) for p in top10],
        "top3_probs": [round(p.get("top3_probability", 0) * 100, 1) for p in top10],
        "top10_probs": [round(p.get("top10_probability", 0) * 100, 1) for p in top10],
        "dnf_probs": [round(p.get("dnf_probability", 0) * 100, 1) for p in top10],
        "teammate_beat_probs": [round(p.get("teammate_beat_prob", 0) * 100, 1) for p in top10],
        "composite_scores": [round(p.get("composite_score", 0) * 100, 1) for p in top10],
        "colours": [p.get("team_colour", "#888") for p in top10],
        "teams": [p.get("team", "") for p in top10],
        "position_distributions": [p.get("position_distribution", [0] * 22) for p in top10],
    }
    
    # Full predictions JSON for interactive features
    all_pred_for_js = []
    for p in predictions:
        pred_data = {
            "driver_id": p.get("driver_id", ""),
            "driver_name": p.get("driver", ""),
            "team": p.get("team", ""),
            "display_position": p.get("display_position", 0),
            "win_pct": round(p.get("win_probability", 0) * 100, 1),
            "top3_pct": round(p.get("top3_probability", 0) * 100, 1),
            "top10_pct": round(p.get("top10_probability", 0) * 100, 1),
            "dnf_pct": round(p.get("dnf_probability", 0) * 100, 1),
            "teammate_beat_pct": round(p.get("teammate_beat_prob", 0) * 100, 1),
            "composite_score": round(p.get("composite_score", 0) * 100 if isinstance(p.get("composite_score"), float) else 0, 1),
            "team_colour": p.get("team_colour", "#888"),
            "position_distribution": p.get("position_distribution", [0] * 22),
            "circuit_history": p.get("circuit_history"),
        }
        all_pred_for_js.append(pred_data)
    
    # Create podium data structure compatible with template
    podium_data = []
    for p in predictions[:3]:
        podium_data.append({
            "driver_name": p.get("driver", ""),
            "win_probability": p.get("win_probability", 0),
            "team": p.get("team", ""),
        })
    
    # Load and render template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    env.filters['format_number'] = format_number
    env.filters['clamp'] = clamp
    template = env.get_template("report.html")
    
    html = template.render(
        meta=meta,
        predictions=predictions,
        chart_data=json.dumps(chart_data),
        all_predictions_json=json.dumps(all_pred_for_js),
        podium=podium_data,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    
    # Save report
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    if output_path is None:
        output_path = os.path.join(REPORT_OUTPUT_DIR, f"{circuit_id}_prediction_report.html")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return output_path


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = ["generate_report", "TEAM_COLOURS"]
