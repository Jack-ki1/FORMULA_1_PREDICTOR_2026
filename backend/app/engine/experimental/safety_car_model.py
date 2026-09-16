"""
Safety car model - SC probability by lap-window.
Models the likelihood of safety car deployments during a race.
"""
import numpy as np
from typing import Dict, Any
from backend.app.data.circuit_data import get_circuit_characteristics


class SafetyCarModel:
    """
    Models safety car probability during races.
    Considers circuit characteristics, weather, and race phase.
    """
    
    def __init__(self):
        # Base safety car probabilities per circuit type
        self.circuit_sc_prob = {
            'street': 0.65,      # High SC probability on street circuits
            'high_speed': 0.25,  # Lower SC probability on high-speed circuits
            'technical': 0.35,   # Medium SC probability on technical circuits
            'standard': 0.30,    # Average SC probability
        }
    
    def get_safety_car_probability(
        self,
        race_id: str,
        lap: int = None,
        total_laps: int = None,
        weather: str = 'dry',
    ) -> Dict[str, Any]:
        """
        Get safety car probability for specific conditions.
        
        Args:
            race_id: Race identifier
            lap: Current lap (for lap-specific probability)
            total_laps: Total race laps
            weather: Weather condition
        
        Returns:
            Safety car probability analysis
        """
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return self._error_response(f"Race not found: {race_id}")
        
        total_laps = total_laps or race['laps']
        circuit = get_circuit_characteristics(race['circuit'].lower().replace(' ', '_'))
        
        # Base probability from circuit
        base_prob = circuit.get('safety_car_probability', 0.3)
        
        # Weather adjustment
        weather_mult = self._get_weather_multiplier(weather)
        
        # Lap-specific adjustment
        lap_mult = 1.0
        if lap is not None:
            lap_mult = self._get_lap_multiplier(lap, total_laps)
        
        # Calculate final probability
        sc_prob = base_prob * weather_mult * lap_mult
        
        # Ensure probability is within reasonable bounds
        sc_prob = max(0.05, min(0.80, sc_prob))
        
        return {
            'race_id': race_id,
            'circuit': race['circuit'],
            'lap': lap,
            'total_laps': total_laps,
            'weather': weather,
            'base_probability': base_prob,
            'weather_multiplier': weather_mult,
            'lap_multiplier': lap_mult,
            'safety_car_probability': sc_prob,
            'risk_level': self._get_risk_level(sc_prob),
        }
    
    def _get_weather_multiplier(self, weather: str) -> float:
        """Get weather multiplier for safety car probability."""
        weather_mults = {
            'dry': 1.0,
            'mixed': 1.4,
            'wet': 1.8,
        }
        return weather_mults.get(weather, 1.0)
    
    def _get_lap_multiplier(self, lap: int, total_laps: int) -> float:
        """Get lap-specific multiplier."""
        if lap is None:
            return 1.0
        
        lap_progress = lap / total_laps
        
        # Higher SC probability at start and end of race
        if lap_progress < 0.1:  # First 10% of race
            return 1.5
        elif lap_progress > 0.8:  # Last 20% of race
            return 1.3
        else:
            return 1.0
    
    def _get_risk_level(self, probability: float) -> str:
        """Get risk level from probability."""
        if probability < 0.25:
            return 'Low'
        elif probability < 0.45:
            return 'Medium'
        else:
            return 'High'
    
    def predict_safety_car_windows(
        self,
        race_id: str,
        total_laps: int = None,
        weather: str = 'dry',
    ) -> Dict[str, Any]:
        """
        Predict safety car probability across race laps.
        
        Args:
            race_id: Race identifier
            total_laps: Total race laps
            weather: Weather condition
        
        Returns:
            Safety car probability windows
        """
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return self._error_response(f"Race not found: {race_id}")
        
        total_laps = total_laps or race['laps']
        
        # Calculate probability for each lap
        lap_probabilities = []
        for lap in range(1, total_laps + 1):
            prob_info = self.get_safety_car_probability(race_id, lap, total_laps, weather)
            lap_probabilities.append({
                'lap': lap,
                'probability': prob_info['safety_car_probability'],
                'risk_level': prob_info['risk_level'],
            })
        
        # Identify high-risk windows
        high_risk_laps = [
            lp for lp in lap_probabilities
            if lp['risk_level'] == 'High'
        ]
        
        # Calculate overall race probability
        overall_prob = np.mean([lp['probability'] for lp in lap_probabilities])
        
        return {
            'race_id': race_id,
            'total_laps': total_laps,
            'weather': weather,
            'overall_probability': overall_prob,
            'lap_probabilities': lap_probabilities,
            'high_risk_laps': high_risk_laps,
            'expected_safety_cars': int(overall_prob * 3),  # Expect 0-3 SCs per race
        }
    
    def get_circuit_safety_car_rating(self, circuit_id: str) -> Dict[str, Any]:
        """
        Get safety car rating for a circuit.
        
        Args:
            circuit_id: Circuit identifier
        
        Returns:
            Circuit safety car characteristics
        """
        circuit = get_circuit_characteristics(circuit_id)
        if not circuit:
            return self._error_response(f"Circuit not found: {circuit_id}")
        
        base_prob = circuit.get('safety_car_probability', 0.3)
        overtaking = circuit.get('overtaking_difficulty', 0.5)
        
        # Determine circuit type
        if overtaking < 0.3:
            circuit_type = 'street'
        elif overtaking > 0.7:
            circuit_type = 'high_speed'
        elif circuit.get('corner_count', 15) > 17:
            circuit_type = 'technical'
        else:
            circuit_type = 'standard'
        
        return {
            'circuit_id': circuit_id,
            'circuit_type': circuit_type,
            'base_probability': base_prob,
            'risk_level': self._get_risk_level(base_prob),
            'overtaking_difficulty': overtaking,
            'characteristics': self._get_circuit_characteristics(circuit_type),
        }
    
    def _get_circuit_characteristics(self, circuit_type: str) -> Dict[str, Any]:
        """Get characteristics for circuit type."""
        characteristics = {
            'street': {
                'description': 'Street circuit with limited run-off areas',
                'typical_sc_per_race': 2.5,
                'common_causes': ['Contact', 'Track limits', 'Mechanical'],
            },
            'high_speed': {
                'description': 'High-speed circuit with good run-off',
                'typical_sc_per_race': 0.8,
                'common_causes': ['Mechanical', 'Debris'],
            },
            'technical': {
                'description': 'Technical circuit with medium speed corners',
                'typical_sc_per_race': 1.2,
                'common_causes': ['Contact', 'Mechanical', 'Spin'],
            },
            'standard': {
                'description': 'Standard circuit with balanced characteristics',
                'typical_sc_per_race': 1.0,
                'common_causes': ['Contact', 'Mechanical'],
            },
        }
        return characteristics.get(circuit_type, characteristics['standard'])
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            'error': message,
            'safety_car_probability': 0.3,
            'risk_level': 'Medium',
        }


# Global safety car model instance
safety_car_model = SafetyCarModel()
