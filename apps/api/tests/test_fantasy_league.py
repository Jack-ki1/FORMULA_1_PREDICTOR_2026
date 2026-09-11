"""Tests for auth (sync-user/me) and the fantasy league feature (picks,
leaderboard, per-user settings) — all new in the FastAPI migration."""
import os

from data.calendar_2026 import CALENDAR_2026

UPCOMING_RACE_ID = next(r["id"] for r in CALENDAR_2026 if r["status"] != "completed")
COMPLETED_RACE_ID = next(r["id"] for r in CALENDAR_2026 if r["status"] == "completed")


def test_sync_user_requires_correct_secret(client):
    response = client.post(
        "/api/auth/sync-user",
        json={"provider": "github", "provider_account_id": "x", "display_name": "X"},
        headers={"x-sync-secret": "wrong-secret"},
    )
    assert response.status_code == 403


def test_sync_user_and_me(client):
    r = client.post(
        "/api/auth/sync-user",
        json={"provider": "github", "provider_account_id": "abc123", "display_name": "Charlie", "email": "c@example.com"},
        headers={"x-sync-secret": os.environ["AUTH_SYNC_SECRET"]},
    )
    assert r.status_code == 200
    token = r.json()["token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["display_name"] == "Charlie"


def test_sync_user_upserts_on_repeat_login(client):
    body = {"provider": "github", "provider_account_id": "same-id", "display_name": "First Name"}
    r1 = client.post("/api/auth/sync-user", json=body, headers={"x-sync-secret": os.environ["AUTH_SYNC_SECRET"]})
    body["display_name"] = "Updated Name"
    r2 = client.post("/api/auth/sync-user", json=body, headers={"x-sync-secret": os.environ["AUTH_SYNC_SECRET"]})
    assert r1.json()["user_id"] == r2.json()["user_id"]  # same user, not a duplicate
    assert r2.json()["display_name"] == "Updated Name"


def test_picks_require_auth(client):
    response = client.post(
        "/api/picks",
        json={"race_id": UPCOMING_RACE_ID, "session": "race", "target": "winner", "driver_id": "VER"},
    )
    assert response.status_code == 401


def test_submit_and_read_pick(client, auth_headers):
    response = client.post(
        "/api/picks",
        json={"race_id": UPCOMING_RACE_ID, "session": "race", "target": "winner", "driver_id": "ver"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["driver_id"] == "VER"  # normalized to uppercase

    mine = client.get("/api/picks", headers=auth_headers)
    assert mine.status_code == 200
    assert any(p["race_id"] == UPCOMING_RACE_ID for p in mine.json())


def test_resubmitting_a_pick_updates_it_not_duplicates(client, auth_headers):
    body = {"race_id": UPCOMING_RACE_ID, "session": "qualifying", "target": "pole", "driver_id": "VER"}
    client.post("/api/picks", json=body, headers=auth_headers)
    body["driver_id"] = "NOR"
    client.post("/api/picks", json=body, headers=auth_headers)

    mine = client.get("/api/picks", params={"race_id": UPCOMING_RACE_ID}, headers=auth_headers).json()
    pole_picks = [p for p in mine if p["target"] == "pole"]
    assert len(pole_picks) == 1
    assert pole_picks[0]["driver_id"] == "NOR"


def test_cannot_pick_a_completed_race(client, auth_headers):
    response = client.post(
        "/api/picks",
        json={"race_id": COMPLETED_RACE_ID, "session": "race", "target": "winner", "driver_id": "VER"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_pick_rejects_unknown_driver(client, auth_headers):
    response = client.post(
        "/api/picks",
        json={"race_id": UPCOMING_RACE_ID, "session": "race", "target": "winner", "driver_id": "ZZZ"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_leaderboard_lists_signed_in_users(client, auth_headers):
    client.post(
        "/api/picks",
        json={"race_id": UPCOMING_RACE_ID, "session": "race", "target": "fastest_lap", "driver_id": "VER"},
        headers=auth_headers,
    )
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "display_name" in response.json()[0]


def test_user_settings_round_trip(client, auth_headers):
    payload = {
        "chaos_level": 80, "wet_influence": 30, "reliability_influence": 60,
        "strategy_aggressiveness": 40, "grid_weight": 55,
    }
    save = client.post("/api/settings/feature-weights", json=payload, headers=auth_headers)
    assert save.status_code == 200
    assert save.json()["status"] == "saved"

    read = client.get("/api/settings/feature-weights", headers=auth_headers)
    assert read.status_code == 200
    assert read.json()["scope"] == "user"
    assert read.json()["chaos_level"] == 80
