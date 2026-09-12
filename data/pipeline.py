from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from data.validation import DataValidator
from data.provenance import DataProvenanceTracker
from data.pipeline_config import PipelineConfig
from data.pipeline_utils import validate_pipeline_configuration


class DataProvenance:
    """Track data source and processing history."""
    def __init__(self, source: str, timestamp: datetime, cache_status: str = 'hit'):
        self.source = source
        self.timestamp = timestamp
        self.cache_status = cache_status


class DataValidationError(Exception):
    """Raised when data fails validation."""
    pass

class PipelineStep:
    """Base class for pipeline processing steps."""
    def process(self, data: Dict[str, Any], provenance: DataProvenance) -> Tuple[Dict[str, Any], DataProvenance]:
        raise NotImplementedError()

class StandingsNormalizer(PipelineStep):
    """Normalize championship standings data."""
    def process(self, data: Dict[str, Any], provenance: DataProvenance) -> Tuple[Dict[str, Any], DataProvenance]:
        normalized = {}
        
        # Handle Jolpica format
        if 'MRData' in data and 'StandingsTable' in data['MRData']:
            standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
            for entry in standings:
                driver = entry['Driver']
                normalized[driver['code']] = {
                    'position': int(entry['position']),
                    'points': float(entry['points']),
                    'wins': int(entry['wins'])
                }
        
        # Handle OpenF1 format
        elif isinstance(data, list) and all('position' in item for item in data):
            for item in data:
                normalized[item['driver_code']] = {
                    'position': item['position'],
                    'points': item['points'],
                    'wins': item.get('wins', 0)
                }
        
        # Handle simulated data
        elif 'driver_standings' in data:
            for driver, stats in data['driver_standings'].items():
                normalized[driver] = {
                    'position': stats['position'],
                    'points': stats['points'],
                    'wins': stats['wins']
                }
        
        return normalized, provenance

class GridPositionValidator(PipelineStep):
    """Validate grid positions are in proper range."""
    def process(self, data: Dict[str, Any], provenance: DataProvenance) -> Tuple[Dict[str, Any], DataProvenance]:
        for driver, position in data.items():
            if not (1 <= position <= 20):
                raise DataValidationError(f"Invalid grid position {position} for {driver}")
        return data, provenance

class WeatherDataNormalizer(PipelineStep):
    """Normalize weather data from different sources."""
    def process(self, data: Dict[str, Any], provenance: DataProvenance) -> Tuple[Dict[str, Any], DataProvenance]:
        normalized = {}
        
        # Handle FastF1 weather format
        if 'weather_data' in data:
            last_entry = data['weather_data'][-1]
            normalized = {
                'air_temp': last_entry['AirTemp'],
                'track_temp': last_entry['TrackTemp'],
                'humidity': last_entry['Humidity'],
                'rain': last_entry['Rainfall'] > 0
            }
        
        # Handle OpenF1 weather format
        elif 'weather' in data:
            normalized = {
                'air_temp': data['weather'].get('air_temp'),
                'track_temp': data['weather'].get('track_temp'),
                'humidity': data['weather'].get('humidity'),
                'rain': data['weather'].get('rain', False)
            }
        
        return normalized, provenance

class DataValidationStep(PipelineStep):
    """Validate data before processing."""
    def __init__(self, data_type: str):
        self.data_type = data_type
    
    def process(self, data: Dict[str, Any], provenance: DataProvenance) -> Tuple[Dict[str, Any], DataProvenance]:
        errors = DataValidator.get_validation_errors(data, self.data_type)
        if errors:
            raise DataValidationError(f"Validation failed for {self.data_type}: {', '.join(errors)}")
        return data, provenance

class DataPipeline:
    """Centralized data processing pipeline."""
    def __init__(self):
        self.config = PipelineConfig.get_pipeline_config()
        
        # Validate configuration
        if not validate_pipeline_configuration(self.config):
            raise ValueError("Invalid pipeline configuration")
        
        self.steps = {
            'standings': [DataValidationStep('standings'), StandingsNormalizer()],
            'grid': [DataValidationStep('grid'), GridPositionValidator()],
            'weather': [DataValidationStep('weather'), WeatherDataNormalizer()]
        }
    
    def process(self, data_type: str, raw_data: Dict[str, Any], provenance: DataProvenance) -> Dict[str, Any]:
        """Process data through appropriate pipeline."""
        if data_type not in self.steps:
            raise ValueError(f"Unknown data type: {data_type}")
        
        processed_data = raw_data
        for step in self.steps[data_type]:
            processed_data, provenance = step.process(processed_data, provenance)
        
        return {
            'data': processed_data,
            'provenance': DataProvenanceTracker.create_provenance(
                source=provenance.source,
                cache_status=provenance.cache_status,
                timestamp=provenance.timestamp
            )
        }