"""
API v1 integration tests — FastAPI minimal.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_v1_races(client):
    r = client.get("/api/v1/races")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 23
    assert r.headers.get("X-Request-ID") or r.headers.get("x-request-id")

def test_legacy_races_removed(client):
    r = client.get("/dashboard/api/races")
    assert r.status_code == 404

def test_v1_predict(client):
    r = client.post("/api/v1/predictions", json={"race_id":"au","session_type":"race","simulation_count":500})
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "success"
    assert "predictions" in j
    assert "winner" in j["predictions"]
    assert r.headers.get("X-Prediction-Latency") or r.headers.get("x-prediction-latency")
    assert r.headers.get("X-Request-ID") or r.headers.get("x-request-id")

def test_legacy_predict_removed(client):
    r = client.post("/dashboard/api/predict-session", json={"race_id":"au","session_type":"race","simulation_count":500})
    assert r.status_code == 404

def test_v1_standings(client):
    for path in ["/api/v1/standings/drivers", "/api/v1/standings/constructors"]:
        r = client.get(path)
        assert r.status_code == 200

def test_v1_h2h(client):
    r = client.get("/api/v1/h2h/drivers")
    assert r.status_code == 200
    r = client.post("/api/v1/h2h/compare", json={"driver_a":"VER","driver_b":"HAM"})
    assert r.status_code == 200
    j = r.json()
    assert "win_probability" in j

def test_v1_constructors(client):
    for p in ["/api/v1/constructors/teams","/api/v1/constructors/power-rankings"]:
        assert client.get(p).status_code == 200

def test_v1_analytics(client):
    assert client.get("/api/v1/analytics/accuracy").status_code == 200
    assert client.get("/api/v1/analytics/feature-weights").status_code == 200
    assert client.get("/api/v1/analytics/targets").status_code == 200
    r = client.post("/api/v1/analytics/feature-weights", json={"chaos_level": 42})
    assert r.status_code == 200

def test_v1_reports_export(client):
    pred = client.post("/api/v1/predictions", json={"race_id":"au","session_type":"race","simulation_count":200}).json()
    r = client.post("/api/v1/reports/export", json={"race_id":"au","session":"race","format":"json","predictions": pred["predictions"]})
    assert r.status_code == 200

def test_error_contract(client):
    r = client.post("/api/v1/predictions", json={})
    assert r.status_code == 400
    j = r.json()
    assert "error" in j
    assert "code" in j["error"]
    assert "request_id" in j["error"]

def test_openapi(client):
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    assert r.json()["openapi"].startswith("3.")

def test_health(client):
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200

def test_docs(client):
    assert client.get("/docs").status_code == 200
