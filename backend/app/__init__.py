"""
F1 Predictor 2026 — Backend application factory (FastAPI).
Pure JSON API + frontend static. Python is minimal: ~8 core engine/data files,
async FastAPI, ONNX-ready, Redis cache. Replaces Flask dashboard/app.py.
"""
import time
import uuid
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application — minimal Python, auto-docs at /docs."""
    app = FastAPI(
        title="F1 Predictor 2026 API",
        description="Flask → FastAPI minimal Python. Monte Carlo, Elo, grid-model. Preserves prediction parity. Docs at /docs.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # CORS — production must set FRONTEND_ORIGIN allowlist; wildcard + credentials is rejected
    cors_origins = settings.CORS_ORIGINS
    # FRONTEND_ORIGIN overrides CORS_ORIGINS if set (explicit allowlist)
    frontend_origin = getattr(settings, 'FRONTEND_ORIGIN', '') or ''
    if frontend_origin:
        allow_origins = [o.strip() for o in frontend_origin.split(",") if o.strip()]
    elif cors_origins == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    # Wildcard with credentials is invalid — disable credentials in that case
    allow_credentials = False if allow_origins == ["*"] else True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: request_id, timing, security headers, rate limiting
    @app.middleware("http")
    async def _middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()
        # rate limit stub
        try:
            from backend.app.security.middleware import rate_limit_check_fastapi
            blocked = rate_limit_check_fastapi(request)
            if blocked:
                return blocked
        except Exception:
            pass
        response: Response = await call_next(request)
        # security headers
        try:
            from backend.app.security.middleware import add_security_headers_fastapi
            response = add_security_headers_fastapi(response, request)
        except Exception:
            pass
        # timing + request-id echo
        latency = time.time() - request.state.start_time
        response.headers["X-Response-Time"] = f"{latency:.3f}s"
        response.headers["X-Request-ID"] = request_id
        return response

    # Register versioned /api/v1 routers
    try:
        from backend.app.api.routes.health import router as health_router
        from backend.app.api.routes.races import router as races_router
        from backend.app.api.routes.predictions import router as predictions_router
        from backend.app.api.routes.standings import router as standings_router
        from backend.app.api.routes.h2h import router as h2h_router
        from backend.app.api.routes.constructors import router as constructors_router
        from backend.app.api.routes.analytics import router as analytics_router
        from backend.app.api.routes.reports import router as reports_router
        from backend.app.api.routes.ai import router as ai_router
        from backend.app.api.routes.openapi import router as openapi_router
        from backend.app.api.routes.system import router as system_router
        from backend.app.api.routes.scenario import router as scenario_router
        from backend.app.api.routes.live import router as live_router
        from backend.app.api.routes.jobs import router as jobs_router
        from backend.app.api.routes.settings import router as settings_router
        from backend.app.api.routes.news import router as news_router

        app.include_router(health_router)
        app.include_router(races_router)
        app.include_router(predictions_router)
        app.include_router(standings_router)
        app.include_router(h2h_router)
        app.include_router(constructors_router)
        app.include_router(analytics_router)
        app.include_router(reports_router)
        app.include_router(ai_router)
        app.include_router(openapi_router)
        app.include_router(system_router)
        app.include_router(scenario_router)
        app.include_router(live_router)
        app.include_router(jobs_router)
        app.include_router(settings_router)
        app.include_router(news_router)
        logger.info("Registered /api/v1 routers (including system/scenario/live/jobs+settings+news)")
    except Exception as e:
        logger.warning(f"Failed to register v1 routers: {e}")

    # Monitoring /metrics
    try:
        from backend.app.monitoring.blueprint import router as monitoring_router
        app.include_router(monitoring_router)
    except Exception:
        pass

    # API root — explicitly API only, never frontend HTML
    @app.get("/", tags=["health"])
    async def root():
        return {
            "service": "F1 Predictor 2026 API",
            "version": "1.0.0",
            "mode": "pure API — frontend is decoupled on Vite dev server",
            "frontend": "http://localhost:5173",
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1",
            "endpoints": ["/api/v1/races", "/api/v1/predictions", "/api/v1/standings/drivers", "/api/v1/h2h/compare"],
        }

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy", "version": "1.0.0"}

    # Backend is pure API — frontend is decoupled on Vite dev server (5173)
    # No static mount here. For production, frontend/dist is served via CDN/Vercel or `frontend` nginx service.

    # Error handlers — standard envelope
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return JSONResponse({"error": {"code": "NOT_FOUND", "message": "Not found", "details": {}, "request_id": rid}}, status_code=404)

    @app.exception_handler(500)
    async def internal_handler(request: Request, exc):
        rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
        return JSONResponse({"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "details": {}, "request_id": rid}}, status_code=500)

    return app


# For Vercel: `api/index.py` can import `app = create_app()` — Vercel detects `app` variable
app = create_app()
