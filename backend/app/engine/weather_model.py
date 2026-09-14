"""
Weather model - wet-skill blending and weather prediction.
Models how weather conditions affect driver performance.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.config.constants import WEATHER_CONDITIONS


class WeatherModel:
    """
    Models weather effects on driver performance.
    Blends wet-weather skill with overall strength based on conditions.
    """
    
    def __init__(self):
        self.drivers = get_all_drivers()
        self.driver_map = {d['code']: d for d in self.drivers}
    
    def calculate_weather_impact(
        self,
        driver_code: str,
        weather: str,
        wet_influence: float = 50,
    ) -> Dict[str, Any]:
        """
        Calculate how weather affects a driver's performance.
        
        Args:
            driver_code: Driver code
            weather: Weather condition (dry, mixed, wet)
            wet_influence: How much wet skill matters (0-100)
        
        Returns:
            Weather impact analysis
        """
        driver = self.driver_map.get(driver_code.upper())
        if not driver:
            return self._error_response(f"Driver not found: {driver_code}")
        
        base_strength = driver['strength']
        wet_skill = driver['wet_skill']
        
        # Calculate wet weather factor
        wet_factor = wet_influence / 50.0  # 50 = baseline
        
        if weather == 'dry':
            # Dry conditions: use base strength
            effective_strength = base_strength
            wet_contribution = 0.0
        
        elif weather == 'mixed':
            # Mixed conditions: blend strength and wet skill
            wet_weight = 0.28 * wet_factor  # Original JSX formula
            effective_strength = base_strength * (1 - wet_weight) + wet_skill * wet_weight
            wet_contribution = wet_weight
        
        else:  # wet
            # Wet conditions: emphasize wet skill
            wet_weight = 0.55 * wet_factor  # Original JSX formula
            effective_strength = base_strength * (1 - wet_weight) + wet_skill * wet_weight
            wet_contribution = wet_weight
        
        # Calculate performance change
        performance_change = effective_strength - base_strength
        performance_change_pct = (performance_change / base_strength) * 100
        
        return {
            'driver_code': driver_code,
            'weather': weather,
            'base_strength': base_strength,
            'wet_skill': wet_skill,
            'wet_influence': wet_influence,
            'effective_strength': effective_strength,
            'wet_contribution': wet_contribution,
            'performance_change': performance_change,
            'performance_change_pct': performance_change_pct,
            'weather_advantage': self._calculate_weather_advantage(driver, weather),
        }
    
    def _calculate_weather_advantage(self, driver: Dict, weather: str) -> float:
        """Calculate weather advantage for a driver."""
        if weather == 'dry':
            return 0.0  # No advantage in dry conditions
        
        # Advantage = wet skill - average wet skill
        avg_wet_skill = np.mean([d['wet_skill'] for d in self.drivers])
        advantage = driver['wet_skill'] - avg_wet_skill
        
        return advantage
    
    def get_weather_rankings(
        self,
        weather: str,
        wet_influence: float = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get driver rankings for specific weather conditions.
        
        Args:
            weather: Weather condition
            wet_influence: Wet skill influence
        
        Returns:
            Ranked list of drivers by effective strength
        """
        rankings = []
        
        for driver in self.drivers:
            impact = self.calculate_weather_impact(driver['code'], weather, wet_influence)
            rankings.append({
                'driver_code': driver['code'],
                'driver_name': driver['name'],
                'team': driver['team_name'],
                'effective_strength': impact['effective_strength'],
                'weather_advantage': impact['weather_advantage'],
            })
        
        # Sort by effective strength
        rankings.sort(key=lambda x: x['effective_strength'], reverse=True)
        
        # Add positions
        for i, ranking in enumerate(rankings, 1):
            ranking['position'] = i
        
        return rankings
    
    def predict_race_weather(
        self,
        race_id: str,
        base_rain_prob: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Predict weather conditions for a race.
        
        Args:
            race_id: Race identifier
            base_rain_prob: Base probability of rain
        
        Returns:
            Weather prediction
        """
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return self._error_response(f"Race not found: {race_id}")
        
        # Use circuit-specific base rain probability
        circuit_rain_prob = race.get('base_rain', base_rain_prob) / 100.0
        
        # Simple weather prediction model
        # In production, this would use real weather API
        rand = np.random.random()
        
        if rand < circuit_rain_prob * 0.3:
            weather = 'wet'
            confidence = 0.7
        elif rand < circuit_rain_prob:
            weather = 'mixed'
            confidence = 0.6
        else:
            weather = 'dry'
            confidence = 0.8
        
        return {
            'race_id': race_id,
            'predicted_weather': weather,
            'confidence': confidence,
            'rain_probability': circuit_rain_prob,
            'circuit': race['circuit'],
        }
    
    def get_weather_conditions_description(self, weather: str) -> Dict[str, Any]:
        """Get detailed description of weather conditions."""
        conditions = WEATHER_CONDITIONS.get(weather, WEATHER_CONDITIONS['dry'])
        
        descriptions = {
            'dry': {
                'description': 'Optimal racing conditions with full grip',
                'tire_impact': 'Standard tire degradation',
                'overtaking': 'Normal overtaking difficulty',
                'risk_factors': ['Mechanical failure', 'Driver error'],
            },
            'mixed': {
                'description': 'Variable grip conditions, changing track surface',
                'tire_impact': 'Accelerated tire degradation on wet patches',
                'overtaking': 'Increased overtaking opportunities in tricky conditions',
                'risk_factors': ['Mechanical failure', 'Driver error', 'Loss of grip'],
            },
            'wet': {
                'description': 'Reduced grip, standing water, spray',
                'tire_impact': 'Heavy tire wear on intermediate/wet tires',
                'overtaking': 'Variable - easier in straights, harder in corners',
                'risk_factors': ['Mechanical failure', 'Driver error', 'Aquaplaning', 'Visibility'],
            },
        }
        
        return {
            'weather': weather,
            'icon': conditions['icon'],
            'label': conditions['label'],
            'default_compound': conditions['compound_default'],
            'details': descriptions.get(weather, descriptions['dry']),
        }
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            'error': message,
            'weather_advantage': 0.0,
            'effective_strength': 0.0,
        }


# Global weather model instance
weather_model = WeatherModel()
