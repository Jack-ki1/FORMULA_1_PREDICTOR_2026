"""
Startup-time database checks.

Schema creation/upgrades are Alembic's job (`alembic upgrade head`, run in
CI before each deploy — see /alembic and .github/workflows/ci.yml), not
something the app does to itself on import. This module is now just a
thin health-check wrapper kept for backwards-compat call sites
(routers/health.py, routers/status.py).
"""
from database.db import verify_connection

# Backwards-compatible name used elsewhere in the codebase.
verify_database_connection = verify_connection
