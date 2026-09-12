"""
Tests for dashboard blueprints and API endpoints.
"""
import pytest
from dashboard.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_races(client):
    """Test /dashboard/api/races returns 2026 calendar."""
    response = client.get("/dashboard/api/races")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 20


def test_api_predict_session_race(client):
    """Test /dashboard/api/predict-session with race payload."""
    payload = {
        "race_id": "bahrain",
        "session_type": "race",
        "weather": "dry",
        "simulation_count": 500
    }
    response = client.post("/dashboard/api/predict-session", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "predictions" in data
    assert "winner" in data["predictions"]
    assert "podium" in data["predictions"]
    assert "points" in data["predictions"]
    assert "grid_positions" in data


def test_api_predict_session_qualifying(client):
    """Test /dashboard/api/predict-session with qualifying payload."""
    payload = {
        "race_id": "bahrain",
        "session_type": "qualifying",
        "weather": "dry"
    }
    response = client.post("/dashboard/api/predict-session", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "q3" in data["predictions"]


def test_api_ai_chat_validation(client):
    """Test /dashboard/api/ai-chat validates empty input."""
    response = client.post("/dashboard/api/ai-chat", json={})
    assert response.status_code == 400


def test_h2h_compare(client):
    """Test /h2h/api/compare endpoint."""
    response = client.post("/h2h/api/compare", json={"driver_a": "VER", "driver_b": "HAM"})
    assert response.status_code == 200
    data = response.get_json()
    assert "win_probability" in data
    assert "driver_a" in data
    assert "driver_b" in data


def test_reports_export_csv(client):
    """Test /reports/api/export endpoint for CSV."""
    payload = {
        "race_id": "bahrain",
        "session": "race",
        "target_id": "winner",
        "format": "csv",
        "predictions": {
            "winner": {
                "predictions": [
                    {"driver_code": "VER", "probability": 0.45, "percentage": 45.0},
                    {"driver_code": "NOR", "probability": 0.25, "percentage": 25.0}
                ]
            }
        }
    }
    response = client.post("/reports/api/export", json=payload)
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("Content-Type", "")
