"""
Multi-Dimensional ELO Rating System (FEATURE-9).

Extends basic ELO to track different skill dimensions:
- Qualifying ELO (single-lap pace)
- Race ELO (long-run consistency)
- Wet Weather ELO (rain performance)
- Overtaking ELO (wheel-to-wheel skill)
- Defense ELO (ability to hold position)

Uses Glicko-2 system for uncertainty tracking (Rating Deviation).
"""

import math
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MultiDimensionalELO:
    """
    Tracks multiple ELO ratings per driver across different skill dimensions.
    
    Each dimension has:
    - Rating (1500 base)
    - Rating Deviation (RD): Uncertainty measure (lower = more certain)
    - Volatility: How much rating changes race-to-race
    """
    
    # Glicko-2 constants
    SCALE_FACTOR = 173.7178  # Converts from Glicko-2 scale to traditional ELO
    TAU = 0.5  # System constant limiting volatility changes
    
    def __init__(self):
        # Initialize drivers with base ratings
        self.drivers = {}
        
    def initialize_driver(self, driver_id: str, base_rating: float = 1500.0):
        """Initialize a driver with multi-dimensional ELO ratings."""
        self.drivers[driver_id] = {
            "qualifying": {
                "rating": base_rating,
                "rd": 350.0,  # High initial uncertainty
                "volatility": 0.06,
            },
            "race": {
                "rating": base_rating,
                "rd": 350.0,
                "volatility": 0.06,
            },
            "wet_weather": {
                "rating": base_rating,
                "rd": 400.0,  # Even higher uncertainty (fewer wet races)
                "volatility": 0.08,
            },
            "overtaking": {
                "rating": base_rating,
                "rd": 350.0,
                "volatility": 0.06,
            },
            "defense": {
                "rating": base_rating,
                "rd": 350.0,
                "volatility": 0.06,
            },
        }
    
    def get_elo_score(self, driver_id: str, dimension: str = "race") -> float:
        """
        Get normalized ELO score for a driver in a specific dimension.
        
        Returns value between 0 and 1 for use in composite score calculation.
        """
        if driver_id not in self.drivers:
            return 0.5
        
        rating = self.drivers[driver_id][dimension]["rating"]
        
        # Normalize to 0-1 range (assuming typical range 1200-1800)
        normalized = (rating - 1200) / 600
        return max(0.0, min(1.0, normalized))
    
    def update_ratings_after_race(self, race_results: List[Dict], 
                                 weather_conditions: str = "dry"):
        """
        Update all ELO dimensions based on race results.
        
        Args:
            race_results: List of dicts with driver_id, grid_pos, finish_pos, etc.
            weather_conditions: "dry", "wet", or "mixed"
        """
        # Update race ELO for all drivers
        self._update_dimension(race_results, "race")
        
        # Update qualifying ELO if qualifying data available
        if all("quali_pos" in r for r in race_results):
            quali_results = [{"driver_id": r["driver_id"], 
                            "grid_pos": r.get("quali_pos", r["grid_pos"]),
                            "finish_pos": r["finish_pos"]} 
                           for r in race_results]
            self._update_dimension(quali_results, "qualifying")
        
        # Update wet weather ELO if race was wet
        if weather_conditions in ["wet", "mixed"]:
            self._update_dimension(race_results, "wet_weather")
        
        # Update overtaking/defense ELO based on position changes
        self._update_overtaking_defense(race_results)
    
    def _update_dimension(self, results: List[Dict], dimension: str):
        """Update a specific ELO dimension using Glicko-2 algorithm."""
        n_drivers = len(results)
        if n_drivers < 2:
            return
        
        for i, driver_result in enumerate(results):
            driver_id = driver_result["driver_id"]
            if driver_id not in self.drivers:
                self.initialize_driver(driver_id)
            
            player = self.drivers[driver_id][dimension]
            
            # Calculate expected scores against all other drivers
            total_score = 0.0
            variance = 0.0
            
            for j, opponent_result in enumerate(results):
                if i == j:
                    continue
                
                opp_id = opponent_result["driver_id"]
                if opp_id not in self.drivers:
                    continue
                
                opponent = self.drivers[opp_id][dimension]
                
                # Calculate expected outcome using Glicko-2 formula
                expected = self._glicko2_expected(player, opponent)
                
                # Actual outcome: 1 = beat opponent, 0 = lost to opponent
                actual = 1.0 if driver_result["finish_pos"] < opponent_result["finish_pos"] else 0.0
                
                # Weight by finishing position difference (bigger gap = stronger signal)
                pos_diff = abs(driver_result["finish_pos"] - opponent_result["finish_pos"])
                weight = min(1.0, pos_diff / 10.0)  # Cap at 10 positions
                
                total_score += weight * (actual - expected)
                variance += weight ** 2 * expected * (1 - expected)
            
            # Update rating
            if variance > 0:
                new_rating = player["rating"] + (player["volatility"] ** 2 / variance) * total_score
                
                # Update RD (Rating Deviation)
                new_rd = math.sqrt(1 / (1 / player["rd"]**2 + variance / player["volatility"]**2))
                
                # Clamp values
                player["rating"] = max(1000, min(2000, new_rating))
                player["rd"] = max(50, min(350, new_rd))
    
    def _update_overtaking_defense(self, results: List[Dict]):
        """Update overtaking and defense ELO based on position changes."""
        for result in results:
            driver_id = result["driver_id"]
            if driver_id not in self.drivers:
                continue
            
            grid_pos = result.get("grid_pos", result.get("finish_pos"))
            finish_pos = result["finish_pos"]
            
            position_change = grid_pos - finish_pos  # Positive = gained positions
            
            # Update overtaking ELO
            if position_change > 0:
                # Gained positions = good overtaking
                self._incremental_update(driver_id, "overtaking", position_change * 2)
            
            # Update defense ELO
            if position_change >= 0:
                # Maintained or improved position = good defense
                self._incremental_update(driver_id, "defense", 1)
            else:
                # Lost positions = poor defense
                self._incremental_update(driver_id, "defense", position_change)
    
    def _incremental_update(self, driver_id: str, dimension: str, performance_delta: float):
        """Simple incremental ELO update."""
        player = self.drivers[driver_id][dimension]
        
        # Learning rate decreases with certainty (lower RD)
        learning_rate = 0.01 * (player["rd"] / 350.0)
        
        # Update rating
        player["rating"] += learning_rate * performance_delta
        player["rating"] = max(1200, min(1800, player["rating"]))
        
        # Decrease RD slightly (more data = more certainty)
        player["rd"] = max(50, player["rd"] * 0.995)
    
    def _glicko2_expected(self, player: Dict, opponent: Dict) -> float:
        """Calculate expected score using Glicko-2 formula."""
        # Convert to Glicko-2 scale
        r1 = (player["rating"] - 1500) / self.SCALE_FACTOR
        r2 = (opponent["rating"] - 1500) / self.SCALE_FACTOR
        
        rd1 = player["rd"] / self.SCALE_FACTOR
        rd2 = opponent["rd"] / self.SCALE_FACTOR
        
        # Expected score
        denominator = math.sqrt(1 + 3 * (rd1**2 + rd2**2) / (math.pi**2))
        expected = 1 / (1 + math.exp(-(r1 - r2) / denominator))
        
        return expected
    
    def get_driver_profile(self, driver_id: str) -> Dict:
        """Get complete ELO profile for a driver."""
        if driver_id not in self.drivers:
            return {}
        
        profile = {}
        for dimension, data in self.drivers[driver_id].items():
            profile[dimension] = {
                "rating": round(data["rating"], 1),
                "rd": round(data["rd"], 1),
                "normalized": round(self.get_elo_score(driver_id, dimension), 3),
                "certainty_pct": round((1 - data["rd"] / 350) * 100, 1),
            }
        
        return profile
    
    def compare_drivers(self, driver1_id: str, driver2_id: str, 
                       dimension: str = "race") -> Dict:
        """Compare two drivers in a specific dimension."""
        if driver1_id not in self.drivers or driver2_id not in self.drivers:
            return {}
        
        d1 = self.drivers[driver1_id][dimension]
        d2 = self.drivers[driver2_id][dimension]
        
        # Calculate win probability using logistic function
        rating_diff = d1["rating"] - d2["rating"]
        combined_rd = math.sqrt(d1["rd"]**2 + d2["rd"]**2)
        
        # Probability driver1 beats driver2
        win_prob = 1 / (1 + math.exp(-rating_diff / (combined_rd + 100)))
        
        return {
            "driver1": {
                "id": driver1_id,
                "rating": d1["rating"],
                "rd": d1["rd"],
            },
            "driver2": {
                "id": driver2_id,
                "rating": d2["rating"],
                "rd": d2["rd"],
            },
            "dimension": dimension,
            "win_probability": round(win_prob, 3),
            "rating_difference": round(rating_diff, 1),
        }


