"""
Tire Strategy Modeling Module (FEATURE-2).

Models tire degradation, pit stop strategies, and compound choices.
Critical for accurate midfield predictions where strategy differentials matter most.

Features:
- Tire degradation curves per circuit
- Pit stop strategy optimization (1-stop vs 2-stop vs 3-stop)
- Compound choice impact (soft/medium/hard)
- Safety Car pit stop advantage modeling
- Temperature effects on tire wear
"""

import math
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# Tire compound characteristics
TIRE_COMPOUNDS = {
    "soft": {
        "initial_grip": 1.0,
        "degradation_rate": 0.08,  # Lap time loss per lap (%)
        "optimal_window": 15,      # Laps before significant degradation
        "max_laps": 30,            # Absolute maximum before failure risk
        "pit_time_loss": 22.0,     # Seconds lost in pit stop
    },
    "medium": {
        "initial_grip": 0.97,
        "degradation_rate": 0.05,
        "optimal_window": 25,
        "max_laps": 45,
        "pit_time_loss": 22.0,
    },
    "hard": {
        "initial_grip": 0.94,
        "degradation_rate": 0.03,
        "optimal_window": 35,
        "max_laps": 60,
        "pit_time_loss": 22.0,
    },
    "intermediate": {
        "initial_grip": 0.90,
        "degradation_rate": 0.10,
        "optimal_window": 20,
        "max_laps": 40,
        "pit_time_loss": 24.0,
    },
    "wet": {
        "initial_grip": 0.85,
        "degradation_rate": 0.12,
        "optimal_window": 15,
        "max_laps": 30,
        "pit_time_loss": 25.0,
    }
}


