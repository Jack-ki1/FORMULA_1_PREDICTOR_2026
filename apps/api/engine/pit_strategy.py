"""
Pit strategy prediction module.
Predicts optimal pit strategies (1-stop vs 2-stop) based on circuit and conditions.
"""
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from config.team_driver_lineup_2026 import get_all_drivers
from config.constants import PIRELLI_COMPOUNDS
from data.circuit_data import get_circuit_characteristics

logger = logging.getLogger(__name__)


class PitStrategyPredictor:
    """
    Predicts optimal pit strategies for drivers.
    Considers circuit characteristics, weather, and driver style.
    """
    
    def __init__(self):
        self.drivers = get_all_drivers()
        self.driver_map = {d['code']: d for d in self.drivers}
    
    def predict_strategy(
        self,
        driver_code: str,
        race_id: str,
        weather: str = 'dry',
        strategy_aggressiveness: float = 50,
        laps: int = None,
    ) -> Dict[str, Any]:
        """
        Predict optimal pit strategy for a driver.
        
        Args:
            driver_code: Driver code
            race_id: Race identifier
            weather: Weather condition
            strategy_aggressiveness: Aggressiveness level (0-100)
            laps: Number of laps in race
        
        Returns:
            Predicted strategy with compound choices
        """
        driver = self.driver_map.get(driver_code.upper())
        if not driver:
            return self._error_response(f"Driver not found: {driver_code}")
        
        # Get circuit information
        from data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return self._error_response(f"Race not found: {race_id}")
        
        laps = laps or race['laps']
        circuit = get_circuit_characteristics(race['circuit'].lower().replace(' ', '_'))
        
        # Determine strategy type
        two_stop_threshold = 0.65 - (strategy_aggressiveness / 100.0) * 0.4
        two_stop = np.random.random() > two_stop_threshold
        
        # Predict compound choices
        if weather == 'wet':
            strategy = self._wet_strategy(laps, driver)
        elif weather == 'mixed':
            strategy = self._mixed_strategy(laps, driver, two_stop)
        else:
            strategy = self._dry_strategy(laps, driver, two_stop, circuit)
        
        return {
            'driver_code': driver_code,
            'race_id': race_id,
            'weather': weather,
            'strategy_type': '2-stop' if two_stop else '1-stop',
            'strategy_aggressiveness': strategy_aggressiveness,
            'stops': strategy,
            'total_laps': laps,
        }
    
    def _dry_strategy(
        self,
        laps: int,
        driver: Dict,
        two_stop: bool,
        circuit: Dict,
    ) -> List[Dict[str, Any]]:
        """Predict dry weather strategy."""
        strategies = []
        
        # Determine starting compound
        start_compound = self._select_starting_compound(driver, circuit)
        
        if two_stop:
            # 2-stop strategy
            s1_laps = int(laps * (0.28 + np.random.random() * 0.08))
            s2_laps = int(laps * (0.32 + np.random.random() * 0.08))
            s3_laps = laps - s1_laps - s2_laps
            
            strategies.append({'compound': start_compound, 'laps': s1_laps})
            strategies.append({'compound': 'Medium', 'laps': s2_laps})
            strategies.append({'compound': 'Hard', 'laps': s3_laps})
        else:
            # 1-stop strategy
            s1_laps = int(laps * (0.35 + np.random.random() * 0.1))
            s2_laps = laps - s1_laps
            
            strategies.append({'compound': start_compound, 'laps': s1_laps})
            strategies.append({'compound': 'Hard', 'laps': s2_laps})
        
        return strategies
    
    def _wet_strategy(self, laps: int, driver: Dict) -> List[Dict[str, Any]]:
        """Predict wet weather strategy."""
        strategies = []
        
        # Wet strategy: Start on inters or wets
        start_compound = 'Intermediate' if np.random.random() > 0.3 else 'Wet'
        
        # Split strategy
        split_lap = int(laps * (0.45 + np.random.random() * 0.15))
        
        strategies.append({'compound': start_compound, 'laps': split_lap})
        strategies.append({'compound': 'Wet', 'laps': laps - split_lap})
        
        return strategies
    
    def _mixed_strategy(
        self,
        laps: int,
        driver: Dict,
        two_stop: bool,
    ) -> List[Dict[str, Any]]:
        """Predict mixed weather strategy."""
        strategies = []
        
        if two_stop:
            # More flexible for mixed conditions
            s1_laps = int(laps * (0.30 + np.random.random() * 0.10))
            s2_laps = int(laps * (0.30 + np.random.random() * 0.10))
            s3_laps = laps - s1_laps - s2_laps
            
            strategies.append({'compound': 'Intermediate', 'laps': s1_laps})
            strategies.append({'compound': 'Medium', 'laps': s2_laps})
            strategies.append({'compound': 'Hard', 'laps': s3_laps})
        else:
            # Conservative 1-stop
            s1_laps = int(laps * (0.40 + np.random.random() * 0.10))
            s2_laps = laps - s1_laps
            
            strategies.append({'compound': 'Intermediate', 'laps': s1_laps})
            strategies.append({'compound': 'Medium', 'laps': s2_laps})
        
        return strategies
    
    def _select_starting_compound(self, driver: Dict, circuit: Dict) -> str:
        """Select optimal starting compound."""
        # Factor in driver style and circuit characteristics
        overtaking_difficulty = circuit.get('overtaking_difficulty', 0.5)
        
        # High overtaking difficulty = favor softer compounds for position
        if overtaking_difficulty < 0.4:
            return 'Soft'
        elif overtaking_difficulty > 0.7:
            return 'Hard'
        else:
            # Random choice based on driver strength
            if driver['strength'] > 80:
                return 'Soft'
            elif driver['strength'] > 60:
                return 'Medium'
            else:
                return 'Hard'
    
    def predict_team_strategies(
        self,
        race_id: str,
        weather: str = 'dry',
        strategy_aggressiveness: float = 50,
    ) -> Dict[str, Dict[str, Any]]:
        """Predict strategies for all drivers by team."""
        all_strategies = {}
        
        for driver in self.drivers:
            strategy = self.predict_strategy(
                driver['code'],
                race_id,
                weather,
                strategy_aggressiveness,
            )
            all_strategies[driver['code']] = strategy
        
        return all_strategies
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            'error': message,
            'strategy_type': 'unknown',
            'stops': [],
        }


