"""
Vercel serverless entry point for F1 Predictor 2026.
This file is required by Vercel's FastAPI integration.
It wraps the main application for serverless deployment.
"""
import sys
import os

# Ensure repo root is on sys.path
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from main module
from backend.app import create_app

# Create the app instance - Vercel expects 'app' variable
app = create_app()

# Initialize database on cold start
try:
    from backend.app.database.init import initialize_database
    initialize_database()
except Exception as e:
    print(f"Database initialization note: {e}")

# Note: Background schedulers (live_updater) are disabled in serverless
# Vercel Functions are stateless and ephemeral - no long-running processes
print("F1 Predictor 2026 - Vercel serverless deployment")
print("Note: Live updater disabled in serverless environment")
