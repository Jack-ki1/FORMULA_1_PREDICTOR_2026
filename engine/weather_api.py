"""
Weather API Integration - P1-6 Implementation.

Fetches real weather forecasts for F1 race weekends to improve rain probability predictions.
Supports OpenWeatherMap API with caching to avoid rate limits.

Usage:
    from engine.weather_api import get_race_weather_forecast
    weather = get_race_weather_forecast("monaco", "2026-06-07")
    
Configuration:
    Set OPENWEATHERMAP_API_KEY in .env file or environment variable.
"""

import os
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Weather API cache (simple in-memory cache with TTL)
_weather_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache for weather data

# Circuit coordinates (latitude, longitude) for major F1 circuits
CIRCUIT_COORDS = {
    "australia": (-37.8497, 144.9894),    # Albert Park, Melbourne
    "bahrain": (26.0325, 50.5106),        # Bahrain International Circuit
    "china": (31.3389, 121.2203),         # Shanghai International Circuit
    "japan": (34.9153, 136.5153),         # Suzuka Circuit
    "miami": (25.9581, -80.2389),         # Miami International Autodrome
    "canada": (45.5000, -73.5233),        # Circuit Gilles Villeneuve, Montreal
    "spain": (41.5700, 2.2583),           # Circuit de Barcelona-Catalunya
    "austria": (47.6197, 14.7647),        # Red Bull Ring
    "britain": (52.0750, -1.0167),        # Silverstone Circuit
    "hungary": (47.5833, 19.2500),        # Hungaroring
    "belgium": (50.4372, 5.9717),         # Circuit de Spa-Francorchamps
    "netherlands": (52.3889, 5.9222),     # Circuit Zandvoort
    "italy": (45.6156, 9.2811),           # Autodromo Nazionale Monza
    "monaco": (43.7347, 7.4206),          # Circuit de Monaco
    "azerbaijan": (40.3725, 49.7269),     # Baku City Circuit
    "singapore": (1.2914, 103.8636),      # Marina Bay Street Circuit
    "usa": (30.1458, -97.6411),           # Circuit of the Americas, Austin
    "mexico": (19.4042, -99.0908),        # Autódromo Hermanos Rodríguez
    "brazil": (-23.7017, -46.6975),       # Interlagos, São Paulo
    "las_vegas": (36.1147, -115.1733),    # Las Vegas Strip Circuit
    "qatar": (25.4889, 51.4542),          # Losail International Circuit
    "uae": (24.4672, 54.6031),            # Yas Marina Circuit, Abu Dhabi
    "madrid": (40.5167, -3.6167),         # Madrid Street Circuit (2026)
}


def get_rain_probability(circuit_id: str, race_date: str, api_key: Optional[str] = None) -> Optional[float]:
    """
    P1-6: Get rain probability from weather forecast for a race weekend.
    
    Args:
        circuit_id: Circuit ID (e.g., 'monaco', 'canada')
        race_date: Race date in YYYY-MM-DD format
        api_key: OpenWeatherMap API key (falls back to env var)
    
    Returns:
        Rain probability (0.0-1.0) or None if API unavailable
    
    Example:
        >>> get_rain_probability("monaco", "2026-06-07")
        0.35  # 35% chance of rain
    """
    api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
    
    # Return None if no API key configured (graceful degradation)
    if not api_key:
        logger.debug("OpenWeatherMap API key not configured. Using default rain probability.")
        return None
    
    # Check cache
    cache_key = f"{circuit_id}_{race_date}"
    if cache_key in _weather_cache:
        cached_time, cached_value = _weather_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            logger.debug(f"Using cached weather data for {circuit_id}")
            return cached_value
    
    # Get circuit coordinates
    coords = CIRCUIT_COORDS.get(circuit_id)
    if not coords:
        logger.warning(f"Circuit coordinates not found for {circuit_id}. Using default.")
        return None
    
    lat, lon = coords
    
    try:
        import httpx
        
        # Fetch 5-day forecast from OpenWeatherMap
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
        }
        
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        forecast_data = response.json()
        
        # Find forecast closest to race date (assume 14:00 local time)
        race_datetime = datetime.strptime(race_date, "%Y-%m-%d")
        race_datetime = race_datetime.replace(hour=14, minute=0, second=0)
        
        closest_forecast = None
        min_time_diff = float('inf')
        
        for forecast in forecast_data.get("list", []):
            forecast_time = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
            time_diff = abs((forecast_time - race_datetime).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast
        
        if not closest_forecast:
            logger.warning("No forecast data found for race date.")
            return None
        
        # Extract rain probability from forecast
        # OpenWeatherMap provides "pop" (probability of precipitation) 0-1
        rain_prob = closest_forecast.get("pop", 0.0)
        
        # Also check weather conditions for rain/drizzle/thunderstorm
        weather_conditions = closest_forecast.get("weather", [])
        has_rain = any(
            "rain" in w.get("main", "").lower() or
            "drizzle" in w.get("main", "").lower() or
            "thunderstorm" in w.get("main", "").lower()
            for w in weather_conditions
        )
        
        # If rain is in conditions but pop is low, use minimum 20%
        if has_rain and rain_prob < 0.2:
            rain_prob = max(rain_prob, 0.2)
        
        # Cache the result
        _weather_cache[cache_key] = (time.time(), rain_prob)
        
        logger.info(f"Weather forecast for {circuit_id}: {rain_prob*100:.0f}% rain probability")
        return rain_prob
        
    except ImportError:
        logger.error("httpx library not installed. Run: pip install httpx")
        return None
    except Exception as e:
        logger.error(f"Weather API request failed: {e}")
        return None


def get_weather_summary(circuit_id: str, race_date: str, api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive weather summary for race weekend.
    
    Returns:
        Dictionary with temperature, humidity, wind speed, and rain probability
    """
    api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
    
    if not api_key:
        return {"error": "API key not configured", "source": "unavailable"}
    
    coords = CIRCUIT_COORDS.get(circuit_id)
    if not coords:
        return {"error": "Circuit coordinates not found", "source": "unavailable"}
    
    lat, lon = coords
    
    try:
        import httpx
        
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
        }
        
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        forecast_data = response.json()
        
        # Get race day forecast (assume 14:00)
        race_datetime = datetime.strptime(race_date, "%Y-%m-%d").replace(hour=14)
        
        closest_forecast = None
        min_time_diff = float('inf')
        
        for forecast in forecast_data.get("list", []):
            forecast_time = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
            time_diff = abs((forecast_time - race_datetime).total_seconds())
            
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast
        
        if not closest_forecast:
            return {"error": "No forecast data found", "source": "unavailable"}
        
        return {
            "temperature_c": closest_forecast["main"]["temp"],
            "feels_like_c": closest_forecast["main"]["feels_like"],
            "humidity_pct": closest_forecast["main"]["humidity"],
            "wind_speed_ms": closest_forecast["wind"]["speed"],
            "rain_probability": closest_forecast.get("pop", 0.0),
            "conditions": closest_forecast["weather"][0]["description"],
            "source": "OpenWeatherMap",
            "timestamp": closest_forecast["dt_txt"],
        }
        
    except Exception as e:
        logger.error(f"Weather summary request failed: {e}")
        return {"error": str(e), "source": "unavailable"}


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = ["get_rain_probability", "get_weather_summary"]
