"""
Shared pytest fixtures.

Points the whole test session at a throwaway SQLite file (never the
real f1_predictions.db dev database) and creates the schema directly
from the models rather than running Alembic — fast, and exercises the
same models Alembic's migration was generated from.
"""
import os
import tempfile

os.environ.setdefault("AUTH_SYNC_SECRET", "test-sync-secret")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

import pytest  # noqa: E402

from database.db import create_all_for_tests  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _setup_test_db():
    create_all_for_tests()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """A signed-in user's Authorization header, for tests that need one."""
    r = client.post(
        "/api/auth/sync-user",
        json={
            "provider": "github",
            "provider_account_id": "test-user-1",
            "email": "test@example.com",
            "display_name": "Test User",
        },
        headers={"x-sync-secret": os.environ["AUTH_SYNC_SECRET"]},
    )
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}
