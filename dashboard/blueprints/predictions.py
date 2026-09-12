import logging
import json
from flask import Blueprint, request, jsonify, render_template
from engine.predictor import generate_prediction
from config.settings import settings
from data.calendar_2026 import CALENDAR_2026, get_race_by_id
from data.circuit_data import CIRCUITS

logger = logging.getLogger(__name__)

predictions_bp = Blueprint('predictions', __name__)


@predictions_bp.route('/')
def index():
    """Render the main dashboard page."""
    try:
        # Filter out cancelled races to show only valid race options
        valid_calendar = [race for race in CALENDAR_2026 if race.get('status') != 'cancelled']
        logger.info(f"Rendering dashboard with {len(valid_calendar)} valid races (from {len(CALENDAR_2026)} total)")
        return render_template('dashboard.html', calendar=valid_calendar)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return render_template('dashboard.html', calendar=[])


@predictions_bp.route('/api/races')
def api_races():
    """Return calendar data as JSON for the dashboard."""
    return jsonify(CALENDAR_2026)


@predictions_bp.route('/api/race-result/<race_id>')
def api_race_result(race_id):
    """Return result for a completed race (or 404 if not completed)."""
    race = get_race_by_id(race_id)
    if not race:
        return jsonify({'error': 'Race not found'}), 404
    if race.get('status') != 'completed':
        return jsonify({'error': 'Race not yet completed'}), 404
    return jsonify(race)


@predictions_bp.route('/api/predict-session', methods=['POST'])
def api_predict_session():
    """Generate predictions for a race session from the dashboard UI."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    race_id = data.get('race_id')
    session_type = data.get('session_type', 'race')
    sub_session = data.get('sub_session')  # New parameter for FP1, FP2, FP3, Q1, Q2, Q3
    weather = data.get('weather', 'dry')
    grid_positions = data.get('grid_positions')
    feature_weights = data.get('feature_weights')
    simulation_count = data.get('simulation_count', 10000)
    ai_mode = data.get('ai_mode', 'normal')
    ai_model = data.get('ai_model', 'gemini-2.0-flash-exp')
    ai_api_key = data.get('ai_api_key', '')
    ai_weight = data.get('ai_weight', 0.3)
    ai_temperature = data.get('ai_temperature', 0.7)

    if not race_id:
        return jsonify({'error': 'race_id is required'}), 400

    try:
        result = generate_prediction(
            race_id=race_id,
            session_type=session_type,
            sub_session=sub_session,
            weather=weather,
            grid_positions=grid_positions,
            feature_weights=feature_weights,
            simulation_count=simulation_count,
            ai_config={
                'ai_mode': ai_mode,
                'ai_model': ai_model,
                'ai_api_key': ai_api_key,
                'ai_weight': ai_weight,
                'ai_temperature': ai_temperature,
            }
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Prediction error for race {race_id}: {e}")
        if settings.DEBUG:
            import traceback
            logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@predictions_bp.route('/api/ai-chat', methods=['POST'])
def api_ai_chat():
    """AI chat endpoint for the dashboard AI sidebar."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    message = data.get('message', '')
    model = data.get('model', 'gemini-2.0-flash-exp')
    api_key = data.get('api_key', '')
    temperature = float(data.get('temperature', 0.7))

    if not message:
        return jsonify({'error': 'message is required'}), 400

    try:
        from engine.ai_client import ai_client
        
        # Enhanced system prompt for F1-specific chat
        system_prompt = """You are an expert Formula 1 analyst and racing strategist. You have deep knowledge of:
- Current F1 regulations and technical rules
- Driver performance histories and driving styles
- Team strategies and car characteristics
- Circuit layouts and their specific challenges
- Weather impacts on racing
- Tyre strategies and degradation patterns

Provide detailed, accurate, and insightful responses about F1 racing. When discussing predictions or probabilities, always acknowledge uncertainty and the many variables that affect race outcomes. Be specific but cautious about definitive predictions."""
        
        enhanced_message = f"{system_prompt}\n\nUser question: {message}"
        
        if api_key:
            res = ai_client.call_ai(model=model, api_key=api_key, prompt=enhanced_message, temperature=temperature, max_tokens=1500)
            if res and 'text' in res:
                return jsonify({'response': res['text'], 'provider': res.get('provider'), 'model': model}), 200
            else:
                # Provide helpful fallback response
                fallback_response = """I'm having trouble connecting to the AI service right now. However, I can still help you with F1 predictions using the traditional ML models available in the dashboard. 

For specific questions about:
- Driver predictions: Use the prediction dashboard
- Race analysis: Check the standings and head-to-head sections
- Strategy insights: The simulation results provide detailed strategy analysis

Please try again with a valid API key for AI-enhanced responses."""
                return jsonify({'response': fallback_response, 'provider': 'fallback', 'model': model}), 200
        else:
            from ai.provider import AIProviderManager
            manager = AIProviderManager()
            result = manager.predict(prompt=enhanced_message)
            return jsonify({'response': result.get('text', str(result)), 'provider': 'fallback', 'model': model}), 200
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        if settings.DEBUG:
            import traceback
            logger.error(traceback.format_exc())
        
        error_response = f"I encountered an error processing your request: {str(e)}. Please check your API key and try again."
        return jsonify({'response': error_response, 'provider': 'error', 'model': model}), 200  # Return 200 with error message instead of 500


def validate_prediction_request(data: dict) -> list:
    """Validate prediction request data."""
    errors = []
    if not isinstance(data, dict):
        errors.append("Request data must be a JSON object")
        return errors

    race_id = data.get('race_id')
    if not race_id or not isinstance(race_id, str):
        errors.append("race_id is required and must be a string")

    session_type = data.get('session_type')
    if not session_type or not isinstance(session_type, str):
        errors.append("session_type is required and must be a string")

    return errors


def handle_prediction_error(e: Exception, race_id: str) -> tuple:
    """Handle prediction errors and return appropriate response."""
    error_msg = str(e)
    logger.error(f"Error generating prediction for race {race_id}: {error_msg}")
    return jsonify({
        'error': 'Prediction generation failed',
        'message': error_msg,
        'race_id': race_id
    }), 500


@predictions_bp.route('/predict', methods=['POST'])
def predict():
    """Generate predictions for a race session (legacy endpoint)."""
    try:
        data = request.get_json() or {}
        race_id = data.get('race_id')
        session_type = data.get('session_type', 'race')
        weather = data.get('weather', 'dry')
        grid_positions = data.get('grid_positions')

        if not race_id:
            return jsonify({'error': 'race_id is required'}), 400

        result = generate_prediction(
            race_id=race_id,
            session_type=session_type,
            weather=weather,
            grid_positions=grid_positions
        )
        return jsonify(result), 200
    except Exception as e:
        return handle_prediction_error(e, data.get('race_id', 'unknown'))
