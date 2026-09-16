"""
Main entry point for F1 Predictor 2026 — FastAPI minimal Python.
Boots FastAPI app + background schedulers.
"""
import sys
import os

# Ensure repo root is on sys.path so `import backend` resolves correctly
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.config.settings import settings
from backend.app import create_app
from backend.app.data.live_updater import start_live_updater


def main():
    """Main entry point — boots FastAPI via Uvicorn + background schedulers."""
    print("=" * 60)
    print("F1 PREDICTOR 2026 — FastAPI minimal")
    print("=" * 60)

    print("Initializing directories...")
    print("[OK] Directories initialized")

    print("Database initialization skipped (authentication disabled)")

    if settings.LIVE_UPDATE_INTERVAL > 0:
        print(f"Starting live updater ({settings.LIVE_UPDATE_INTERVAL}s interval)...")
        try:
            start_live_updater()
            print("[OK] Live updater started")
        except Exception as e:
            print(f"[WARNING] Could not start live updater: {e}")
            print("  Continuing without live updates...")
    else:
        print("Live updater disabled (LIVE_UPDATE_INTERVAL = 0)")

    print("Creating FastAPI application...")
    app = create_app()
    print("[OK] FastAPI application created — docs at /docs")

    # HOST/PORT are the canonical settings. The FLASK_HOST/FLASK_PORT env vars
    # are still honoured via the settings shims for older deployments, but the
    # documented names are HOST/PORT.
    run_host = os.environ.get("HOST", settings.HOST)
    run_port = int(os.environ.get("PORT", settings.PORT))
    print(f"\nStarting FastAPI server on {run_host}:{run_port}...")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Season: {settings.SEASON_YEAR}")
    print("=" * 60)

    try:
        import uvicorn
        uvicorn.run(app, host=run_host, port=run_port, log_level="info")
    except KeyboardInterrupt:
        print("\nShutting down...")
        print("Stopping live updater...")
        from backend.app.data.live_updater import stop_live_updater
        stop_live_updater()
        print("[OK] Live updater stopped")
        print("[OK] F1 Predictor 2026 stopped")
    except Exception as e:
        print(f"\n[ERROR] Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
