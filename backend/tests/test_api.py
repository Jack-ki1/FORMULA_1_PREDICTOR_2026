from fastapi.testclient import TestClient

from main import app
from app import provider

c = TestClient(app)


def test_health_and_meta():
    assert c.get("/health").json() == {"status": "ok"}
    m = c.get("/api/v1/meta").json()
    assert m["source"] == "seed" and m["as_of_round"] == 17


def test_races_and_next():
    races = c.get("/api/v1/races").json()
    assert len(races) >= 7 and races[0]["circuit"]["name"]
    nxt = c.get("/api/v1/races/next").json()
    assert nxt["status"] != "completed"


def test_prediction_contract():
    r = c.post("/api/v1/predictions", json={"sims": 1000, "weather": "dry", "race_id": "19"})
    assert r.status_code == 200
    j = r.json()
    assert j["race"]["name"].startswith("Mexico") and len(j["drivers"]) == 22
    assert len(j["qualifying"]) == 22 and sum(s["prob"] for s in j["strategies"]) == 100
    assert c.post("/api/v1/predictions", json={"sims": 5}).status_code == 422
    assert c.post("/api/v1/predictions", json={"race_id": "nope"}).status_code == 404


def test_standings_h2h_fantasy_search_recent():
    s = c.get("/api/v1/standings").json()
    assert s["drivers"][0]["code"] == "ANT" and s["constructors"][0]["points"] == 578
    h = c.get("/api/v1/h2h", params={"a": "ver", "b": "nor", "race_id": "19"}).json()
    assert h["a"]["points"] == 221 and h["b"]["points"] == 201
    assert c.get("/api/v1/h2h", params={"a": "VER", "b": "VER"}).status_code == 422
    f = c.get("/api/v1/fantasy/pool", params={"race_id": "19"}).json()
    assert len(f["optimal"]) == 5 and sum(p["price"] for p in f["pool"] if p["code"] in f["optimal"]) <= 100.01
    assert c.get("/api/v1/search", params={"q": "ham"}).json()["drivers"][0]["code"] == "HAM"
    assert c.get("/api/v1/recent").json()[-1]["next"] is True


ERGAST_RESULTS = {"RaceTable": {"Races": [
    {"round": "1", "Results": [{"position": "1", "Driver": {"code": "ANT"}}, {"position": "2", "Driver": {"code": "RUS"}}]},
    {"round": "1", "Results": [{"position": "3", "Driver": {"code": "VER"}}]},  # same race, second page
    {"round": "2", "Results": [{"position": "1", "Driver": {"code": "VER"}}, {"position": "2", "Driver": {"code": "ANT"}}]}]}}


def test_ergast_parsers():
    winners, fin = provider.parse_results([ERGAST_RESULTS])
    assert winners == {1: "ANT", 2: "VER"} and fin["VER"] == {1: 3, 2: 1}
    pages = [{"StandingsTable": {"StandingsLists": [{"round": "17", "DriverStandings": [
        {"position": "1", "points": "340", "wins": "8", "Driver": {"code": "ANT", "givenName": "Kimi", "familyName": "Antonelli"},
         "Constructors": [{"constructorId": "mercedes"}]}]}]}}]
    rnd, rows = provider.parse_driver_standings(pages)
    assert rnd == 17 and rows["ANT"]["points"] == 340 and rows["ANT"]["team"] == "mercedes"
    cal = provider.parse_calendar([{"RaceTable": {"Races": [{"round": "19", "raceName": "Mexico City Grand Prix", "date": "2026-11-01",
        "time": "20:00:00Z", "Circuit": {"circuitId": "rodriguez", "circuitName": "AHR", "Location": {"lat": "19.4", "long": "-99.09", "locality": "Mexico City", "country": "Mexico"}}}]}}], {})
    assert cal[0]["cc"] == "MX" and cal[0]["date_start"] == "2026-10-30"


def test_full_calendar_sessions_and_labels():
    races = c.get("/api/v1/races").json()
    assert len(races) == 23 and races[15]["name"] == "Bahrain Grand Prix in Malaysia" and races[15]["cc"] == "MY"
    mex = races[18]
    assert [s["key"] for s in mex["sessions"]] == ["FP1", "FP2", "FP3", "Q", "R"] and mex["labels"]["race_day"] == "Sunday"
    assert races[20]["labels"]["race_day"] == "Saturday" and races[14]["labels"]["race_day"] == "Saturday"  # Las Vegas, Baku
    assert [s["key"] for s in races[16]["sessions"]] == ["FP1", "SQ", "SPR", "Q", "R"] and races[16]["sprint"]  # Singapore sprint weekend
    assert races[22]["circuit"]["laps"] == 58


def test_sessions_and_manual_grid():
    body = {"race_id": "19", "sims": 1500, "weather": "dry"}
    prac = c.post("/api/v1/predictions", json={**body, "session": "practice"}).json()
    assert "pace_gap" in prac["drivers"][0] and prac["drivers"][0]["pace_gap"] >= 0
    q = c.post("/api/v1/predictions", json={**body, "session": "qualifying"}).json()
    assert q["drivers"][0]["reach_q3"] > 0.9 and abs(sum(d["pole"] for d in q["drivers"]) - 1) < 1e-9
    base = c.post("/api/v1/predictions", json=body).json()
    m = c.post("/api/v1/predictions", json={**body, "grid_mode": "manual", "grid": ["HAM", "ANT", "RUS"]}).json()
    assert m["grid_source"] == "manual" and m["grid_locked"] == 3
    ham = lambda j: next(d for d in j["drivers"] if d["code"] == "HAM")
    assert ham(m)["avg_grid"] < 1.01 and ham(m)["win"] > ham(base)["win"]
    assert c.post("/api/v1/predictions", json={**body, "grid_mode": "manual", "grid": ["HAM", "HAM"]}).status_code == 422
    assert c.post("/api/v1/predictions", json={**body, "grid_mode": "manual", "grid": ["XXX"]}).status_code == 422
    g = c.get("/api/v1/races/19/grid").json()
    assert len(g["by_form"]) == 22 and g["live"] is None


def test_engine_weights_change_results_and_admin_guard():
    body = {"race_id": "19", "sims": 3000, "weather": "dry", "seed": 5}
    a = c.post("/api/v1/predictions", json=body).json()["drivers"][0]["win"]
    b = c.post("/api/v1/predictions", json={**body, "chaos": 1.0}).json()["drivers"][0]["win"]
    assert b < a
    cfg = c.get("/api/v1/config").json()
    assert cfg["admin_enabled"] is False and cfg["cache_ttl"] > 0
    assert c.put("/api/v1/admin/config", json={"cache_ttl": 5}).status_code == 403


def test_admin_config_with_token(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "admin_token", "s3cret")
    assert c.get("/api/v1/admin/verify", headers={"x-admin-token": "bad"}).status_code == 401
    assert c.get("/api/v1/admin/verify", headers={"x-admin-token": "s3cret"}).json() == {"ok": True}
    r = c.put("/api/v1/admin/config", json={"cache_ttl": 120, "model_type": "monte_carlo"}, headers={"x-admin-token": "s3cret"})
    assert r.status_code == 200 and r.json()["cache_ttl"] == 120
    assert c.put("/api/v1/admin/config", json={"model_type": "nope"}, headers={"x-admin-token": "s3cret"}).status_code == 422
    c.put("/api/v1/admin/config", json={"cache_ttl": 600, "model_type": "monte_carlo_form"}, headers={"x-admin-token": "s3cret"})
