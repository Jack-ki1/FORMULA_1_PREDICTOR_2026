"""
Hugging Face dataset loader for historical race data.
Provides access to the tracinginsights/RaceData dataset for backtesting.
"""
from typing import Optional, Dict, List, Any
from backend.app.config.api_settings import api_settings


class HuggingFaceDataset:
    """Loader for Hugging Face race data datasets."""
    
    def __init__(self):
        if not api_settings.is_enabled('huggingface'):
            raise ValueError("Hugging Face integration is not enabled in settings")
        
        self.dataset_name = api_settings.HUGGINGFACE_DATASET
        self._dataset = None
    
    def load_dataset(self) -> Dict[str, Any]:
        """
        Load the Hugging Face dataset.
        
        Returns:
            Dictionary with dataset data and source info
        """
        try:
            from datasets import load_dataset
            
            dataset = load_dataset(self.dataset_name)
            self._dataset = dataset
            
            return {
                'data': {
                    'dataset_name': self.dataset_name,
                    'splits': list(dataset.keys()),
                    'features': dataset[list(dataset.keys())[0]].features,
                },
                'source': 'live',
            }
            
        except ImportError:
            return self._error_response("datasets library not installed")
        except Exception as e:
            return self._error_response(f"Hugging Face error: {str(e)}")
    
    def get_historical_race_results(self, season: int) -> Dict[str, Any]:
        """
        Get historical race results for a specific season.
        
        Args:
            season: Season year
        
        Returns:
            Dictionary with race results and source info
        """
        if not self._dataset:
            load_result = self.load_dataset()
            if load_result['source'] == 'error':
                return load_result
        
        try:
            # Assuming dataset has a structure that allows filtering by season
            # This would need to be adapted based on the actual dataset structure
            if 'train' in self._dataset:
                season_data = self._dataset['train'].filter(lambda x: x['season'] == season)
                
                return {
                    'data': season_data.to_dict(),
                    'source': 'live',
                    'season': season,
                }
            else:
                return self._error_response("Dataset structure not recognized")
                
        except Exception as e:
            return self._error_response(f"Error filtering data: {str(e)}")
    
    def get_driver_history(self, driver_code: str) -> Dict[str, Any]:
        """
        Get historical performance data for a specific driver.
        
        Args:
            driver_code: Driver code (e.g., 'VER', 'HAM')
        
        Returns:
            Dictionary with driver history and source info
        """
        if not self._dataset:
            load_result = self.load_dataset()
            if load_result['source'] == 'error':
                return load_result
        
        try:
            # Assuming dataset has driver information
            if 'train' in self._dataset:
                driver_data = self._dataset['train'].filter(lambda x: x['driver_code'] == driver_code.upper())
                
                return {
                    'data': driver_data.to_dict(),
                    'source': 'live',
                    'driver_code': driver_code,
                }
            else:
                return self._error_response("Dataset structure not recognized")
                
        except Exception as e:
            return self._error_response(f"Error filtering driver data: {str(e)}")
    
    def get_circuit_history(self, circuit_name: str) -> Dict[str, Any]:
        """
        Get historical race data for a specific circuit.
        
        Args:
            circuit_name: Circuit name or partial match
        
        Returns:
            Dictionary with circuit history and source info
        """
        if not self._dataset:
            load_result = self.load_dataset()
            if load_result['source'] == 'error':
                return load_result
        
        try:
            # Assuming dataset has circuit information
            if 'train' in self._dataset:
                circuit_data = self._dataset['train'].filter(
                    lambda x: circuit_name.lower() in x['circuit_name'].lower()
                )
                
                return {
                    'data': circuit_data.to_dict(),
                    'source': 'live',
                    'circuit_name': circuit_name,
                }
            else:
                return self._error_response("Dataset structure not recognized")
                
        except Exception as e:
            return self._error_response(f"Error filtering circuit data: {str(e)}")
    
    def get_backtest_data(self, start_season: int, end_season: int) -> Dict[str, Any]:
        """
        Get data for backtesting model accuracy.
        
        Args:
            start_season: Start season year
            end_season: End season year
        
        Returns:
            Dictionary with backtest data and source info
        """
        if not self._dataset:
            load_result = self.load_dataset()
            if load_result['source'] == 'error':
                return load_result
        
        try:
            # Get data for multiple seasons
            all_data = []
            for season in range(start_season, end_season + 1):
                season_result = self.get_historical_race_results(season)
                if season_result['source'] == 'live':
                    all_data.extend(season_result['data'])
            
            return {
                'data': all_data,
                'source': 'live',
                'seasons': list(range(start_season, end_season + 1)),
            }
            
        except Exception as e:
            return self._error_response(f"Error getting backtest data: {str(e)}")
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            'data': None,
            'source': 'error',
            'error': message,
        }
    
    def _fallback_data(self, message: str) -> Dict[str, Any]:
        """Fallback when Hugging Face is unavailable."""
        return {
            'data': [],
            'source': 'simulated',
            'note': f'Hugging Face unavailable - {message}',
        }
