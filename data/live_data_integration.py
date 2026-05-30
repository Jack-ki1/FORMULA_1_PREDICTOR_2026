"""
Real-Time Data Integration Module for F1 Live Data.

Integrates with Ergast Developer API and Jolpica API for live practice/qualifying results,
weather forecasts, and automated data ingestion.

Features:
- Practice session pace analysis (FP1-FP3)
- Qualifying results ingestion
- Weather forecast integration (OpenWeatherMap)
- Automated post-session data updates
- Driver penalty tracking
"""

import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# API Configuration
ERGAST_BASE_URL = "https://api.jolpi.ca/ergast/f1"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


class F1LiveDataClient:
    """Client for fetching real-time F1 data from external APIs."""
    
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=10.0)
    
    async def close(self):
        await self.session.aclose()
    
    async def get_current_season_info(self, year: int = 2026) -> Dict:
        """Fetch current season calendar and standings."""
        try:
            url = f"{ERGAST_BASE_URL}/{year}.json"
            response = await self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return {
                "season": year,
                "total_races": len(data["MRData"]["RaceTable"]["Races"]),
                "races": data["MRData"]["RaceTable"]["Races"]
            }
        except Exception as e:
            logger.error(f"Failed to fetch season info: {e}")
            return {"season": year, "error": str(e)}
    
    async def get_practice_results(self, year: int, round_num: int, session: str = "3") -> List[Dict]:
        """
        Fetch practice session results (FP1, FP2, or FP3).
        
        Args:
            year: Season year
            round_num: Race round number (1-24)
            session: Session number ("1", "2", or "3")
        
        Returns:
            List of driver results with lap times
        """
        try:
            url = f"{ERGAST_BASE_URL}/{year}/{round_num}/practice/{session}/results.json"
            response = await self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if "PracticeTable" not in data["MRData"]:
                return []
            
            results = []
            for entry in data["MRData"]["PracticeTable"]["Practices"]:
                results.append({
                    "driver_id": entry["Driver"]["driverId"],
                    "driver_name": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                    "team": entry["Constructor"]["name"],
                    "position": int(entry["position"]),
                    "time": entry.get("time"),
                    "gap": entry.get("gap"),
                    "laps": int(entry.get("laps", 0))
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to fetch practice results: {e}")
            return []
    
    async def get_qualifying_results(self, year: int, round_num: int) -> List[Dict]:
        """
        Fetch qualifying results for a race.
        
        Returns:
            List of drivers with Q1/Q2/Q3 times and grid positions
        """
        try:
            url = f"{ERGAST_BASE_URL}/{year}/{round_num}/qualifying.json"
            response = await self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if "QualifyingTable" not in data["MRData"]:
                return []
            
            results = []
            for entry in data["MRData"]["QualifyingTable"]["Qualifying"]:
                results.append({
                    "driver_id": entry["Driver"]["driverId"],
                    "driver_name": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                    "team": entry["Constructor"]["name"],
                    "grid_position": int(entry["position"]),
                    "q1_time": entry.get("Q1"),
                    "q2_time": entry.get("Q2"),
                    "q3_time": entry.get("Q3"),
                    "best_lap_time": entry.get("Q3") or entry.get("Q2") or entry.get("Q1")
                })
            
            return sorted(results, key=lambda x: x["grid_position"])
        except Exception as e:
            logger.error(f"Failed to fetch qualifying results: {e}")
            return []
    
    async def get_race_results(self, year: int, round_num: int) -> List[Dict]:
        """Fetch completed race results."""
        try:
            url = f"{ERGAST_BASE_URL}/{year}/{round_num}/results.json"
            response = await self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if "RaceTable" not in data["MRData"]:
                return []
            
            results = []
            for entry in data["MRData"]["RaceTable"]["Races"][0]["Results"]:
                results.append({
                    "driver_id": entry["Driver"]["driverId"],
                    "driver_name": f"{entry['Driver']['givenName']} {entry['Driver']['familyName']}",
                    "team": entry["Constructor"]["name"],
                    "grid_position": int(entry["grid"]),
                    "finish_position": int(entry["position"]),
                    "points": float(entry.get("points", 0)),
                    "status": entry["status"],
                    "fastest_lap_rank": int(entry.get("FastestLap", {}).get("rank", 0)),
                    "fastest_lap_time": entry.get("FastestLap", {}).get("Time", {}).get("time"),
                    "laps_completed": int(entry.get("laps", 0))
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to fetch race results: {e}")
            return []
    
    async def get_weather_forecast(self, city: str, country: str) -> Optional[Dict]:
        """
        Fetch weather forecast for race day using OpenWeatherMap API.
        
        Returns:
            Weather data including temperature, rain probability, wind speed
        """
        if not OPENWEATHER_API_KEY:
            logger.warning("OpenWeatherMap API key not configured")
            return None
        
        try:
            # Geocoding to get coordinates
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},{country}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_response = await self.session.get(geo_url)
            geo_data = geo_response.json()
            
            if not geo_data:
                return None
            
            lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
            
            # Get 5-day forecast
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
            forecast_response = await self.session.get(forecast_url)
            forecast_data = forecast_response.json()
            
            # Extract next 24 hours of forecasts
            hourly_forecasts = []
            for item in forecast_data["list"][:8]:  # 3-hour intervals, 8 = 24 hours
                hourly_forecasts.append({
                    "datetime": item["dt_txt"],
                    "temperature_c": item["main"]["temp"],
                    "humidity_pct": item["main"]["humidity"],
                    "wind_speed_ms": item["wind"]["speed"],
                    "rain_probability": item.get("pop", 0),
                    "conditions": item["weather"][0]["description"]
                })
            
            return {
                "location": f"{city}, {country}",
                "current_conditions": hourly_forecasts[0] if hourly_forecasts else None,
                "hourly_forecast": hourly_forecasts,
                "avg_temperature": sum(h["temperature_c"] for h in hourly_forecasts) / len(hourly_forecasts),
                "max_rain_probability": max(h["rain_probability"] for h in hourly_forecasts)
            }
        except Exception as e:
            logger.error(f"Failed to fetch weather forecast: {e}")
            return None
    
    async def get_driver_penalties(self, year: int, driver_id: str) -> List[Dict]:
        """Fetch driver penalties and incidents for the season."""
        # Note: Ergast doesn't provide penalty data directly
        # This would require scraping from official F1 site or other sources
        # Placeholder for future implementation
        logger.info("Driver penalty tracking requires custom scraper - not yet implemented")
        return []


async def ingest_session_data(year: int, round_num: int, session_type: str = "qualifying") -> Dict:
    """
    Main function to ingest session data and prepare it for prediction updates.
    
    Args:
        year: Season year
        round_num: Race round number
        session_type: "practice", "qualifying", or "race"
    
    Returns:
        Dictionary with ingested data ready for model updates
    """
    client = F1LiveDataClient()
    
    try:
        if session_type == "practice":
            fp3_results = await client.get_practice_results(year, round_num, "3")
            return {
                "session_type": "practice",
                "fp3_results": fp3_results,
                "long_run_pace": _analyze_long_run_pace(fp3_results),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif session_type == "qualifying":
            qual_results = await client.get_qualifying_results(year, round_num)
            return {
                "session_type": "qualifying",
                "grid_positions": {r["driver_id"]: r["grid_position"] for r in qual_results},
                "qualifying_times": {r["driver_id"]: r["best_lap_time"] for r in qual_results},
                "timestamp": datetime.utcnow().isoformat()
            }
        
        elif session_type == "race":
            race_results = await client.get_race_results(year, round_num)
            return {
                "session_type": "race",
                "results": race_results,
                "dnf_drivers": [r["driver_id"] for r in race_results if "DNF" in r["status"] or "Retired" in r["status"]],
                "fastest_lap": _find_fastest_lap(race_results),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        else:
            raise ValueError(f"Unknown session type: {session_type}")
    
    finally:
        await client.close()


def _analyze_long_run_pace(practice_results: List[Dict]) -> Dict:
    """Analyze long-run pace from practice sessions."""
    # Simplified analysis - in production, this would parse detailed timing data
    return {
        "drivers_analyzed": len(practice_results),
        "note": "Detailed long-run analysis requires timing data parsing"
    }


def _find_fastest_lap(race_results: List[Dict]) -> Optional[Dict]:
    """Find the fastest lap from race results."""
    valid_laps = [r for r in race_results if r.get("fastest_lap_time")]
    if not valid_laps:
        return None
    
    # Sort by fastest lap time (simplified - would need proper time parsing)
    fastest = min(valid_laps, key=lambda x: x["fastest_lap_time"])
    return {
        "driver_id": fastest["driver_id"],
        "driver_name": fastest["driver_name"],
        "lap_time": fastest["fastest_lap_time"]
    }


if __name__ == "__main__":
    import asyncio
    
    async def test_live_data():
        print("Testing F1 Live Data Integration...")
        
        # Test qualifying results fetch
        qual_data = await ingest_session_data(2026, 5, "qualifying")
        print(f"\nQualifying Data: {len(qual_data.get('grid_positions', {}))} drivers")
        
        # Test weather forecast
        client = F1LiveDataClient()
        weather = await client.get_weather_forecast("Montreal", "Canada")
        if weather:
            print(f"\nWeather Forecast for Montreal:")
            print(f"  Avg Temperature: {weather['avg_temperature']:.1f}°C")
            print(f"  Max Rain Probability: {weather['max_rain_probability']*100:.0f}%")
        await client.close()
    
    asyncio.run(test_live_data())
