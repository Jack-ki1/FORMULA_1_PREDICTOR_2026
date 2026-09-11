"""
FastAPI application — replaces the old Flask `dashboard/app.py`.

Locally:      uvicorn main:app --reload --port 8000
On Vercel:    index.py imports `app` from here; vercel.json routes /api/*
              to it (see /vercel.json at the repo root).
On Render:    same `app`, run via `uvicorn main:app --host 0.0.0.0 --port $PORT`
              (see AUDIT.md / PLAN.md §9 for the fallback deploy path).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from security.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from routers import (
    predictions,
    standings,
    h2h,
    constructors,
    reports,
    settings_router,
    health,
    status,
    auth,
    picks,
)

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="F1 Predictor API",
    version=settings.VERSION,
    description="Prediction, standings, and fantasy-league API for the F1 Predictor app.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(standings.router, prefix="/api/standings", tags=["standings"])
app.include_router(h2h.router, prefix="/api/h2h", tags=["h2h"])
app.include_router(constructors.router, prefix="/api/constructors", tags=["constructors"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(picks.router, prefix="/api", tags=["fantasy league"])


@app.get("/api")
def root():
    return {"name": "F1 Predictor API", "version": settings.VERSION, "docs": "/api/docs"}
