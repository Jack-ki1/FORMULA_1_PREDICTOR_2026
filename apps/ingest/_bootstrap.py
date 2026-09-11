"""
Import shim so apps/ingest scripts can reuse apps/api's engine/data/
database/config packages without duplicating or pip-installing them
separately. Every ingest script does:

    import _bootstrap  # noqa: F401  (must be first import)

before importing anything from engine/data/database/config.
"""
import os
import sys

_API_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "api"))
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)
