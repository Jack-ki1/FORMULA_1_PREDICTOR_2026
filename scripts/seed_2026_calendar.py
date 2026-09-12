"""
Seed script for 2026 calendar and roster.
Loads the 2026 F1 calendar and driver/team lineup into the database.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db
from config.team_driver_lineup_2026 import TEAMS_2026
from data.calendar_2026 import CALENDAR_2026
from database.models import Team, Driver, Circuit, Race


def seed_calendar():
    """Seed 2026 calendar and roster into database."""
    print("Seeding 2026 calendar and roster...")
    
    try:
        # Connect to database
        db.connect()
        print("[OK] Database connection established")
        
        with db.session_scope() as session:
            # Clear existing data
            print("Clearing existing data...")
            session.query(Race).delete()
            session.query(Circuit).delete()
            session.query(Driver).delete()
            session.query(Team).delete()
            print("[OK] Existing data cleared")
            
            # Seed teams
            print("Seeding teams...")
            for team_data in TEAMS_2026:
                team = Team(
                    id=team_data['id'],
                    name=team_data['name'],
                    color_hex=team_data['color'],
                )
                session.add(team)
            print(f"[OK] Seeded {len(TEAMS_2026)} teams")
            
            # Seed drivers
            print("Seeding drivers...")
            for team_data in TEAMS_2026:
                for driver_data in team_data['drivers']:
                    driver = Driver(
                        id=driver_data['code'],
                        name=driver_data['name'],
                        number=driver_data['number'],
                        team_id=team_data['id'],
                        wet_skill=driver_data['wet_skill'],
                        reliability_base=driver_data['reliability'],
                    )
                    session.add(driver)
            print(f"[OK] Seeded {sum(len(t['drivers']) for t in TEAMS_2026)} drivers")
            
            # Seed circuits
            print("Seeding circuits...")
            from data.circuit_data import CIRCUITS
            for circuit_id, circuit_data in CIRCUITS.items():
                circuit = Circuit(
                    id=circuit_id,
                    name=circuit_data['name'],
                    location=circuit_data['location'],
                    country=circuit_data['country'],
                    laps=circuit_data['laps'],
                    length_km=circuit_data['length_km'],
                    drs_zones=circuit_data['drs_zones'],
                    overtaking_rating=circuit_data['overtaking'],
                )
                session.add(circuit)
            print(f"[OK] Seeded {len(CIRCUITS)} circuits")
            
            # Seed calendar
            print("Seeding race calendar...")
            from datetime import datetime
            for race_data in CALENDAR_2026:
                if race_data['status'] == 'cancelled':
                    continue
                
                # Parse date (handle format like "Mar 6-8")
                date_str = race_data['date']
                try:
                    # Extract first day from range format (e.g., "Mar 6-8" -> "Mar 6")
                    if '-' in date_str:
                        date_str = date_str.split('-')[0].strip()
                    
                    # Parse the date
                    race_date = datetime.strptime(f"2026-{date_str}", "%Y-%b %d")
                except ValueError:
                    print(f"Warning: Could not parse date for {race_data['name']}: {date_str}")
                    # Use a default date for races with unparseable dates
                    from datetime import timedelta
                    race_date = datetime(2026, 3, 6) + timedelta(days=int(race_data['round']) * 14)
                
                # Map circuit name to circuit ID
                circuit_id = race_data['circuit'].lower().replace(' ', '_')
                
                race = Race(
                    season=2026,
                    round=race_data['round'],
                    circuit_id=circuit_id,
                    date=race_date,
                    status=race_data['status'],
                    sprint=race_data.get('sprint', False),
                )
                session.add(race)
            
            active_races = len([r for r in CALENDAR_2026 if r['status'] != 'cancelled'])
            print(f"[OK] Seeded {active_races} races")
        
        print("\n[OK] Calendar seeding completed successfully")
        
    except Exception as e:
        print(f"\n[ERROR] Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.disconnect()


if __name__ == "__main__":
    seed_calendar()
