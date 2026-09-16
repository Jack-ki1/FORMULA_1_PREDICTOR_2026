"""API package — exposes all v1 routers for FastAPI registration."""
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.races import router as races_router
from backend.app.api.routes.predictions import router as predictions_router
from backend.app.api.routes.standings import router as standings_router
from backend.app.api.routes.h2h import router as h2h_router
# Removed: constructors router - teams section eliminated
from backend.app.api.routes.reports import router as reports_router
from backend.app.api.routes.ai import router as ai_router

__all__ = ["health_router","races_router","predictions_router","standings_router","h2h_router","reports_router","ai_router"]
