"""API package — exposes all v1 blueprints for registration."""
from backend.app.api.routes.health import health_bp
from backend.app.api.routes.races import races_bp
from backend.app.api.routes.predictions import predictions_bp
from backend.app.api.routes.standings import standings_bp
from backend.app.api.routes.h2h import h2h_bp
from backend.app.api.routes.constructors import constructors_bp
from backend.app.api.routes.analytics import analytics_bp
from backend.app.api.routes.reports import reports_bp
from backend.app.api.routes.ai import ai_bp
__all__ = ["health_bp","races_bp","predictions_bp","standings_bp","h2h_bp","constructors_bp","analytics_bp","reports_bp","ai_bp"]
