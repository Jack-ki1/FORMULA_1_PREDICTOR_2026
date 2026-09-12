"""
Flask application factory - main application entry point.
Registers all blueprints and configures the Flask app.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from config.settings import settings


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder='static')
    
    # Configure Flask app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    app.config['FLASK_ENV'] = settings.FLASK_ENV

    # Enable CORS
    CORS(app)

    # Register blueprints
    from dashboard.blueprints.landing import landing_bp
    from dashboard.blueprints.predictions import predictions_bp
    from dashboard.blueprints.standings import standings_bp
    from dashboard.blueprints.h2h import h2h_bp
    from dashboard.blueprints.constructors import constructors_bp
    from dashboard.blueprints.analytics_settings import analytics_settings_bp
    from dashboard.blueprints.reports import reports_bp

    # landing_bp owns '/' and renders homepage.html — this is the site's
    # single home page. (Previously there was ALSO an @app.route('/') below
    # rendering templates/landing.html; Flask/Werkzeug resolves duplicate
    # rules by registration order, so that second route could never actually
    # be served and templates/landing.html was silently dead code. Removed —
    # see templates/landing.html's docstring-equivalent comment for what to
    # do with that file.)
    app.register_blueprint(landing_bp)
    app.register_blueprint(predictions_bp, url_prefix='/dashboard')
    app.register_blueprint(standings_bp, url_prefix='/standings')
    app.register_blueprint(h2h_bp, url_prefix='/h2h')
    app.register_blueprint(constructors_bp, url_prefix='/constructors')
    app.register_blueprint(analytics_settings_bp, url_prefix='/analytics')
    # reports_bp only provides API endpoints now, no UI page
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Add a direct route to /dashboard (without trailing slash) that redirects to /dashboard/
    @app.route('/dashboard')
    def dashboard_redirect():
        from flask import redirect
        return redirect('/dashboard/')

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'version': '1.0.0'})

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app
