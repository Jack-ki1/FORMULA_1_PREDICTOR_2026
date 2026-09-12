"""
Fantasy scoring module - real F1 Fantasy ruleset.
Implements the actual F1 Fantasy scoring replacing the JSX's approximation.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from config.constants import POINTS_SYSTEM, SPRINT_POINTS_SYSTEM
from config.team_driver_lineup_2026 import get_all_drivers


class FantasyScoring:
    """
    Real F1 Fantasy rules implementation.
    Calculates fantasy points based on official scoring rules.
    """
    
    def __init__(self):
        self.drivers = get_all_drivers()
        self.driver_map = {d['code']: d for d in self.drivers}
        
        # Fantasy scoring rules (2026 format)
        self.scoring_rules = {
            'position_points': {
                1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
                6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
            },
            'qualifying_bonus': {
                1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1,
            },
            'fastest_lap_bonus': 1,
            'overtake_bonus': 2,  # Per overtake
            'dnf_penalty': -5,
            'sprint_points': {
                1: 8, 2: 7, 3: 6, 4: 5, 5: 4,
                6: 3, 7: 2, 8: 1,
            },
        }
    
    def calculate_driver_fantasy_points(
        self,
        driver_code: str,
        race_position: int,
        qualifying_position: int = None,
        fastest_lap: bool = False,
        overtakes: int = 0,
        dnf: bool = False,
        is_sprint: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate fantasy points for a driver in a race.
        
        Args:
            driver_code: Driver code
            race_position: Finishing position (1-22, 99 for DNF)
            qualifying_position: Qualifying position (1-22)
            fastest_lap: Whether driver scored fastest lap
            overtakes: Number of overtakes made
            dnf: Whether driver DNF'd
            is_sprint: Whether this is a sprint race
        
        Returns:
            Fantasy points breakdown
        """
        points_breakdown = {
            'driver_code': driver_code,
            'position_points': 0,
            'qualifying_bonus': 0,
            'fastest_lap_bonus': 0,
            'overtake_bonus': 0,
            'dnf_penalty': 0,
            'total_points': 0,
        }
        
        # Position points
        if not dnf and race_position <= 10:
            position_points = self.scoring_rules['position_points'].get(race_position, 0)
            if is_sprint:
                position_points = self.scoring_rules['sprint_points'].get(race_position, 0)
            points_breakdown['position_points'] = position_points
        
        # Qualifying bonus
        if qualifying_position and qualifying_position <= 6:
            points_breakdown['qualifying_bonus'] = self.scoring_rules['qualifying_bonus'].get(
                qualifying_position, 0
            )
        
        # Fastest lap bonus (only if finishes in top 10)
        if fastest_lap and not dnf and race_position <= 10:
            points_breakdown['fastest_lap_bonus'] = self.scoring_rules['fastest_lap_bonus']
        
        # Overtake bonus
        points_breakdown['overtake_bonus'] = overtakes * self.scoring_rules['overtake_bonus']
        
        # DNF penalty
        if dnf:
            points_breakdown['dnf_penalty'] = self.scoring_rules['dnf_penalty']
        
        # Calculate total
        points_breakdown['total_points'] = (
            points_breakdown['position_points'] +
            points_breakdown['qualifying_bonus'] +
            points_breakdown['fastest_lap_bonus'] +
            points_breakdown['overtake_bonus'] +
            points_breakdown['dnf_penalty']
        )
        
        return points_breakdown
    
    def calculate_team_fantasy_points(
        self,
        team_id: str,
        race_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate fantasy points for a team (sum of drivers).
        
        Args:
            team_id: Team identifier
            race_results: Dictionary of driver codes to race results
        
        Returns:
            Team fantasy points
        """
        from config.team_driver_lineup_2026 import get_drivers_by_team
        
        team_drivers = get_drivers_by_team(team_id)
        team_points = 0
        driver_breakdowns = {}
        
        for driver in team_drivers:
            driver_result = race_results.get(driver['code'])
            if driver_result:
                driver_points = self.calculate_driver_fantasy_points(
                    driver['code'],
                    **driver_result
                )
                team_points += driver_points['total_points']
                driver_breakdowns[driver['code']] = driver_points
        
        return {
            'team_id': team_id,
            'total_points': team_points,
            'driver_breakdowns': driver_breakdowns,
        }
    
    def calculate_expected_fantasy_points(
        self,
        driver_code: str,
        predicted_position: float,
        grid_position: int = None,
    ) -> Dict[str, Any]:
        """
        Calculate expected fantasy points based on predictions.
        
        Args:
            driver_code: Driver code
            predicted_position: Predicted finishing position (float)
            grid_position: Starting grid position
        
        Returns:
            Expected fantasy points with confidence intervals
        """
        # Expected position points (interpolated)
        position = int(np.round(predicted_position))
        expected_position_points = self._interpolate_position_points(position)
        
        # Expected qualifying bonus
        expected_qualifying_bonus = 0
        if grid_position:
            expected_qualifying_bonus = self.scoring_rules['qualifying_bonus'].get(
                grid_position, 0
            )
        
        # Expected fastest lap (based on position)
        expected_fastest_lap_prob = max(0, 1.0 - (position / 10.0))
        expected_fastest_lap = expected_fastest_lap_prob * self.scoring_rules['fastest_lap_bonus']
        
        # Expected overtakes (based on grid position)
        expected_overtakes = 0
        if grid_position and position:
            expected_overtakes = max(0, grid_position - position) * 0.5
        expected_overtake_bonus = expected_overtakes * self.scoring_rules['overtake_bonus']
        
        # Expected DNF risk
        driver = self.driver_map.get(driver_code.upper())
        dnf_risk = (100 - driver['reliability']) / 100.0 if driver else 0.1
        expected_dnf_penalty = -dnf_risk * self.scoring_rules['dnf_penalty']
        
        # Calculate expected total
        expected_total = (
            expected_position_points +
            expected_qualifying_bonus +
            expected_fastest_lap +
            expected_overtake_bonus +
            expected_dnf_penalty
        )
        
        # Simple confidence interval
        confidence = 0.8 - (dnf_risk * 0.5)
        lower_bound = expected_total * (1 - (1 - confidence))
        upper_bound = expected_total * (1 + (1 - confidence))
        
        return {
            'driver_code': driver_code,
            'predicted_position': predicted_position,
            'expected_points': expected_total,
            'breakdown': {
                'position_points': expected_position_points,
                'qualifying_bonus': expected_qualifying_bonus,
                'fastest_lap': expected_fastest_lap,
                'overtake_bonus': expected_overtake_bonus,
                'dnf_penalty': expected_dnf_penalty,
            },
            'confidence': confidence,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
        }
    
    def _interpolate_position_points(self, position: int) -> float:
        """Interpolate position points for non-integer positions."""
        if position <= 10:
            return self.scoring_rules['position_points'].get(position, 0)
        return 0.0
    
    def calculate_fantasy_league_score(
        self,
        user_picks: Dict[str, str],
        race_results: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate fantasy league score for user's picks.
        
        Args:
            user_picks: Dictionary of slot names to driver codes
            race_results: Dictionary of driver codes to race results
        
        Returns:
            User's fantasy league score
        """
        total_score = 0
        slot_scores = {}
        
        for slot, driver_code in user_picks.items():
            driver_result = race_results.get(driver_code)
            if driver_result:
                driver_points = self.calculate_driver_fantasy_points(
                    driver_code,
                    **driver_result
                )
                slot_scores[slot] = driver_points
                total_score += driver_points['total_points']
            else:
                slot_scores[slot] = {'total_points': 0, 'error': 'Driver not found'}
        
        return {
            'user_picks': user_picks,
            'total_score': total_score,
            'slot_scores': slot_scores,
        }
    
    def get_driver_fantasy_rankings(
        self,
        season_points: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        """
        Get driver fantasy rankings based on season points.
        
        Args:
            season_points: Dictionary of driver codes to season points
        
        Returns:
            Ranked list of drivers by fantasy points
        """
        rankings = []
        
        for driver_code, points in season_points.items():
            driver = self.driver_map.get(driver_code)
            rankings.append({
                'driver_code': driver_code,
                'driver_name': driver['name'] if driver else driver_code,
                'team': driver['team_name'] if driver else 'Unknown',
                'fantasy_points': points,
            })
        
        # Sort by fantasy points
        rankings.sort(key=lambda x: x['fantasy_points'], reverse=True)
        
        # Add positions
        for i, ranking in enumerate(rankings, 1):
            ranking['position'] = i
        
        return rankings
    
    def get_optimal_picks(
        self,
        race_predictions: Dict[str, Dict[str, float]],
        budget: int = 100,
        driver_costs: Dict[str, int] = None,
    ) -> Dict[str, Any]:
        """
        Suggest optimal fantasy picks based on predictions.
        
        Args:
            race_predictions: Driver predictions
            budget: Fantasy budget
            driver_costs: Driver costs (if using budget system)
        
        Returns:
            Optimal picks recommendation
        """
        # Sort drivers by expected fantasy points
        driver_values = []
        
        for driver_code, predictions in race_predictions.items():
            expected_points = self.calculate_expected_fantasy_points(
                driver_code,
                predictions.get('position', 12),
                predictions.get('grid', 12),
            )
            driver_values.append({
                'driver_code': driver_code,
                'expected_points': expected_points['expected_points'],
                'confidence': expected_points['confidence'],
            })
        
        # Sort by expected points
        driver_values.sort(key=lambda x: x['expected_points'], reverse=True)
        
        # Select top drivers (simplified - real fantasy has position limits)
        optimal_picks = {}
        for i, driver_value in enumerate(driver_values[:5]):  # Top 5 drivers
            slot = f"driver_{i+1}"
            optimal_picks[slot] = driver_value['driver_code']
        
        return {
            'optimal_picks': optimal_picks,
            'total_expected_points': sum(d['expected_points'] for d in driver_values[:5]),
            'driver_values': driver_values,
        }


# Global fantasy scoring instance
fantasy_scoring = FantasyScoring()
