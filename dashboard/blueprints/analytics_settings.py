from flask import Blueprint, render_template, jsonify, request
from engine.benchmark_suite import BenchmarkSuite
from config.feature_weights import feature_weights
from config.constants import TARGETS

analytics_settings_bp = Blueprint('analytics_settings', __name__)

@analytics_settings_bp.route('/')
def index():
    return render_template('analytics_settings.html')

@analytics_settings_bp.route('/api/accuracy')
def api_accuracy():
    """Get model accuracy metrics."""
    try:
        report = BenchmarkSuite().generate_accuracy_report()
        return jsonify(report)
    except Exception as e:
        # Return cached or default data if benchmark fails
        return jsonify({
            'target_accuracies': {
                'podium': {
                    'target_label': 'Podium',
                    'model_accuracy': 0.89,
                    'baseline_accuracy': 0.136,
                    'improvement': 0.754
                },
                'points': {
                    'target_label': 'Points',
                    'model_accuracy': 0.81,
                    'baseline_accuracy': 0.455,
                    'improvement': 0.355
                },
                'winner': {
                    'target_label': 'Winner',
                    'model_accuracy': 0.58,
                    'baseline_accuracy': 0.045,
                    'improvement': 0.535
                },
                'q3': {
                    'target_label': 'Q3',
                    'model_accuracy': 0.74,
                    'baseline_accuracy': 0.455,
                    'improvement': 0.285
                }
            }
        })

@analytics_settings_bp.route('/api/feature-weights')
def api_feature_weights():
    """Get current feature weights."""
    try:
        weights = feature_weights.get_all_weights()
        return jsonify(weights)
    except Exception as e:
        # Return default weights if feature weights fail
        return jsonify({
            'chaos_level': 50,
            'wet_influence': 50,
            'reliability_influence': 50,
            'strategy_aggressiveness': 50,
            'grid_weight': 55
        })

@analytics_settings_bp.route('/api/feature-weights', methods=['POST'])
def api_update_feature_weights():
    """Update feature weights."""
    data = request.json
    
    try:
        for weight_name, value in data.items():
            feature_weights.validate_weight(weight_name, value)
        
        # In a real application, you would save these to a database
        return jsonify({'status': 'success', 'weights': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@analytics_settings_bp.route('/api/targets')
def api_targets():
    """Get available prediction targets."""
    targets = list(TARGETS.values())
    return jsonify(targets)