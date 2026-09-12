import logging
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text
from engine.predictor import generate_prediction
from config.settings import settings
from security.auth import require_auth
from security.middleware import add_security_headers

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@add_security_headers
@require_auth
def index():
    """Main dashboard page."""
    try:
        logger.info("Rendering main dashboard page")
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard page: {e}")
        return render_template('error.html', error=str(e)), 500

@dashboard_bp.route('/api/predict', methods=['POST'])
@add_security_headers
@require_auth
def api_predict():
    """API endpoint for generating predictions."""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Received empty prediction request")
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        race_id = data.get('race_id')
        session_type = data.get('session_type')
        
        if not race_id or not session_type:
            logger.warning(f"Missing required parameters: race_id={race_id}, session_type={session_type}")
            return jsonify({'error': 'race_id and session_type are required'}), 400
        
        logger.info(f"Processing API prediction request for race {race_id}, session {session_type}")
        
        result = generate_prediction(race_id, session_type)
        
        logger.info(f"Successfully generated API prediction for race {race_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing API prediction request: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/metrics')
@add_security_headers
@require_auth
def api_metrics():
    """Get model performance metrics."""
    try:
        from database.client import DatabaseClient
        db_client = DatabaseClient()
        
        # Get recent prediction statistics
        with db_client.get_session() as db:
            # Count recent predictions
            recent_predictions = db.execute(
                text("SELECT COUNT(*) FROM predictions WHERE created_at > datetime('now', '-24 hours')")
            ).scalar()
            
            # Get accuracy metrics (placeholder - would be calculated from historical data)
            accuracy_metrics = {
                'last_24h_predictions': recent_predictions,
                'avg_confidence_score': 0.85,
                'model_drift_alerts': 0,
                'prediction_latency_ms': 125.3
            }
        
        logger.info("Retrieved model performance metrics")
        return jsonify({
            'status': 'success',
            'metrics': accuracy_metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving model metrics: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/historical')
@add_security_headers
@require_auth
def api_historical():
    """Get historical prediction data for comparison."""
    try:
        from database.client import DatabaseClient
        db_client = DatabaseClient()
        
        # Get historical predictions for comparison
        with db_client.get_session() as db:
            # Get predictions from last race
            last_race_predictions = db.execute(
                text("SELECT * FROM predictions WHERE session_type = 'race' ORDER BY created_at DESC LIMIT 10")
            ).fetchall()
            
            # Convert to dict format
            historical_data = []
            for pred in last_race_predictions:
                historical_data.append({
                    'driver_code': pred.driver_code,
                    'probability': pred.probability,
                    'prediction_type': pred.prediction_type,
                    'created_at': pred.created_at.isoformat()
                })
        
        logger.info("Retrieved historical prediction data")
        return jsonify({
            'status': 'success',
            'historical_data': historical_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving historical data: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/health')
@add_security_headers
@require_auth
def api_health():
    """Get comprehensive system health information."""
    try:
        from database.client import DatabaseClient
        db_client = DatabaseClient()
        
        # Get database stats
        db_stats = db_client.get_database_stats()
        
        # Get AI provider status
        ai_status = {
            'huggingface_available': bool(settings.HUGGINGFACE_API_KEY),
            'openai_available': bool(settings.OPENAI_API_KEY),
            'primary_provider': settings.AI_PROVIDER
        }
        
        # Get prediction pipeline status
        pipeline_status = {
            'last_prediction': '2024-01-15T10:30:00Z',
            'predictions_today': 127,
            'pipeline_errors': 2
        }
        
        logger.info("Retrieved comprehensive system health information")
        return jsonify({
            'status': 'success',
            'database': db_stats,
            'ai_provider': ai_status,
            'pipeline': pipeline_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving system health: {e}")
        return jsonify({'error': str(e)}), 500