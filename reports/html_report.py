"""
HTML Report Generator.

Generates a self-contained single-file HTML race prediction report
using Jinja2 templating and inline Chart.js for visualisations.
"""

import os
import json
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from engine.predictor import predict, PredictionRequest
from config.settings import REPORT_OUTPUT_DIR


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


def generate_report(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = 5000,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a full HTML prediction report.

    Returns the path to the generated file.
    """
    result = predict(PredictionRequest(
        circuit_id=circuit_id,
        rain_probability=rain_probability,
        n_simulations=n_simulations,
    ))

    meta = result["meta"]
    predictions = result["predictions"]

    # Attach team colour for template
    for p in predictions:
        p["team_colour"] = TEAM_COLOURS.get(p["team"], "#888888")

    # Chart.js data payloads
    top8 = predictions[:8]
    chart_data = {
        "labels": [p["driver"].split()[-1] for p in top8],
        "win_probs": [p["win_pct"] for p in top8],
        "top3_probs": [p["top3_pct"] for p in top8],
        "colours": [TEAM_COLOURS.get(p["team"], "#888") for p in top8],
    }

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")

    html = template.render(
        meta=meta,
        predictions=predictions,
        chart_data=json.dumps(chart_data),
        podium=result["podium_predictions"],
        surprises=result["likely_top_surprises"],
    )

    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    if output_path is None:
        output_path = os.path.join(REPORT_OUTPUT_DIR, f"{circuit_id}_prediction_report.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
