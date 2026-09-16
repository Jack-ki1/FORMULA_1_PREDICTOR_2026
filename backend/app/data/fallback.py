from typing import Dict, Any
import datetime as dt
from backend.app.config.team_driver_lineup_2026 import get_all_drivers


class FallbackStrategy:
    """Centralized fallback strategy implementation."""
    
    @staticmethod
    def get_standings_fallback() -> Dict[str, Any]:
        """Generate simulated driver standings based on driver strength."""
        drivers = get_all_drivers()
        standings = {}
        
        # Sort drivers by strength (descending)
        sorted_drivers = sorted(drivers, key=lambda x: x['strength'], reverse=True)
        
        for i, driver in enumerate(sorted_drivers):
            standings[driver['code']] = {
                'position': i + 1,
                'points': 25 - (i * 2),
                'wins': 1 if i == 0 else 0
            }
        
        return {
            'driver_standings': standings,
            'source': 'fallback',
            'timestamp': dt.datetime.now().isoformat(),
            'note': 'Simulated standings based on driver strength'
        }
    
    @staticmethod
    def get_grid_fallback() -> Dict[str, int]:
        """Generate simulated grid positions based on driver strength."""
        drivers = get_all_drivers()
        grid_positions = {}
        
        # Sort drivers by strength (descending)
        sorted_drivers = sorted(drivers, key=lambda x: x['strength'], reverse=True)
        
        for i, driver in enumerate(sorted_drivers):
            grid_positions[driver['code']] = i + 1
        
        return {
            'grid_positions': grid_positions,
            'source': 'fallback',
            'timestamp': dt.datetime.now().isoformat(),
            'note': 'Simulated grid positions based on driver strength'
        }
    
    @staticmethod
    def get_weather_fallback() -> Dict[str, Any]:
        """Generate simulated weather data."""
        return {
            'weather': {
                'air_temp': 25.0,
                'track_temp': 45.0,
                'humidity': 40.0,
                'rain': False
            },
            'source': 'fallback',
            'timestamp': dt.datetime.now().isoformat(),
            'note': 'Simulated weather data'
        }
    
    @staticmethod
    def get_lap_times_fallback() -> Dict[str, Any]:
        """Generate simulated lap times."""
        drivers = get_all_drivers()
        lap_data = []
        
        for driver in drivers:
            base_time = 90.0 - (driver['strength'] * 0.2)  # Base lap time in seconds
            for lap in range(1, 6):  # Simulate 5 laps
                lap_data.append({
                    'driver': driver['code'],
                    'lap_number': lap,
                    'lap_time': f"{base_time + (lap * 0.1):.3f}",
                    'sector_times': [f"{base_time * 0.4:.3f}", f"{base_time * 0.3:.3f}", f"{base_time * 0.3:.3f}"],
                    'compound': 'Medium',
                    'tyre_life': lap,
                    'fresh_tyre': lap == 1,
                })
        
        return {
            'lap_times': lap_data,
            'source': 'fallback',
            'timestamp': dt.datetime.now().isoformat(),
            'note': 'Simulated lap times based on driver strength'
        }
    
    @staticmethod
    def generate_fallback_probabilities() -> Dict[str, float]:
        """Generate fallback probabilities based on driver strength."""
        drivers = get_all_drivers()
        probabilities = {}
        
        # Calculate strength-based probabilities
        total_strength = sum(driver['strength'] for driver in drivers)
        
        for driver in drivers:
            # Normalize strength to probability
            base_prob = driver['strength'] / total_strength
            probabilities[driver['code']] = base_prob
        
        # Normalize to ensure sum = 1.0
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v / total_prob for k, v in probabilities.items()}
        
        return probabilities
    
    @staticmethod
    def generate_fallback_prediction() -> Dict[str, Any]:
        """Generate a complete fallback prediction response."""
        probabilities = FallbackStrategy.generate_fallback_probabilities()
        
        return {
            'driver_probabilities': probabilities,
            'source': 'fallback',
            'timestamp': dt.datetime.now().isoformat(),
            'note': 'Fallback prediction based on driver strength',
            'model_version': 'fallback_v1.0',
            'feature_version': 'v1.0'
        }