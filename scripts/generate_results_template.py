"""
Generate Race Results Template.

Creates a JSON template with all drivers for easy post-race evaluation.

Usage:
    py scripts/generate_results_template.py --race canada
    py scripts/generate_results_template.py --race monaco --output my_template.json
"""

import sys
import os
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_template(circuit_id: str, output_file: str = None):
    """Generate a race results template for the specified circuit."""
    from data.driver_data import get_all_drivers
    
    if output_file is None:
        output_file = f"{circuit_id}_results.json"
    
    # Get all drivers
    drivers = get_all_drivers()
    
    # Create template with placeholder positions
    template = {}
    for driver in drivers:
        driver_id = driver["id"]
        template[driver_id] = 0  # Placeholder, user fills in actual positions
    
    # Sort by typical performance (optional, just for convenience)
    # In practice, users will reorder based on actual results
    
    # Write template
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    print(f"[SUCCESS] Template generated: {output_file}")
    print(f"\nInstructions:")
    print(f"1. Open {output_file} in a text editor")
    print(f"2. Replace '0' with actual finishing positions (1-20)")
    print(f"3. Use >20 for DNFs (Did Not Finish)")
    print(f"4. Save the file")
    print(f"5. Run: py main.py evaluate-race --race {circuit_id} --results {output_file}")
    print(f"\nExample:")
    print(f'  "verstappen": 1,')
    print(f'  "hamilton": 2,')
    print(f'  "leclerc": 3,')
    print(f'  ...')
    print(f'  "stroll": 22  # DNF')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate race results template")
    parser.add_argument("--race", "-r", required=True, help="Circuit ID (e.g., canada, monaco)")
    parser.add_argument("--output", "-o", default=None, help="Output filename (default: <circuit>_results.json)")
    
    args = parser.parse_args()
    
    generate_template(args.race, args.output)
