"""
Vercel Python Functions entrypoint.

Deploy apps/api as its own Vercel project (Project Settings → Root
Directory: apps/api). Vercel's Python runtime looks for files under an
/api directory by convention; this just re-exports the real FastAPI app
from ../main.py so there's exactly one app definition, not a duplicate.

vercel.json's catch-all rewrite sends every request here and lets
FastAPI's own router handle the path — Vercel's file-based routing
isn't used beyond that one rewrite.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402,F401
