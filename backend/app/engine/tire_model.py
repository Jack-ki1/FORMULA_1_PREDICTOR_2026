"""
Tire model - degradation curves per compound/circuit.
Models tire wear and performance degradation across stints.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from backend.app.config.constants import PIRELLI_COMPOUNDS


class TireModel:
    """
    Models tire degradation and performance characteristics.
    Provides degradation curves per compound and circuit.
    """
    
    def __init__(self):
        # Base degradation rates per compound (per lap)
        self.compound_degradation = {
            'Soft': 0.025,      # 2.5% per lap
            'Medium': 0.018,    # 1.8% per lap
            'Hard': 0.012,      # 1.2% per lap
            'Intermediate': 0.020,  # 2.0% per lap
            'Wet': 0.015,       # 1.5% per lap
        }
        
        # Circuit-specific multipliers
        self.circuit_multipliers = {
            'high_wear': 1.3,      # Circuits with high tire wear
            'medium_wear': 1.0,    # Average tire wear
            'low_wear': 0.7,       # Circuits with low tire wear
        }
    
    def get_degradation_rate(
        self,
        compound: str,
        circuit_type: str = 'medium_wear',
        weather: str = 'dry',
    ) -> float:
        """
        Get tire degradation rate for specific conditions.
        
        Args:
            compound: Tire compound
            circuit_type: Circuit wear characteristics
            weather: Weather condition
        
        Returns:
            Degradation rate per lap (0-1)
        """
        base_rate = self.compound_degradation.get(compound, 0.02)
        circuit_mult = self.circuit_multipliers.get(circuit_type, 1.0)
        
        # Weather adjustment
        weather_mult = 1.0
        if weather == 'wet':
            weather_mult = 0.8  # Slower degradation in wet
        elif weather == 'mixed':
            weather_mult = 0.9
        
        return base_rate * circuit_mult * weather_mult
    
    def calculate_tire_life(
        self,
        compound: str,
        circuit_type: str = 'medium_wear',
        weather: str = 'dry',
        starting_life: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculate tire life characteristics.
        
        Args:
            compound: Tire compound
            circuit_type: Circuit wear characteristics
            weather: Weather condition
            starting_life: Starting tire life (laps)
        
        Returns:
            Tire life information
        """
        degradation_rate = self.get_degradation_rate(compound, circuit_type, weather)
        
        # Calculate effective tire life (laps before performance drops significantly)
        effective_life = int(100 / degradation_rate) - starting_life
        
        # Calculate performance profile over life
        performance_profile = []
        for lap in range(effective_life + 1):
            total_life = starting_life + lap
            performance = self._calculate_performance(compound, total_life, degradation_rate)
            performance_profile.append({
                'lap': lap,
                'tire_life': total_life,
                'performance': performance,
            })
        
        return {
            'compound': compound,
            'degradation_rate': degradation_rate,
            'effective_life': effective_life,
            'starting_life': starting_life,
            'performance_profile': performance_profile,
        }
    
    def _calculate_performance(self, compound: str, tire_life: int, degradation_rate: float) -> float:
        """Calculate tire performance factor (0-1)."""
        # Performance drops as tire life increases
        performance = 1.0 - (tire_life * degradation_rate)
        return max(0.5, min(1.0, performance))  # Never drop below 50%
    
    def get_optimal_stint_length(
        self,
        compound: str,
        circuit_type: str = 'medium_wear',
        weather: str = 'dry',
    ) -> int:
        """
        Get optimal stint length for a compound.
        
        Args:
            compound: Tire compound
            circuit_type: Circuit wear characteristics
            weather: Weather condition
        
        Returns:
            Optimal stint length in laps
        """
        degradation_rate = self.get_degradation_rate(compound, circuit_type, weather)
        
        # Optimal stint is when performance drops to ~75%
        optimal_life = int(25 / degradation_rate)
        
        return max(10, min(40, optimal_life))  # Reasonable bounds
    
    def compare_compounds(
        self,
        circuit_type: str = 'medium_wear',
        weather: str = 'dry',
    ) -> Dict[str, Dict[str, Any]]:
        """Compare all compounds for given conditions."""
        comparison = {}
        
        for compound in PIRELLI_COMPOUNDS.keys():
            comparison[compound] = {
                'degradation_rate': self.get_degradation_rate(compound, circuit_type, weather),
                'optimal_stint': self.get_optimal_stint_length(compound, circuit_type, weather),
                'tire_life': self.calculate_tire_life(compound, circuit_type, weather),
            }
        
        return comparison
    
    def predict_pit_window(
        self,
        current_lap: int,
        compound: str,
        circuit_type: str = 'medium_wear',
        weather: str = 'dry',
        tire_life: int = 0,
    ) -> Dict[str, Any]:
        """
        Predict optimal pit window for current tire.
        
        Args:
            current_lap: Current race lap
            compound: Current compound
            circuit_type: Circuit wear characteristics
            weather: Weather condition
            tire_life: Current tire life
        
        Returns:
            Pit window prediction
        """
        optimal_stint = self.get_optimal_stint_length(compound, circuit_type, weather)
        remaining_life = optimal_stint - tire_life
        
        earliest_pit = current_lap + max(5, remaining_life - 10)
        latest_pit = current_lap + remaining_life + 5
        
        return {
            'current_lap': current_lap,
            'compound': compound,
            'tire_life': tire_life,
            'optimal_stint': optimal_stint,
            'remaining_life': remaining_life,
            'earliest_pit': earliest_pit,
            'latest_pit': latest_pit,
            'recommended_pit': current_lap + remaining_life - 3,
        }


# Global tire model instance
tire_model = TireModel()