class TireStrategyModel:
    """Models tire performance and strategy decisions."""
    
    def __init__(self, circuit_id: str, race_laps: int):
        self.circuit_id = circuit_id
        self.race_laps = race_laps
        
        # Circuit-specific tire degradation multipliers
        self.circuit_degradation_factors = self._get_circuit_tire_factors()
    
    def _get_circuit_tire_factors(self) -> Dict[str, float]:
        """
        Get tire degradation factors specific to each circuit.
        
        High-degradation circuits: Monaco, Singapore, Hungary (high downforce, low speed)
        Low-degradation circuits: Monza, Spa, Baku (high speed, low downforce)
        """
        return {
            "monaco": 1.3,       # Very high degradation (tight corners, low speed)
            "singapore": 1.25,   # High degradation (humidity, street circuit)
            "hungary": 1.2,      # High degradation (technical, slow corners)
            "spain": 1.15,       # Moderate-high degradation
            "italy": 0.85,       # Low degradation (high speed, long straights)
            "belgium": 0.90,     # Low-moderate degradation
            "azerbaijan": 0.88,  # Low degradation (street but fast)
            "canada": 1.1,       # Moderate degradation (heavy braking)
            "austria": 0.95,     # Moderate degradation
            "britain": 1.0,      # Average degradation
            "netherlands": 1.05, # Slightly above average
            "japan": 1.1,        # Moderate degradation (Suzuka corners)
            "usa": 0.95,         # Moderate degradation
            "mexico": 0.90,      # Lower degradation (altitude helps)
            "brazil": 1.15,      # High degradation (elevation changes)
            "uae": 1.2,          # High degradation (heat, abrasive surface)
        }
    
    def calculate_tire_performance(self, compound: str, lap_number: int, 
                                  stint_length: int, temperature_c: float = 25.0) -> float:
        """
        Calculate tire performance factor for a given lap.
        
        Args:
            compound: Tire compound ("soft", "medium", "hard", etc.)
            lap_number: Current lap number in stint (1-based)
            stint_length: Total planned stint length
            temperature_c: Track temperature in Celsius
        
        Returns:
            Performance multiplier (1.0 = optimal, <1.0 = degraded)
        """
        tire_data = TIRE_COMPOUNDS.get(compound)
        if not tire_data:
            logger.warning(f"Unknown tire compound: {compound}")
            return 0.90
        
        # Base degradation
        degradation = tire_data["degradation_rate"]
        
        # Apply circuit-specific factor
        circuit_factor = self.circuit_degradation_factors.get(self.circuit_id, 1.0)
        adjusted_degradation = degradation * circuit_factor
        
        # Temperature effect: higher temps increase degradation
        temp_factor = 1.0 + max(0, (temperature_c - 25) / 50)  # +2% per 1°C above 25°C
        
        # Calculate performance loss
        # Exponential degradation model: performance drops faster as tires age
        age_ratio = lap_number / stint_length
        performance_loss = adjusted_degradation * lap_number * (1 + 0.5 * age_ratio) * temp_factor
        
        # Initial grip bonus for fresh tires
        initial_grip = tire_data["initial_grip"]
        
        # Final performance factor
        performance = initial_grip * (1 - performance_loss)
        
        # Clamp to reasonable range
        return max(0.70, min(1.05, performance))
    
    def simulate_stint(self, compound: str, start_lap: int, end_lap: int,
                      temperature_c: float = 25.0) -> Dict:
        """
        Simulate a tire stint and return performance metrics.
        
        Args:
            compound: Tire compound
            start_lap: Stint start lap
            end_lap: Stint end lap
            temperature_c: Track temperature
        
        Returns:
            Dictionary with stint statistics
        """
        stint_length = end_lap - start_lap + 1
        lap_performances = []
        
        for lap in range(start_lap, end_lap + 1):
            lap_num_in_stint = lap - start_lap + 1
            perf = self.calculate_tire_performance(compound, lap_num_in_stint, stint_length, temperature_c)
            lap_performances.append(perf)
        
        avg_performance = sum(lap_performances) / len(lap_performances)
        min_performance = min(lap_performances)
        
        # Check if stint exceeds tire limits
        tire_data = TIRE_COMPOUNDS[compound]
        exceeded_max = stint_length > tire_data["max_laps"]
        past_optimal = stint_length > tire_data["optimal_window"]
        
        return {
            "compound": compound,
            "start_lap": start_lap,
            "end_lap": end_lap,
            "stint_length": stint_length,
            "avg_performance": round(avg_performance, 4),
            "min_performance": round(min_performance, 4),
            "exceeded_max_laps": exceeded_max,
            "past_optimal_window": past_optimal,
            "lap_by_lap": lap_performances,
        }
    
    def evaluate_strategy(self, strategy: List[Tuple[str, int, int]], 
                         temperature_c: float = 25.0) -> Dict:
        """
        Evaluate a complete race strategy (multiple stints).
        
        Args:
            strategy: List of (compound, start_lap, end_lap) tuples
            temperature_c: Track temperature
        
        Returns:
            Strategy evaluation with total time, performance metrics
        """
        total_pit_stops = len(strategy) - 1
        pit_time_loss = total_pit_stops * 22.0  # ~22 seconds per stop
        
        stint_results = []
        total_performance = 0.0
        total_laps = 0
        
        for compound, start_lap, end_lap in strategy:
            stint = self.simulate_stint(compound, start_lap, end_lap, temperature_c)
            stint_results.append(stint)
            
            # Weighted performance by stint length
            stint_laps = end_lap - start_lap + 1
            total_performance += stint["avg_performance"] * stint_laps
            total_laps += stint_laps
        
        avg_race_performance = total_performance / max(total_laps, 1)
        
        # Penalty for exceeding tire limits
        penalty = 0.0
        for stint in stint_results:
            if stint["exceeded_max_laps"]:
                penalty += 5.0  # 5 second penalty per exceeded stint
            if stint["past_optimal_window"]:
                penalty += 1.0  # 1 second penalty per suboptimal stint
        
        return {
            "strategy": strategy,
            "total_pit_stops": total_pit_stops,
            "pit_time_loss_seconds": pit_time_loss,
            "avg_performance": round(avg_race_performance, 4),
            "stint_details": stint_results,
            "tire_limit_penalty": penalty,
            "estimated_total_time_loss": round(pit_time_loss + penalty, 2),
        }
    
    def find_optimal_strategy(self, available_compounds: List[str] = None,
                             rain_probability: float = 0.0) -> Dict:
        """
        Find the optimal tire strategy for this race.
        
        Uses simple heuristic search over common strategies.
        In production, would use dynamic programming or genetic algorithms.
        
        Args:
            available_compounds: Available compounds for this race weekend
            rain_probability: Probability of rain
        
        Returns:
            Optimal strategy details
        """
        if available_compounds is None:
            available_compounds = ["soft", "medium", "hard"]
        
        # Generate candidate strategies
        candidates = self._generate_candidate_strategies(available_compounds)
        
        best_strategy = None
        best_score = float('inf')
        
        for strategy in candidates:
            evaluation = self.evaluate_strategy(strategy)
            score = evaluation["estimated_total_time_loss"] - (evaluation["avg_performance"] * 100)
            
            if score < best_score:
                best_score = score
                best_strategy = evaluation
        
        # Adjust for rain probability
        if rain_probability > 0.3:
            best_strategy["rain_adjustment"] = "Consider intermediate/wet tires"
            best_strategy["recommended_compounds"] = available_compounds + ["intermediate", "wet"]
        
        return best_strategy
    
    def _generate_candidate_strategies(self, compounds: List[str]) -> List[List[Tuple[str, int, int]]]:
        """Generate common tire strategy patterns."""
        strategies = []
        
        # 1-stop strategies
        if "medium" in compounds and "hard" in compounds:
            # Medium-Hard
            strategies.append([
                ("medium", 1, 25),
                ("hard", 26, self.race_laps)
            ])
            # Hard-Medium
            strategies.append([
                ("hard", 1, 30),
                ("medium", 31, self.race_laps)
            ])
        
        # 2-stop strategies
        if "soft" in compounds and "medium" in compounds and "hard" in compounds:
            # Soft-Medium-Hard
            strategies.append([
                ("soft", 1, 18),
                ("medium", 19, 38),
                ("hard", 39, self.race_laps)
            ])
            # Medium-Hard-Medium
            strategies.append([
                ("medium", 1, 20),
                ("hard", 21, 40),
                ("medium", 41, self.race_laps)
            ])
        
        # Aggressive 2-stop (for overtaking)
        if "soft" in compounds:
            strategies.append([
                ("soft", 1, 15),
                ("soft", 16, 30),
                ("medium", 31, self.race_laps)
            ])
        
        # Conservative 1-stop (for track position)
        if "hard" in compounds:
            strategies.append([
                ("hard", 1, self.race_laps)
            ])
        
        return strategies
    
    def calculate_safety_car_advantage(self, current_lap: int, 
                                      planned_pit_lap: int) -> float:
        """
        Calculate time advantage of pitting under Safety Car.
        
        Under SC, pit stop costs ~12 seconds instead of 22 seconds.
        
        Args:
            current_lap: Current race lap
            planned_pit_lap: Originally planned pit lap
        
        Returns:
            Time advantage in seconds (positive = beneficial to pit now)
        """
        if current_lap == planned_pit_lap:
            return 0.0
        
        # If SC comes out near planned pit window, advantage is minimal
        laps_difference = abs(current_lap - planned_pit_lap)
        
        if laps_difference <= 3:
            # Close to planned stop, small advantage
            return 5.0
        elif laps_difference <= 8:
            # Moderate difference, decent advantage
            return 8.0
        else:
            # Far from planned stop, large advantage
            return 10.0
    
    def get_strategy_recommendation(self, driver_position: int, 
                                   tire_degradation_sensitivity: float = 1.0) -> str:
        """
        Get strategic recommendation based on driver's situation.
        
        Args:
            driver_position: Current race position
            tire_degradation_sensitivity: How sensitive the car is to tire wear
        
        Returns:
            Strategic advice string
        """
        if driver_position <= 3:
            return "Conservative strategy: Protect position, minimize stops"
        elif driver_position <= 10:
            return "Balanced strategy: Optimize for points, consider undercut"
        elif driver_position <= 15:
            return "Aggressive strategy: Try alternative compounds, look for opportunities"
        else:
            return "Maximum aggression: Unconventional strategy, nothing to lose"


