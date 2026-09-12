"""
Main entry point for F1 Predictor 2026.
Boots Flask app + background schedulers as specified in build plan.
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from dashboard.app import create_app
from data.live_updater import start_live_updater
from database.init import initialize_database


def main():
    """Main entry point - boots Flask app + background schedulers."""
    print("=" * 60)
    print("F1 PREDICTOR 2026")
    print("=" * 60)
    
    # Initialize directories (done automatically in settings init)
    print("Initializing directories...")
    print("[OK] Directories initialized")
    
    # Initialize database
    print("Initializing database...")
    initialize_database()
    print("[OK] Database initialized")
    
    # Start background live updater
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
    
    # Create Flask app
    print("Creating Flask application...")
    app = create_app()
    print("[OK] Flask application created")
    
    # Run Flask app
    print(f"\nStarting Flask server on {settings.FLASK_HOST}:{settings.FLASK_PORT}...")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Season: {settings.SEASON_YEAR}")
    print("=" * 60)
    
    try:
        app.run(
            host=settings.FLASK_HOST,
            port=settings.FLASK_PORT,
            debug=settings.DEBUG,
            use_reloader=False,  # Don't use reloader in production
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
        print("Stopping live updater...")
        from data.live_updater import stop_live_updater
        stop_live_updater()
        print("[OK] Live updater stopped")
        print("[OK] F1 Predictor 2026 stopped")
    except Exception as e:
        print(f"\n[ERROR] Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()