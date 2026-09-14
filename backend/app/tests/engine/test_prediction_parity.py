"""
Prediction parity: engine generate_prediction vs v1 API must match within tolerance.
"""
import json, pathlib, pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.app.engine.predictor import generate_prediction

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "golden"
if not FIXTURES.exists():
    FIXTURES = pathlib.Path("tests/fixtures/golden")
if not FIXTURES.exists():
    FIXTURES = pathlib.Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "golden"

@pytest.fixture(scope="module")
def app_client():
    app = create_app()
    return TestClient(app)

def test_golden_fixtures_exist():
    assert FIXTURES.exists()
    files = list(FIXTURES.glob("*.json"))
    assert len(files) >= 3

def test_parity_against_fixtures(app_client):
    for f in FIXTURES.glob("*.json"):
        payload = json.loads(f.read_text())
        inp = payload["input"]
        direct = generate_prediction(**{**inp, "ai_config":{"ai_mode":"normal"}})
        r = app_client.post("/api/v1/predictions", json={**inp, "ai_mode":"normal"})
        assert r.status_code == 200
        via_api = r.json()
        assert direct["race_id"] == via_api["race_id"]
        assert direct["session_type"] == via_api["session_type"]
        dw = direct["winner_probabilities"]
        aw = via_api["winner_probabilities"]
        assert set(dw.keys()) == set(aw.keys())
        assert abs(sum(dw.values())-1.0) < 0.05
        assert abs(sum(aw.values())-1.0) < 0.05
        assert set(direct["predictions"].keys()) == set(via_api["predictions"].keys())
        for tid in direct["predictions"]:
            d_pred = direct["predictions"][tid]["predictions"]
            a_pred = via_api["predictions"][tid]["predictions"]
            assert len(d_pred) == len(a_pred)
            d_top = d_pred[0]["driver_code"]
            a_top = a_pred[0]["driver_code"]
            d_codes = [p["driver_code"] for p in d_pred[:5]]
            assert a_top in d_codes or d_top in [p["driver_code"] for p in a_pred[:5]]

def test_manual_grid_parity(app_client):
    grid = {"VER":1,"HAM":2,"NOR":3}
    direct = generate_prediction("au","race", grid_positions=grid, simulation_count=500, ai_config={"ai_mode":"normal"})
    r = app_client.post("/api/v1/predictions", json={"race_id":"au","session_type":"race","grid_positions": grid,"simulation_count":500})
    assert r.status_code==200
    via = r.json()
    assert via["grid_positions"]["VER"]==1
    assert via["grid_positions"]["HAM"]==2
    assert direct["grid_positions"]["VER"]==1
