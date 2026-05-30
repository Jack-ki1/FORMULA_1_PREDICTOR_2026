"""
Enhanced Weather Model v3.0 — Real-time forecasts and detailed modeling.

Integrates with OpenWeatherMap API for:
- Hourly rain probability forecasts
- Temperature impact on tire degradation
- Humidity effects on engine performance
- Wind speed impact on aerodynamics
"""

import logging
from typing import Optional, Dict
import os
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherModel:
    """Enhanced weather modeling with real-time forecasts."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather model.
        
        Args:
            api_key: OpenWeatherMap API key (from env var WEATHER_API_KEY)
        """
        self.api_key = api_key or os.getenv("WEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_forecast(self, lat: float, lon: float, race_date: str) -> Dict:
        """
        Get detailed weather forecast for race weekend.
        
        Args:
            lat: Circuit latitude
            lon: Circuit longitude
            race_date: Race date (YYYY-MM-DD)
        
        Returns:
            Detailed weather data including rain timing, temperature, humidity
        """
        if not self.api_key:
            logger.warning("No weather API key provided. Using default values.")
            return self._get_default_forecast()
        
        try:
            # Get 5-day/3-hour forecast
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse forecast for race date
            race_forecast = []
            for forecast in data["list"]:
                forecast_time = datetime.fromisoformat(forecast["dt_txt"])
                forecast_date = forecast_time.strftime("%Y-%m-%d")
                
                if forecast_date == race_date:
                    race_forecast.append({
                        "time": forecast_time,
                        "temperature": forecast["main"]["temp"],
                        "feels_like": forecast["main"]["feels_like"],
                        "humidity": forecast["main"]["humidity"],
                        "rain_probability": forecast.get("pop", 0.0),
                        "rain_volume": forecast.get("rain", {}).get("3h", 0.0),
                        "wind_speed": forecast["wind"]["speed"],
                        "wind_direction": forecast["wind"]["deg"],
                        "cloudiness": forecast["clouds"]["all"],
                        "description": forecast["weather"][0]["description"],
                    })
            
            return {
                "race_date": race_date,
                "hourly_forecast": race_forecast,
                "max_rain_probability": max(f["rain_probability"] for f in race_forecast) if race_forecast else 0.0,
                "avg_temperature": sum(f["temperature"] for f in race_forecast) / len(race_forecast) if race_forecast else 20.0,
                "avg_humidity": sum(f["humidity"] for f in race_forecast) / len(race_forecast) if race_forecast else 50.0,
            }
            
        except Exception as e:
            logger.error(f"Failed to get weather forecast: {e}")
            return self._get_default_forecast()
    
    def _get_default_forecast(self) -> Dict:
        """Return default forecast when API unavailable."""
        return {
            "race_date": datetime.now().strftime("%Y-%m-%d"),
            "hourly_forecast": [],
            "max_rain_probability": 0.2,
            "avg_temperature": 20.0,
            "avg_humidity": 50.0,
        }
    
    def compute_tire_degradation_factor(self, temperature: float, humidity: float) -> float:
        """
        Compute tire degradation factor based on weather conditions.
        
        Higher temperature → faster degradation
        Higher humidity → slightly reduced degradation
        
        Returns:
            Multiplier: 1.0 = baseline, >1.0 = faster degradation
        """
        # Temperature effect: degradation increases exponentially above 30°C
        temp_factor = 1.0 + max(0, (temperature - 30) / 100.0)
        
        # Humidity effect: high humidity reduces degradation slightly
        humidity_factor = 1.0 - (humidity - 50) / 500.0
        
        return max(0.8, min(1.3, temp_factor * humidity_factor))
    
    def compute_engine_power_factor(self, temperature: float, humidity: float, altitude_m: float = 0) -> float:
        """
        Compute engine power factor based on weather and altitude.
        
        Hot air is less dense → less oxygen → reduced power
        High altitude → thinner air → significant power loss
        High humidity → minor power reduction
        
        Returns:
            Multiplier: 1.0 = baseline power, <1.0 = power loss
        """
        # Temperature effect: power decreases above 25°C
        temp_effect = 1.0 - max(0, (temperature - 25) / 200.0)
        
        # Humidity effect: minor reduction
        humidity_effect = 1.0 - (humidity / 1000.0)
        
        # Altitude effect: significant power loss at high altitude
        # Mexico City (~2200m) loses ~25% power
        altitude_effect = 1.0 - (altitude_m / 8800.0)
        
        return max(0.7, min(1.0, temp_effect * humidity_effect * altitude_effect))
    
    def get_rain_timing(self, forecast: Dict) -> Dict:
        """
        Analyze rain timing throughout the day.
        
        Returns:
            Dict with rain probability by race phase:
            - pre_race, laps_1_20, laps_21_40, laps_41_end
        """
        if not forecast.get("hourly_forecast"):
            return {
                "pre_race": 0.0,
                "laps_1_20": 0.0,
                "laps_21_40": 0.0,
                "laps_41_end": 0.0,
            }
        
        # Group forecasts by race phase (simplified)
        hourly = forecast["hourly_forecast"]
        
        return {
            "pre_race": hourly[0]["rain_probability"] if len(hourly) > 0 else 0.0,
            "laps_1_20": hourly[1]["rain_probability"] if len(hourly) > 1 else 0.0,
            "laps_21_40": hourly[2]["rain_probability"] if len(hourly) > 2 else 0.0,
            "laps_41_end": hourly[3]["rain_probability"] if len(hourly) > 3 else 0.0,
        }


def get_weather_for_circuit(circuit_id: str, race_date: str) -> Dict:
    """
    Convenience function to get weather for a specific circuit.
    
    Usage:
        weather = get_weather_for_circuit("canada", "2026-06-14")
        print(f"Rain probability: {weather['max_rain_probability']}")
    """
    from data.circuit_data import get_circuit
    
    circuit = get_circuit(circuit_id)
    
    # Get circuit coordinates (approximate)
    circuit_coords = {
        "canada": (45.5, -73.5),
        "monaco": (43.7, 7.4),
        "silverstone": (52.1, -1.0),
        "monza": (45.6, 9.3),
        "spa": (50.4, 5.9),
    }
    
    lat, lon = circuit_coords.get(circuit_id, (50.0, 0.0))
    
    weather_model = WeatherModel()
    return weather_model.get_forecast(lat, lon, race_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing weather model...")
    weather = get_weather_for_circuit("canada", "2026-06-14")
    
    print(f"Race date: {weather['race_date']}")
    print(f"Max rain probability: {weather['max_rain_probability']:.0%}")
    print(f"Avg temperature: {weather['avg_temperature']:.1f}°C")
    print(f"Avg humidity: {weather['avg_humidity']:.0f}%")
