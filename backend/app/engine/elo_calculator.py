"""
Elo rating system for driver skill tracking.
Updates driver ratings race-by-race, independent of car performance.
"""
from typing import Dict, List, Any
from backend.app.config.team_driver_lineup_2026 import get_all_drivers, get_driver_by_code


class EloCalculator:
    """
    Elo rating system for F1 drivers.
    Separates driver ability from car performance.
    """
    
    def __init__(self, initial_rating: float = 1500, k_factor: float = 32):
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.ratings = {}
        self.initialize_ratings()
    
    def initialize_ratings(self):
        """Initialize Elo ratings for all drivers based on their strength."""
        drivers = get_all_drivers()
        
        for driver in drivers:
            # Map strength (35-97) to Elo rating (1000-2000)
            elo = self.initial_rating + (driver['strength'] - 50) * 10
            self.ratings[driver['code']] = elo
    
    def get_rating(self, driver_code: str) -> float:
        """Get current Elo rating for a driver."""
        return self.ratings.get(driver_code.upper(), self.initial_rating)
    
    def update_rating(
        self,
        driver_code: str,
        actual_position: int,
        expected_position: float,
        num_drivers: int = 22,
    ) -> float:
        """
        Update Elo rating based on race result.
        
        Args:
            driver_code: Driver code
            actual_position: Actual finishing position (1-22)
            expected_position: Expected finishing position (float)
            num_drivers: Number of drivers in race
        
        Returns:
            New Elo rating
        """
        current_rating = self.get_rating(driver_code)
        
        # Convert positions to scores (higher score = better performance)
        actual_score = (num_drivers - actual_position) / num_drivers
        expected_score = (num_drivers - expected_position) / num_drivers
        
        # Calculate rating change
        rating_change = self.k_factor * (actual_score - expected_score)
        
        # Update rating
        new_rating = current_rating + rating_change
        self.ratings[driver_code.upper()] = new_rating
        
        return new_rating
    
    def expected_score(self, driver_a: str, driver_b: str) -> float:
        """
        Calculate expected score for driver A against driver B.
        
        Args:
            driver_a: Driver A code
            driver_b: Driver B code
        
        Returns:
            Expected score (0-1) for driver A
        """
        rating_a = self.get_rating(driver_a)
        rating_b = self.get_rating(driver_b)
        
        expected = 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
        return expected
    
    def update_race_results(
        self,
        race_results: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Update all Elo ratings based on race results.
        
        Args:
            race_results: List of race results with driver_code and position
        
        Returns:
            Dictionary of rating changes
        """
        changes = {}
        
        # Calculate expected positions based on current ratings
        sorted_drivers = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        expected_positions = {
            driver_code: i + 1
            for i, (driver_code, _) in enumerate(sorted_drivers)
        }
        
        # Update each driver's rating
        for result in race_results:
            driver_code = result['driver_code']
            actual_position = result['position']
            expected_position = expected_positions.get(driver_code, 12)
            
            old_rating = self.get_rating(driver_code)
            new_rating = self.update_rating(driver_code, actual_position, expected_position)
            changes[driver_code] = new_rating - old_rating
        
        return changes
    
    def get_h2h_probability(self, driver_a: str, driver_b: str) -> float:
        """
        Calculate head-to-head win probability for driver A vs driver B.
        
        Args:
            driver_a: Driver A code
            driver_b: Driver B code
        
        Returns:
            Probability (0-1) that driver A beats driver B
        """
        return self.expected_score(driver_a, driver_b)
    
    def get_rankings(self) -> List[Dict[str, Any]]:
        """Get current Elo rankings."""
        sorted_ratings = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        rankings = []
        for position, (driver_code, rating) in enumerate(sorted_ratings, 1):
            driver = get_driver_by_code(driver_code)
            rankings.append({
                'position': position,
                'driver_code': driver_code,
                'driver_name': driver['name'] if driver else driver_code,
                'team': driver['team_name'] if driver else 'Unknown',
                'elo_rating': rating,
            })
        
        return rankings
    
    def reset_ratings(self):
        """Reset all ratings to initial values."""
        self.initialize_ratings()


# Global Elo calculator instance
elo_calculator = EloCalculator()
