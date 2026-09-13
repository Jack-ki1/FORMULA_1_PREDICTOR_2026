"""
Flask application factory - main application entry point.
Registers all blueprints and configures the Flask app.
Implements Phase 1-4 of transformation_improvements.md:
- Service layer via backend/app/services
- Versioned /api/v1 contracts
- Legacy Jinja UI preserved for dual-run (old endpoints still active)
- Standardized error contract {error:{code,message,details,request_id}}
- Request-ID, security headers, CORS, observability
"""
import time
import uuid
import logging
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from config.settings import settings

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder='static')
    
    # Configure Flask app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    app.config['FLASK_ENV'] = settings.FLASK_ENV

    # Enable CORS. CORS_ORIGINS defaults to "*" (fine for local dev and the
    # docker-compose stack, where nginx/Vite proxy same-origin anyway). Set
    # it to a comma-separated allowlist in production if the frontend calls
    # this API cross-origin (Option B above).
    _cors_origins = settings.CORS_ORIGINS
    CORS(
        app,
        supports_credentials=True,
        origins=_cors_origins.split(',') if _cors_origins != '*' else '*',
    )

    # === Global middleware: request ID, rate limiting stub, timing ===
    @app.before_request
    def _before():
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g._start_time = time.time()
        # rate limiting stub (non-blocking unless exceeded)
        try:
            from backend.app.security.middleware import rate_limit_check
            blocked = rate_limit_check()
            if blocked:
                return blocked
        except Exception:
            pass

    @app.after_request
    def _after(response):
        # security headers
        try:
            from backend.app.security.middleware import add_security_headers
            response = add_security_headers(response)
        except Exception:
            pass
        # timing / observability
        if hasattr(g, "_start_time"):
            latency = time.time() - g._start_time
            response.headers["X-Response-Time"] = f"{latency:.3f}s"
            # prometheus latency could be recorded here
        # ensure request id echoed
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        return response

    # Register legacy Jinja/blueprint layer (preserved for dual-run)
    from dashboard.blueprints.landing import landing_bp
    from dashboard.blueprints.predictions import predictions_bp
    from dashboard.blueprints.standings import standings_bp
    from dashboard.blueprints.h2h import h2h_bp
    from dashboard.blueprints.constructors import constructors_bp
    from dashboard.blueprints.analytics_settings import analytics_settings_bp
    from dashboard.blueprints.reports import reports_bp

    app.register_blueprint(landing_bp)
    app.register_blueprint(predictions_bp, url_prefix='/dashboard')
    app.register_blueprint(standings_bp, url_prefix='/standings')
    app.register_blueprint(h2h_bp, url_prefix='/h2h')
    app.register_blueprint(constructors_bp, url_prefix='/constructors')
    app.register_blueprint(analytics_settings_bp, url_prefix='/analytics')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # === Register versioned /api/v1 API (new contract) ===
    # These coexist with legacy /dashboard/api/* during migration (Phase 3)
    try:
        from backend.app.api.routes.health import health_bp as v1_health_bp
        from backend.app.api.routes.races import races_bp as v1_races_bp
        from backend.app.api.routes.predictions import predictions_bp as v1_predictions_bp
        from backend.app.api.routes.standings import standings_bp as v1_standings_bp
        from backend.app.api.routes.h2h import h2h_bp as v1_h2h_bp
        from backend.app.api.routes.constructors import constructors_bp as v1_constructors_bp
        from backend.app.api.routes.analytics import analytics_bp as v1_analytics_bp
        from backend.app.api.routes.reports import reports_bp as v1_reports_bp
        from backend.app.api.routes.ai import ai_bp as v1_ai_bp
        from backend.app.api.routes.openapi import openapi_bp
        # all v1 blueprints declare their own /api/v1/* routes, mount at "/"
        for bp in [v1_health_bp, v1_races_bp, v1_predictions_bp, v1_standings_bp, v1_h2h_bp, v1_constructors_bp, v1_analytics_bp, v1_reports_bp, v1_ai_bp, openapi_bp]:
            app.register_blueprint(bp)
        logger.info("Registered /api/v1 blueprints")
    except Exception as e:
        logger.warning("Failed to register v1 blueprints: %s", e)

    # Optional: monitoring blueprint (Prometheus) if available
    try:
        from monitoring.blueprint import monitoring_bp
        app.register_blueprint(monitoring_bp)
    except Exception:
        pass
    
    # Add a direct route to /dashboard (without trailing slash) that redirects to /dashboard/
    @app.route('/dashboard')
    def dashboard_redirect():
        from flask import redirect
        return redirect('/dashboard/')

    # Health check endpoint (legacy)
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'version': '1.0.0'})

    # === Serve React frontend (built via `npm run build` in frontend/) on same port (5000) ===
    # The React SPA is built to `frontend/dist` (Vite, base: '/app/') and served at `/app` on the
    # same Flask port. This keeps a clear backend (Flask/python) + frontend (React/tsx/npm)
    # separation but removes the separate Vite dev server on 5173 — the only browsable
    # port is now 5000. Legacy Jinja pages (/, /dashboard/, /standings/ etc.) keep precedence;
    # React is available at /app, /app/dashboard, /app/standings ... and shares the same /api/v1.
    # If `frontend/dist` doesn't exist (fresh clone before `npm run build`), these routes 404
    # gracefully and the legacy UI + API still work.
    try:
        import pathlib as _pl
        from flask import send_from_directory
        _frontend_dist = _pl.Path(__file__).resolve().parent.parent / "frontend" / "dist"
        if _frontend_dist.is_dir():
            @app.route("/app")
            @app.route("/app/<path:path>")
            def _serve_frontend(path=""):
                # Serve built assets directly if they exist — hashed assets get long cache
                if path and (_frontend_dist / path).is_file():
                    # hashed assets (e.g. /app/assets/index-*.js) -> 1y immutable, index.html/sw.js -> no-cache
                    if path.startswith("assets/"):
                        return send_from_directory(str(_frontend_dist), path, max_age=31536000)
                    if path in ("sw.js", "workbox-*.js", "manifest.webmanifest", "registerSW.js"):
                        return send_from_directory(str(_frontend_dist), path, max_age=0)
                    return send_from_directory(str(_frontend_dist), path, max_age=31536000 if "." in path else 0)
                # SPA fallback — all /app/* routes serve index.html for React Router (no-cache)
                index = _frontend_dist / "index.html"
                if index.is_file():
                    return send_from_directory(str(_frontend_dist), "index.html", max_age=0)
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Frontend not built — run `cd frontend && npm run build`", "details": {}, "request_id": getattr(g, "request_id", "")}}), 404

            # Also serve Vite assets at /app/assets/* when index.html references /app/assets/*
            # (already covered by the `path` check above, but explicitly allow /assets for safety)
            @app.route("/assets/<path:path>")
            def _serve_frontend_assets(path):
                assets_dir = _frontend_dist / "assets"
                if (assets_dir / path).is_file():
                    return send_from_directory(str(assets_dir), path, max_age=31536000)
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Asset not found", "details": {}, "request_id": getattr(g, "request_id", "")}}), 404
            # Serve /app/assets/* directly (duplicate for base '/app/' builds)
            @app.route("/app/assets/<path:path>")
            def _serve_frontend_app_assets(path):
                assets_dir = _frontend_dist / "assets"
                if (assets_dir / path).is_file():
                    return send_from_directory(str(assets_dir), path, max_age=31536000)
                return jsonify({"error": {"code": "NOT_FOUND", "message": "Asset not found", "details": {}, "request_id": getattr(g, "request_id", "")}}), 404
            # PWA: serve manifest and sw at /app/* (vite-plugin-pwa generates at dist root)
            for _pwa_file in ("manifest.webmanifest", "sw.js", "workbox-*.js", "registerSW.js"):
                pass  # handled by /app/<path> above
    except Exception as _e:
        logger.warning("Frontend static serving not configured: %s", _e)

    # Standardized error handlers with request_id
    @app.errorhandler(404)
    def not_found(error):
        rid = getattr(g, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'Not found', 'details': {}, 'request_id': rid}}), 404

    @app.errorhandler(500)
    def internal_error(error):
        rid = getattr(g, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error', 'details': {}, 'request_id': rid}}), 500

    return app
