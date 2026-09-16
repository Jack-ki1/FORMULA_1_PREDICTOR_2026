from typing import Dict, Any, List


class DataValidator:
    """Centralized data validation for all data sources."""
    
    @staticmethod
    def validate_driver_standings(data: Dict[str, Any]) -> bool:
        """Validate driver standings data structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for Jolpica format
        if 'MRData' in data and 'StandingsTable' in data['MRData']:
            standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            return len(standings) > 0 and all(
                'Driver' in entry and 'position' in entry for entry in standings
            )
        
        # Check for OpenF1 format
        if isinstance(data, list) and len(data) > 0:
            return all('driver_code' in item and 'position' in item for item in data)
        
        return False
    
    @staticmethod
    def validate_grid_positions(data: Dict[str, Any]) -> bool:
        """Validate grid positions are integers within the real grid size."""
        if not isinstance(data, dict):
            return False
        from backend.app.config.constants import grid_size
        max_pos = grid_size()

        for position in data.values():
            try:
                pos_int = int(position)
                if not (1 <= pos_int <= max_pos):
                    return False
            except (ValueError, TypeError):
                return False
        return True
    
    @staticmethod
    def validate_weather_data(data: Dict[str, Any]) -> bool:
        """Validate weather data structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for FastF1 format
        if 'weather_data' in data:
            return len(data['weather_data']) > 0
        
        # Check for OpenF1 format
        if 'weather' in data:
            return 'air_temp' in data['weather'] or 'track_temp' in data['weather']
        
        return False
    
    @staticmethod
    def validate_lap_times(data: List[Dict[str, Any]]) -> bool:
        """Validate lap times data structure."""
        if not isinstance(data, list):
            return False
        
        for lap in data:
            if not isinstance(lap, dict):
                return False
            if 'lap_time' not in lap or 'driver' not in lap:
                return False
            if lap['lap_time'] is not None:
                try:
                    float(lap['lap_time'])
                except (ValueError, TypeError):
                    return False
        return True
    
    @staticmethod
    def validate_session_results(data: List[Dict[str, Any]]) -> bool:
        """Validate session results data structure."""
        if not isinstance(data, list):
            return False
        
        for result in data:
            if not isinstance(result, dict):
                return False
            if 'position' not in result or 'driver' not in result:
                return False
            try:
                int(result['position'])
            except (ValueError, TypeError):
                return False
        return True
    
    @staticmethod
    def get_validation_errors(data: Dict[str, Any], data_type: str) -> List[str]:
        """Get detailed validation errors for data."""
        errors = []
        
        if data_type == 'standings':
            if not DataValidator.validate_driver_standings(data):
                errors.append(f"Invalid standings data structure for {data_type}")
        elif data_type == 'grid':
            if not DataValidator.validate_grid_positions(data):
                from backend.app.config.constants import grid_size
                errors.append(f"Invalid grid positions: must be integers 1-{grid_size()}")
        elif data_type == 'weather':
            if not DataValidator.validate_weather_data(data):
                errors.append("Invalid weather data structure")
        elif data_type == 'lap_times':
            if not DataValidator.validate_lap_times(data):
                errors.append("Invalid lap times data structure")
        elif data_type == 'session_results':
            if not DataValidator.validate_session_results(data):
                errors.append("Invalid session results data structure")

        return errors

def validate_probability_data(data: Dict[str, Any]) -> bool:
    """Validate probability data structure."""
    if not isinstance(data, dict):
        return False

    # Check for driver probabilities
    if 'driver_probabilities' in data:
        driver_probs = data['driver_probabilities']
        if not isinstance(driver_probs, dict):
            return False

        # Check probabilities sum to 1.0
        total_prob = sum(driver_probs.values())
        if not (0.99 <= total_prob <= 1.01):  # Allow small floating point errors
            return False

        # Check individual probabilities are valid
        for prob in driver_probs.values():
            if not (0.0 <= prob <= 1.0):
                return False

    return True

def validate_prediction_data(data: Dict[str, Any]) -> List[str]:
    """Validate prediction request data structure."""
    errors = []

    if not isinstance(data, dict):
        errors.append("Prediction data must be a dictionary")
        return errors

    # Check required fields
    required_fields = ['race_id', 'session_type', 'target']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate race_id
    if 'race_id' in data and not isinstance(data['race_id'], str):
        errors.append("race_id must be a string")

    # Validate session_type
    if 'session_type' in data:
        valid_sessions = ['race', 'qualifying', 'practice']
        if data['session_type'] not in valid_sessions:
            errors.append(f"session_type must be one of: {valid_sessions}")

    # Validate target
    if 'target' in data:
        valid_targets = ['winner', 'podium', 'points', 'q3']
        if data['target'] not in valid_targets:
            errors.append(f"target must be one of: {valid_targets}")

    # Validate drivers if provided
    if 'drivers' in data:
        if not isinstance(data['drivers'], list):
            errors.append("drivers must be a list")
        elif len(data['drivers']) < 1 or len(data['drivers']) > 23:
            from backend.app.config.constants import grid_size
            errors.append(f"drivers list must contain 1-{grid_size()} drivers")

    # Validate simulation_count if provided
    if 'simulation_count' in data:
        try:
            sim_count = int(data['simulation_count'])
            if not (100 <= sim_count <= 100000):
                errors.append("simulation_count must be between 100 and 100000")
        except (ValueError, TypeError):
            errors.append("simulation_count must be an integer")
    
    return errors