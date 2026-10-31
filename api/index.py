"""Vercel serverless entrypoint: serves the FastAPI app from ../backend on every /api/* route."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from main import app  # noqa: E402,F401  (Vercel looks for the ASGI variable named `app`)
