from flask import Blueprint, render_template, jsonify
from data.team_data import get_all_enhanced_teams, get_team_power_rankings

constructors_bp = Blueprint('constructors', __name__)

@constructors_bp.route('/')
def index():
    teams = get_all_enhanced_teams()
    return render_template('constructors.html', teams=teams)

@constructors_bp.route('/api/teams')
def api_teams():
    """Get all teams."""
    teams = get_all_enhanced_teams()
    return jsonify(teams)

@constructors_bp.route('/api/power-rankings')
def api_power_rankings():
    """Get team power rankings."""
    rankings = get_team_power_rankings()
    return jsonify(rankings)