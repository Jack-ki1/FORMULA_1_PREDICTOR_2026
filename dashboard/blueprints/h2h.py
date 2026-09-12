"""
H2H blueprint - driver vs driver comparison with live and per-race views.
"""
from flask import Blueprint, render_template, jsonify, request
from engine.elo_calculator import elo_calculator
from config.team_driver_lineup_2026 import get_all_drivers, get_driver_by_code

h2h_bp = Blueprint('h2h', __name__)


@h2h_bp.route('/')
def h2h():
    """Render H2H comparison page."""
    drivers = get_all_drivers()
    return render_template('h2h.html', drivers=drivers)


@h2h_bp.route('/api/compare', methods=['POST'])
def api_compare():
    """
    Compare two drivers.

    NOTE: this previously called get_all_drivers() twice into unused
    `driver_a_info` / `driver_b_info` locals and never returned them — the
    frontend had no way to show either driver's name/team/number without a
    second round trip. Fixed to look each driver up by code and include
    both in the response.
    """
    data = request.json or {}
    driver_a = (data.get('driver_a') or '').upper()
    driver_b = (data.get('driver_b') or '').upper()

    if not driver_a or not driver_b:
        return jsonify({'error': 'driver_a and driver_b are both required'}), 400

    driver_a_info = get_driver_by_code(driver_a)
    driver_b_info = get_driver_by_code(driver_b)
    if not driver_a_info or not driver_b_info:
        return jsonify({'error': 'Unknown driver code'}), 404

    try:
        probability = elo_calculator.get_h2h_probability(driver_a, driver_b)
        return jsonify({
            'driver_a': driver_a_info,
            'driver_b': driver_b_info,
            'win_probability': probability,
            'reverse_probability': 1 - probability,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@h2h_bp.route('/api/drivers')
def api_drivers():
    """Get all drivers for comparison."""
    drivers = get_all_drivers()
    return jsonify(drivers)
