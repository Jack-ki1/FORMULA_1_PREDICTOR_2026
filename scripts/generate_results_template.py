"""
Generate results template script - creates a template for race results entry.
Provides a form structure for entering race results manually if API data is unavailable.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config.team_driver_lineup_2026 import get_all_drivers


def generate_results_template(race_id: str):
    """
    Generate a template for race results entry.
    
    Args:
        race_id: Race identifier
    """
    print(f"Generating results template for race {race_id}...")
    
    try:
        drivers = get_all_drivers()
        
        template = {
            'race_id': race_id,
            'session': 'race',
            'results': [],
        }
        
        # Create template entries for all drivers
        for driver in drivers:
            template['results'].append({
                'driver_code': driver['code'],
                'driver_name': driver['name'],
                'team': driver['team_name'],
                'position': None,  # To be filled
                'points': None,  # To be calculated
                'status': 'Finished',  # Finished, DNF, DNS, etc.
                'grid': None,  # Grid position
                'laps': None,  # Number of laps completed
                'fastest_lap': False,
            })
        
        # Print template structure
        print("\n=== Results Template ===")
        print(f"Race ID: {template['race_id']}")
        print(f"Session: {template['session']}")
        print(f"Number of drivers: {len(template['results'])}")
        
        print("\nTemplate structure:")
        print("```json")
        import json
        print(json.dumps(template, indent=2))
        print("```")
        
        # Generate CSV template
        print("\n=== CSV Template ===")
        print("driver_code,driver_name,team,position,points,status,grid,laps,fastest_lap")
        for result in template['results']:
            print(f"{result['driver_code']},{result['driver_name']},{result['team']},,,,,,")
        
        print("\n✓ Results template generated")
        print("Fill in the missing fields and use this data to update the database")
        
        return template
        
    except Exception as e:
        print(f"\n✗ Template generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Get race ID from command line
    if len(sys.argv) > 1:
        race_id = sys.argv[1]
    else:
        race_id = "latest"  # Placeholder
    
    generate_results_template(race_id)
