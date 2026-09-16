"""
Feature engineering module - builds the feature matrix per driver per session.
This transforms raw data into ML-ready features for prediction models.
"""
import pandas as pd
from typing import Dict, List, Optional
from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.config.constants import grid_prior_multiplier
from backend.app.data.circuit_data import get_circuit_characteristics
from backend.app.data.calendar_2026 import get_race_by_id


class FeatureEngineer:
    """Engineers features for ML prediction models."""
    
    def __init__(self):
        self.drivers = get_all_drivers()
        self.driver_map = {d['code']: d for d in self.drivers}
    
    def build_driver_features(
        self,
        driver_code: str,
        race_id: str,
        weather: str = 'dry',
        grid_position: Optional[int] = None,
        session_type: str = 'race',
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Build feature vector for a specific driver in a specific session.
        
        Args:
            driver_code: Driver code (e.g., 'VER', 'HAM')
            race_id: Race identifier
            weather: Weather condition ('dry', 'mixed', 'wet')
            grid_position: Starting grid position (for race sessions)
            session_type: Session type ('race', 'qualifying', 'practice')
            feature_weights: Weights for feature scaling
        
        Returns:
            Dictionary of engineered features
        """
        driver = self.driver_map.get(driver_code.upper())
        if not driver:
            return {}
        
        race = get_race_by_id(race_id)
        if not race:
            return {}
        
        circuit = get_circuit_characteristics(race['circuit'].lower().replace(' ', '_'))
        if not circuit:
            circuit = {}
        
        weights = feature_weights or {}
        
        # Base driver attributes
        features = {
            # Driver performance
            'strength': driver['strength'] / 100.0,  # Normalized 0-1
            'reliability': driver['reliability'] / 100.0,
            'wet_skill': driver['wet_skill'] / 100.0,
            
            # Weather adaptation
            'weather_dry': 1.0 if weather == 'dry' else 0.0,
            'weather_mixed': 1.0 if weather == 'mixed' else 0.0,
            'weather_wet': 1.0 if weather == 'wet' else 0.0,
            
            # Circuit characteristics
            'overtaking_difficulty': circuit.get('overtaking_difficulty', 0.5),
            'drs_zones': circuit.get('drs_zones_count', 2) / 4.0,  # Normalized
            'avg_speed': circuit.get('average_speed', 230) / 250.0,  # Normalized
            'corner_count': circuit.get('corner_count', 15) / 20.0,  # Normalized
            
            # Race conditions
            'safety_car_prob': circuit.get('safety_car_probability', 0.3),
            'rain_prob': circuit.get('rain_probability', 0.2),
            'base_temp': circuit.get('base_temperature', 25) / 35.0,  # Normalized
        }
        
        # Session-specific features
        if session_type == 'race':
            features['session_race'] = 1.0
            features['session_qualifying'] = 0.0
            features['session_practice'] = 0.0
            
            # Grid position features
            if grid_position:
                features['grid_position'] = grid_position / 22.0  # Normalized
                features['grid_multiplier'] = grid_prior_multiplier(grid_position)
                features['grid_weight'] = weights.get('grid_weight', 55) / 100.0
            else:
                features['grid_position'] = 0.5  # Mid-field average
                features['grid_multiplier'] = 1.0
                features['grid_weight'] = 0.0
                
        elif session_type == 'qualifying':
            features['session_race'] = 0.0
            features['session_qualifying'] = 1.0
            features['session_practice'] = 0.0
            features['grid_position'] = 0.0
            features['grid_multiplier'] = 1.0
            features['grid_weight'] = 0.0
            
        else:  # practice
            features['session_race'] = 0.0
            features['session_qualifying'] = 0.0
            features['session_practice'] = 1.0
            features['grid_position'] = 0.0
            features['grid_multiplier'] = 1.0
            features['grid_weight'] = 0.0
        
        # Feature interactions
        features['strength_x_circuit'] = features['strength'] * (1.0 - features['overtaking_difficulty'])
        features['wet_skill_x_weather'] = features['wet_skill'] * features['weather_wet']
        features['reliability_x_sc_prob'] = features['reliability'] * (1.0 - features['safety_car_prob'])
        
        # Apply feature weights
        if weights:
            wet_influence = weights.get('wet_influence', 50) / 100.0
            reliability_influence = weights.get('reliability_influence', 50) / 100.0
            
            # Adjust features based on weights
            features['wet_skill'] = features['wet_skill'] * wet_influence
            features['reliability'] = features['reliability'] * reliability_influence
        
        return features
    
    def build_session_features(
        self,
        race_id: str,
        weather: str = 'dry',
        session_type: str = 'race',
        grid_positions: Optional[Dict[str, int]] = None,
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Build feature matrix for all drivers in a session.
        
        Args:
            race_id: Race identifier
            weather: Weather condition
            session_type: Session type
            grid_positions: Dictionary of driver codes to grid positions
            feature_weights: Weights for feature scaling
        
        Returns:
            Dictionary mapping driver codes to feature vectors
        """
        all_features = {}
        
        for driver in self.drivers:
            grid_pos = grid_positions.get(driver['code']) if grid_positions else None
            features = self.build_driver_features(
                driver['code'],
                race_id,
                weather,
                grid_pos,
                session_type,
                feature_weights,
            )
            all_features[driver['code']] = features
        
        return all_features
    
    def features_to_dataframe(self, features_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Convert features dictionary to pandas DataFrame for ML models.
        
        Args:
            features_dict: Dictionary of driver features
        
        Returns:
            DataFrame with drivers as index and features as columns
        """
        return pd.DataFrame.from_dict(features_dict, orient='index')
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        # Get a sample feature set to extract names
        sample = self.build_driver_features('VER', 'au', 'dry', 1, 'race')
        return list(sample.keys())
    
    def get_feature_importance_template(self) -> Dict[str, str]:
        """
        Return template for feature importance documentation.
        Maps features to their business meaning.
        """
        return {
            'strength': 'Overall driver performance rating',
            'reliability': 'Mechanical reliability score',
            'wet_skill': 'Driver skill in wet conditions',
            'weather_dry': 'Binary: dry conditions',
            'weather_mixed': 'Binary: mixed conditions',
            'weather_wet': 'Binary: wet conditions',
            'overtaking_difficulty': 'Circuit overtaking difficulty (lower = easier)',
            'drs_zones': 'Number of DRS zones at circuit',
            'avg_speed': 'Average circuit speed',
            'corner_count': 'Number of corners at circuit',
            'safety_car_prob': 'Probability of safety car',
            'rain_prob': 'Probability of rain',
            'base_temp': 'Base circuit temperature',
            'grid_position': 'Starting grid position',
            'grid_multiplier': 'Historical pole-to-win multiplier',
            'grid_weight': 'Weight given to grid position',
            'strength_x_circuit': 'Interaction: driver strength vs circuit',
            'wet_skill_x_weather': 'Interaction: wet skill vs weather',
            'reliability_x_sc_prob': 'Interaction: reliability vs safety car probability',
        }


# Global feature engineer instance
feature_engineer = FeatureEngineer()