# Global instance for easy access
_elo_system = None

def get_elo_system() -> MultiDimensionalELO:
    """Get or create the multi-dimensional ELO system singleton."""
    global _elo_system
    if _elo_system is None:
        _elo_system = MultiDimensionalELO()
        
        # Initialize with current drivers
        from data.driver_data import get_all_drivers
        for driver in get_all_drivers():
            _elo_system.initialize_driver(driver["id"], base_rating=driver.get("elo", 1500))
    
    return _elo_system


if __name__ == "__main__":
    # Test the multi-dimensional ELO system
    print("Testing Multi-Dimensional ELO System...")
    
    elo = get_elo_system()
    
    # Simulate a race result
    test_results = [
        {"driver_id": "antonelli", "grid_pos": 1, "finish_pos": 1},
        {"driver_id": "verstappen", "grid_pos": 3, "finish_pos": 2},
        {"driver_id": "norris", "grid_pos": 2, "finish_pos": 3},
        {"driver_id": "hamilton", "grid_pos": 5, "finish_pos": 4},
        {"driver_id": "leclerc", "grid_pos": 4, "finish_pos": 5},
    ]
    
    # Update ratings
    elo.update_ratings_after_race(test_results, weather_conditions="dry")
    
    # Get profiles
    print("\nDriver Profiles:")
    for driver_id in ["antonelli", "verstappen", "norris"]:
        profile = elo.get_driver_profile(driver_id)
        print(f"\n{driver_id.upper()}:")
        for dim, data in profile.items():
            print(f"  {dim:15s}: {data['rating']:6.1f} (RD: {data['rd']:5.1f}, "
                  f"Certainty: {data['certainty_pct']:.1f}%)")
    
    # Compare drivers
    print("\n\nHead-to-Head Comparison:")
    comparison = elo.compare_drivers("antonelli", "verstappen", "race")
    print(f"Antonelli vs Verstappen (Race):")
    print(f"  Win Probability: {comparison['win_probability']*100:.1f}%")
    print(f"  Rating Difference: {comparison['rating_difference']}")