def analyze_tire_strategy_for_race(circuit_id: str, race_laps: int, 
                                  rain_probability: float = 0.0,
                                  temperature_c: float = 25.0) -> Dict:
    """
    Main function to analyze tire strategies for a race.
    
    Args:
        circuit_id: Circuit identifier
        race_laps: Total race laps
        rain_probability: Rain probability
        temperature_c: Expected track temperature
    
    Returns:
        Comprehensive strategy analysis
    """
    model = TireStrategyModel(circuit_id, race_laps)
    
    # Find optimal strategy
    optimal = model.find_optimal_strategy(rain_probability=rain_probability)
    
    # Get recommendations for different positions
    recommendations = {
        "top_3": model.get_strategy_recommendation(2),
        "midfield": model.get_strategy_recommendation(8),
        "backmarker": model.get_strategy_recommendation(18),
    }
    
    return {
        "circuit": circuit_id,
        "race_laps": race_laps,
        "optimal_strategy": optimal,
        "position_recommendations": recommendations,
        "temperature_c": temperature_c,
        "rain_probability": rain_probability,
    }


if __name__ == "__main__":
    # Test the tire strategy model
    print("Testing Tire Strategy Model...")
    
    result = analyze_tire_strategy_for_race("canada", 70, rain_probability=0.3, temperature_c=22)
    
    print(f"\nCircuit: {result['circuit']}")
    print(f"Race Laps: {result['race_laps']}")
    print(f"\nOptimal Strategy:")
    print(f"  Stops: {result['optimal_strategy']['total_pit_stops']}")
    print(f"  Avg Performance: {result['optimal_strategy']['avg_performance']:.3f}")
    print(f"  Time Loss: {result['optimal_strategy']['estimated_total_time_loss']:.1f}s")
    
    print(f"\nStint Details:")
    for stint in result['optimal_strategy']['stint_details']:
        print(f"  {stint['compound'].upper()}: L{stint['start_lap']}-L{stint['end_lap']} "
              f"(perf: {stint['avg_performance']:.3f})")
    
    print(f"\nRecommendations:")
    for pos, rec in result['position_recommendations'].items():
        print(f"  {pos}: {rec}")
