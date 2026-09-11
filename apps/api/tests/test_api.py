"""
API-layer tests — replaces the old Flask-era test_dashboard_blueprints.py.
Hits the FastAPI app through TestClient against the real /api/* routes.
"""
from data.calendar_2026 import CALENDAR_2026

UPCOMING_RACE_ID = next(r["id"] for r in CALENDAR_2026 if r["status"] != "completed")


def test_api_races(client):
    response = client.get("/api/races")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 20


def test_get_predictions_computes_and_then_caches(client):
    """First call computes on demand; second call reads the row it
    just persisted (see PLAN.md §3 — predictions are precomputed in
    production, computed-on-demand only as a standalone fallback)."""
    r1 = client.get(f"/api/predictions/{UPCOMING_RACE_ID}", params={"session_type": "race"})
    assert r1.status_code == 200
    assert r1.json()["source"] == "computed_on_demand"

    r2 = client.get(f"/api/predictions/{UPCOMING_RACE_ID}", params={"session_type": "race"})
    assert r2.status_code == 200
    assert r2.json()["source"] == "precomputed"
    assert "winner_probabilities" in r2.json()


def test_get_predictions_unknown_race_404(client):
    response = client.get("/api/predictions/not-a-real-race")
    assert response.status_code == 404


def test_recompute_what_if(client):
    payload = {"session_type": "race", "weather": "wet", "simulation_count": 300}
    response = client.post(f"/api/predictions/{UPCOMING_RACE_ID}/recompute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["source"] == "what_if"
    assert "winner" in data["predictions"]


def test_ai_chat_validation(client):
    response = client.post("/api/ai-chat", json={"message": ""})
    assert response.status_code == 400


def test_h2h_compare(client):
    response = client.post("/api/h2h/compare", json={"driver_a": "VER", "driver_b": "HAM"})
    assert response.status_code == 200
    data = response.json()
    assert "win_probability" in data
    assert "driver_a" in data
    assert "driver_b" in data


def test_h2h_compare_unknown_driver(client):
    response = client.post("/api/h2h/compare", json={"driver_a": "VER", "driver_b": "ZZZ"})
    assert response.status_code == 404


def test_constructors_teams(client):
    response = client.get("/api/constructors/teams")
    assert response.status_code == 200
    assert len(response.json()) >= 10


def test_standings_drivers(client):
    response = client.get("/api/standings/drivers")
    assert response.status_code == 200
    assert "data" in response.json()


def test_reports_export_csv(client):
    payload = {
        "race_id": UPCOMING_RACE_ID,
        "session": "race",
        "target_id": "winner",
        "format": "csv",
        "predictions": {
            "winner": {
                "predictions": [
                    {"driver_code": "VER", "probability": 0.45, "percentage": 45.0},
                    {"driver_code": "NOR", "probability": 0.25, "percentage": 25.0},
                ]
            }
        },
    }
    response = client.post("/api/reports/export", json=payload)
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_settings_feature_weights_anonymous_not_persisted(client):
    payload = {
        "chaos_level": 60, "wet_influence": 40, "reliability_influence": 50,
        "strategy_aggressiveness": 55, "grid_weight": 55,
    }
    response = client.post("/api/settings/feature-weights", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "not_persisted"
