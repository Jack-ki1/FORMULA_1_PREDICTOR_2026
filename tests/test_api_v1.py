"""
API v1 + legacy dual-run integration tests.
"""
import pytest
from dashboard.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_v1_races(client):
    r = client.get("/api/v1/races")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 23
    assert r.headers.get("X-Request-ID")

def test_legacy_races_still_works(client):
    r = client.get("/dashboard/api/races")
    assert r.status_code == 200

def test_v1_predict(client):
    r = client.post("/api/v1/predictions", json={"race_id":"au","session_type":"race","simulation_count":500})
    assert r.status_code == 200
    j = r.get_json()
    assert j["status"] == "success"
    assert "predictions" in j
    assert "winner" in j["predictions"]
    assert r.headers.get("X-Prediction-Latency")
    assert r.headers.get("X-Request-ID")

def test_legacy_predict_still_works(client):
    r = client.post("/dashboard/api/predict-session", json={"race_id":"au","session_type":"race","simulation_count":500})
    assert r.status_code == 200

def test_v1_standings(client):
    for path in ["/api/v1/standings/drivers", "/api/v1/standings/constructors"]:
        r = client.get(path)
        assert r.status_code == 200

def test_v1_h2h(client):
    r = client.get("/api/v1/h2h/drivers")
    assert r.status_code == 200
    r = client.post("/api/v1/h2h/compare", json={"driver_a":"VER","driver_b":"HAM"})
    assert r.status_code == 200
    j = r.get_json()
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
    # need a prediction first
    pred = client.post("/api/v1/predictions", json={"race_id":"au","session_type":"race","simulation_count":200}).get_json()
    r = client.post("/api/v1/reports/export", json={"race_id":"au","session":"race","format":"json","predictions": pred["predictions"]})
    assert r.status_code == 200

def test_error_contract(client):
    r = client.post("/api/v1/predictions", json={})
    assert r.status_code == 400
    j = r.get_json()
    assert "error" in j
    assert "code" in j["error"]
    assert "request_id" in j["error"]

def test_openapi(client):
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    assert r.get_json()["openapi"] == "3.0.0"

def test_health(client):
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200
