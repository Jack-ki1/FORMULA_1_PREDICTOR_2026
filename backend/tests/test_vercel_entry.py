"""The Vercel function loads backend code from a sibling folder; make sure that wiring works from the repo root."""
import runpy
from pathlib import Path

from fastapi.testclient import TestClient


def test_api_index_exposes_app_and_routes():
    ns = runpy.run_path(str(Path(__file__).resolve().parents[2] / "api" / "index.py"))
    c = TestClient(ns["app"])
    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/api/v1/races").status_code == 200
    assert c.get("/api/docs").status_code == 200
