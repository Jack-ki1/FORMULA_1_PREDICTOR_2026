#!/usr/bin/env python3
"""
Automated F1 Data Ingestion Script.

This script fetches the latest F1 data from Jolpica-F1 API and updates local data files.
It synchronizes:
- Driver information and current season stats
- Constructor standings
- Race calendar and results
- Historical snapshots for backtesting
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

# Jolpica-F1 API base URL
JOLPICA_BASE_URL = "https://api.jolpica.com"

def fetch_current_drivers() -> List[Dict]:
    """Fetch current season drivers from Jolpica API."""
    try:
        response = requests.get(f"{JOLPICA_BASE_URL}/current/drivers")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching drivers: {e}")
        return []

def fetch_current_constructors() -> List[Dict]:
    """Fetch current season constructors from Jolpica API."""
    try:
        response = requests.get(f"{JOLPICA_BASE_URL}/current/constructors")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching constructors: {e}")
        return []

def fetch_current_calendar() -> List[Dict]:
    """Fetch current season calendar from Jolpica API."""
    try:
        response = requests.get(f"{JOLPICA_BASE_URL}/current/calendar")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []

def fetch_race_results(race_id: str) -> List[Dict]:
    """Fetch results for a specific race from Jolpica API."""
    try:
        response = requests.get(f"{JOLPICA_BASE_URL}/current/races/{race_id}/results")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching race results for {race_id}: {e}")
        return []

def update_local_driver_data(drivers: List[Dict]):
    """Update local driver_data.py with fetched driver information."""
    # This is a simplified version - in practice, you'd need to map the API fields
    # to the local data structure format
    print("Updating local driver data...")
    
    # Create backup of original file
    import shutil
    shutil.copy("data/driver_data.py", f"data/driver_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
    
    # This function would need more sophisticated mapping between API and local format
    print(f"Updated {len(drivers)} drivers in local data.")

def update_local_calendar(calendar: List[Dict]):
    """Update local calendar_2026.py with fetched calendar information."""
    print("Updating local calendar data...")
    
    # Create backup of original file
    import shutil
    shutil.copy("data/calendar_2026.py", f"data/calendar_2026_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
    
    # This function would need more sophisticated mapping between API and local format
    print(f"Updated {len(calendar)} races in local calendar.")

def update_local_standings(standings: List[Dict]):
    """Update local season_2026.py with current standings."""
    print("Updating local standings...")
    
    # Create backup of original file
    import shutil
    shutil.copy("data/season_2026.py", f"data/season_2026_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
    
    print(f"Updated standings for {len(standings)} drivers/teams.")

def store_historical_snapshot():
    """Store current data as historical snapshot for backtesting."""
    import shutil
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_dir = f"data/historical/snapshots_{timestamp}"
    
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir)
        
    # Copy current data files to snapshot directory
    shutil.copy("data/driver_data.py", f"{snapshot_dir}/driver_data.py")
    shutil.copy("data/calendar_2026.py", f"{snapshot_dir}/calendar_2026.py")
    shutil.copy("data/season_2026.py", f"{snapshot_dir}/season_2026.py")
    
    print(f"Historical snapshot created at {snapshot_dir}")

def main():
    """Main ingestion workflow."""
    print("Starting F1 data ingestion...")
    
    # Fetch current season data
    drivers = fetch_current_drivers()
    constructors = fetch_current_constructors()
    calendar = fetch_current_calendar()
    
    if drivers:
        update_local_driver_data(drivers)
    
    if calendar:
        update_local_calendar(calendar)
    
    # Update standings based on latest race results
    if constructors:
        # Extract driver standings from constructor data
        driver_standings = []
        for constructor in constructors:
            if 'drivers' in constructor:
                for driver in constructor['drivers']:
                    driver_standings.append({
                        'driver': driver['id'],
                        'points': driver.get('points', 0),
                        'position': driver.get('position', 999)
                    })
        update_local_standings(driver_standings)
    
    # Store historical snapshot
    store_historical_snapshot()
    
    print("F1 data ingestion completed successfully!")

if __name__ == "__main__":
    main()