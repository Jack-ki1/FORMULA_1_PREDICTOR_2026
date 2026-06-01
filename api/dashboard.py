"""
FastAPI Dashboard - Replaces Flask dashboard (Section 5.1).

Serves HTML templates with Jinja2 for F1 prediction visualization.
All endpoints are now unified under FastAPI.

Usage:
    py main.py dashboard --port 8080
"""

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="F1 Predictor Dashboard")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files if they exist
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass  # No static directory yet


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    from data.circuit_data import get_all_circuits
    from data.calendar_2026 import CALENDAR_2026
    
    circuits = get_all_circuits()
    upcoming_races = [r for r in CALENDAR_2026 if r["status"] == "upcoming"][:5]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "circuits": circuits,
        "upcoming_races": upcoming_races,
        "title": "F1 Prediction Dashboard"
    })


@app.get("/api/dashboard/predict/{circuit_id}")
async def dashboard_predict(circuit_id: str):
    """AJAX endpoint for dashboard predictions."""
    from engine.predictor import predict, PredictionRequest
    from api.routes import _result_to_response
    
    try:
        request = PredictionRequest(
            circuit_id=circuit_id,
            n_simulations=3000,
            output_format="summary",
        )
        result = predict(request)
        return _result_to_response(result)
    except Exception as e:
        logger.error(f"Dashboard prediction failed: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