# Global pit strategy predictor instance
pit_strategy = PitStrategyPredictor()


class PitStrategyModel:
    """
    Pit strategy calculation engine.
    
    Provides tire strategy recommendations, pit window calculations,
    and fuel management based on race context.
    """
    
    def __init__(self):
        """Initialize pit strategy model."""
        self.tire_compounds = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']
        self.tire_lifespans = {
            'SOFT': 18,
            'MEDIUM': 26,
            'HARD': 35,
            'INTERMEDIATE': 22,
            'WET': 20
        }
        
    def calculate_pit_strategy(
        self,
        race_context: Dict[str, Any],
        current_grid: Dict[str, int],
        weather_forecast: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate optimal pit strategy for current race conditions.
        
        Args:
            race_context: Race metadata (circuit, session type, etc.)
            current_grid: Current driver positions (driver_code -> position)
            weather_forecast: Weather predictions for upcoming laps
        
        Returns:
            Dictionary with pit strategy recommendations
        """
        try:
            # Determine race length
            total_laps = race_context.get('total_laps', 70)
            current_lap = race_context.get('current_lap', 1)
            remaining_laps = total_laps - current_lap
            
            # Analyze weather impact
            weather_impact = self._analyze_weather_impact(weather_forecast)
            
            # Calculate tire strategy
            tire_strategy = self._calculate_tire_strategy(
                remaining_laps,
                weather_impact,
                race_context
            )
            
            # Calculate pit windows
            pit_windows = self._calculate_pit_windows(
                current_lap,
                total_laps,
                tire_strategy
            )
            
            return {
                'recommended_stops': len(tire_strategy),
                'tire_strategy': [
                    {
                        'compound': compound,
                        'laps': laps,
                        'recommended_lap': pit_lap
                    }
                    for (compound, laps, pit_lap) in tire_strategy
                ],
                'pit_windows': pit_windows,
                'weather_impact': weather_impact,
                'time_gain': self._estimate_time_gain(pit_windows, race_context),
                'risk_factors': self._identify_risk_factors(race_context, weather_forecast)
            }
            
        except Exception as e:
            logger.error(f"Pit strategy calculation failed: {e}")
            return self._fallback_strategy()

    def _analyze_weather_impact(self, weather_forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze weather impact on tire strategy."""
        if not weather_forecast:
            return {
                'rain_probability': 0,
                'track_drying': False,
                'recommended_compound': 'MEDIUM'
            }
        
        # Get current weather
        current = weather_forecast[0]
        
        # Calculate rain probability
        rain_prob = sum(w['rain_probability'] for w in weather_forecast[:5]) / min(5, len(weather_forecast))
        
        # Determine if track is drying
        track_drying = False
        if len(weather_forecast) > 1:
            prev_rain = weather_forecast[0]['rain_probability']
            curr_rain = weather_forecast[1]['rain_probability']
            track_drying = curr_rain < prev_rain and curr_rain < 30
        
        # Recommend compound based on weather
        if rain_prob > 60:
            recommended = 'WET'
        elif rain_prob > 30:
            recommended = 'INTERMEDIATE'
        else:
            recommended = 'MEDIUM'
        
        return {
            'rain_probability': rain_prob,
            'track_drying': track_drying,
            'recommended_compound': recommended
        }

    def _calculate_tire_strategy(
        self,
        remaining_laps: int,
        weather_impact: Dict[str, Any],
        race_context: Dict[str, Any]
    ) -> List[Tuple[str, int, int]]:
        """Calculate optimal tire strategy."""
        strategy = []
        laps_remaining = remaining_laps
        current_lap = race_context.get('current_lap', 1)
        
        # If wet conditions, start with wet tires
        if weather_impact['rain_probability'] > 60:
            compound = 'WET'
            laps = min(self.tire_lifespans[compound], laps_remaining)
            strategy.append((compound, laps, current_lap))
            laps_remaining -= laps
            current_lap += laps
        
        # Main strategy
        while laps_remaining > 0:
            # Choose compound based on conditions
            if weather_impact['track_drying']:
                compound = 'INTERMEDIATE'
            else:
                # Prefer harder compounds for remaining laps
                if laps_remaining > 30:
                    compound = 'HARD'
                elif laps_remaining > 20:
                    compound = 'MEDIUM'
                else:
                    compound = 'SOFT'
            
            laps = min(self.tire_lifespans[compound], laps_remaining)
            strategy.append((compound, laps, current_lap))
            
            laps_remaining -= laps
            current_lap += laps
        
        return strategy

    def _calculate_pit_windows(
        self,
        current_lap: int,
        total_lap: int,
        tire_strategy: List[Tuple[str, int, int]]
    ) -> List[Dict[str, Any]]:
        """Calculate optimal pit windows."""
        windows = []
        for i, (compound, laps, pit_lap) in enumerate(tire_strategy):
            if i == 0:
                continue  # Skip first stint
                
            # Calculate safe pit window
            min_lap = max(pit_lap - 2, current_lap + 3)
            max_lap = min(pit_lap + 2, total_lap - 5)
            
            windows.append({
                'stint': i,
                'recommended_lap': pit_lap,
                'window_start': min_lap,
                'window_end': max_lap,
                'compound': compound,
                'time_lost': 2.5  # Estimated time loss for pit stop
            })
            
        return windows

    def _estimate_time_gain(
        self,
        pit_windows: List[Dict[str, Any]],
        race_context: Dict[str, Any]
    ) -> float:
        """Estimate potential time gain from optimal pit strategy."""
        # Simplified calculation - in reality would use lap time deltas
        base_gain = 0.0
        for window in pit_windows:
            # Earlier stops in clean air provide more gain
            if window['recommended_lap'] < race_context.get('total_laps', 70) * 0.4:
                base_gain += 1.2
            elif window['recommended_lap'] < race_context.get('total_laps', 70) * 0.7:
                base_gain += 0.8
            else:
                base_gain += 0.5
        
        # Weather impact
        if race_context.get('weather', '').lower() == 'wet':
            base_gain *= 1.5
            
        return round(base_gain, 1)

    def _identify_risk_factors(
        self,
        race_context: Dict[str, Any],
        weather_forecast: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify potential risk factors for pit strategy."""
        risks = []
        
        # Safety car likelihood
        if race_context.get('safety_car_probability', 0) > 0.4:
            risks.append('High Safety Car probability may disrupt pit windows')
        
        # Weather volatility
        if len(weather_forecast) > 2:
            rain_change = abs(weather_forecast[0]['rain_probability'] - weather_forecast[2]['rain_probability'])
            if rain_change > 40:
                risks.append('Rapid weather changes may require adaptive strategy')
        
        # Traffic conditions
        if race_context.get('traffic_density', 0) > 0.7:
            risks.append('High traffic density may increase pit exit time')
        
        return risks

    def _fallback_strategy(self) -> Dict[str, Any]:
        """Return safe fallback strategy when calculation fails."""
        return {
            'recommended_stops': 2,
            'tire_strategy': [
                {'compound': 'MEDIUM', 'laps': 28, 'recommended_lap': 1},
                {'compound': 'HARD', 'laps': 42, 'recommended_lap': 29}
            ],
            'pit_windows': [
                {
                    'stint': 1,
                    'recommended_lap': 29,
                    'window_start': 27,
                    'window_end': 31,
                    'compound': 'HARD',
                    'time_lost': 2.5
                }
            ],
            'weather_impact': {
                'rain_probability': 0,
                'track_drying': False,
                'recommended_compound': 'MEDIUM'
            },
            'time_gain': 1.5,
            'risk_factors': ['Standard two-stop strategy']
        }
