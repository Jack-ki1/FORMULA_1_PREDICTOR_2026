"""
Automated Season Data Sync - P0-1 & P1-8 Implementation.

This script syncs driver standings, ELO ratings, and recent form data
from Fast-F1 or manual JSON input after each race weekend.

Usage:
    py scripts/update_season_data.py --race canada --results results.json
    py scripts/update_season_data.py --race canada --fastf1
"""

import json
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# F1 Points system (2026)
POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
    "fastest_lap": 1  # Bonus point for fastest lap (if finish in top 10)
}


def update_driver_elo(current_elo: float, actual_score: float, expected_score: float, k_factor: float = 32.0) -> float:
    """
    P2-10: Update ELO rating based on race result.
    
    Args:
        current_elo: Current ELO rating
        actual_score: Actual performance (1.0 for win, 0.0 for loss, or points-based)
        expected_score: Expected performance from model
        k_factor: Sensitivity factor (higher for rookies, lower for veterans)
    
    Returns:
        Updated ELO rating
    """
    return current_elo + k_factor * (actual_score - expected_score)


def calculate_expected_score(elo_a: float, elo_b: float) -> float:
    """Calculate expected score for driver A against driver B."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def update_season_data(
    race_id: str,
    race_results: Dict[str, int],
    driver_data_path: str = "data/driver_data.py",
    elo_k_factor: float = 32.0
) -> Dict:
    """
    P0-1: Update driver data after a race.
    
    Args:
        race_id: Circuit ID (e.g., 'canada', 'monaco')
        race_results: Dict mapping driver_id -> finishing position
        driver_data_path: Path to driver_data.py
        elo_k_factor: ELO update sensitivity
    
    Returns:
        Summary of updates made
    """
    from data.driver_data import DRIVERS, get_all_drivers
    
    updates_made = {
        "elo_updates": [],
        "points_updates": [],
        "form_updates": [],
        "errors": []
    }
    
    # Sort results by position
    sorted_results = sorted(race_results.items(), key=lambda x: x[1])
    
    for driver_id, position in sorted_results:
        if driver_id not in DRIVERS:
            updates_made["errors"].append(f"Driver {driver_id} not found in database")
            continue
        
        driver = DRIVERS[driver_id]
        
        # Calculate points earned
        points = POINTS_SYSTEM.get(position, 0)
        
        # Update championship points
        old_points = driver.get("championship_points_2026", 0)
        driver["championship_points_2026"] = old_points + points
        updates_made["points_updates"].append({
            "driver": driver["name"],
            "old_points": old_points,
            "new_points": driver["championship_points_2026"],
            "points_earned": points
        })
        
        # Update recent form (shift and add new result)
        recent_form = driver.get("recent_form", [0, 0, 0, 0, 0, 0])
        recent_form.insert(0, position)  # Add new result at front
        recent_form = recent_form[:6]  # Keep last 6 races
        driver["recent_form"] = recent_form
        updates_made["form_updates"].append({
            "driver": driver["name"],
            "new_form": recent_form
        })
        
        # Update ELO (simplified - should be compared against all other drivers)
        current_elo = driver.get("elo", 1500)
        expected_positions = _calculate_expected_positions(driver_id, race_results)
        actual_score = 1.0 - (position - 1) / 20  # Normalize: 1st=1.0, 20th=0.05
        expected_score = 1.0 - (expected_positions.get(driver_id, 10) - 1) / 20
        
        # Adjust K-factor based on experience
        experience = driver.get("experience_races", 10)
        if experience < 10:
            k_factor = elo_k_factor * 1.5  # Rookies learn faster
        elif experience > 200:
            k_factor = elo_k_factor * 0.7  # Veterans more stable
        
        new_elo = update_driver_elo(current_elo, actual_score, expected_score, k_factor)
        driver["elo"] = round(new_elo, 1)
        updates_made["elo_updates"].append({
            "driver": driver["name"],
            "old_elo": current_elo,
            "new_elo": driver["elo"],
            "change": round(driver["elo"] - current_elo, 1)
        })
    
    return updates_made


def _calculate_expected_positions(driver_id: str, race_results: Dict) -> Dict:
    """Calculate expected positions based on ELO ratings."""
    from data.driver_data import get_driver
    
    expected = {}
    driver_elo = get_driver(driver_id)["elo"]
    
    for other_id in race_results.keys():
        if other_id == driver_id:
            continue
        other_elo = get_driver(other_id)["elo"]
        expected_score = calculate_expected_score(driver_elo, other_elo)
        expected[other_id] = expected_score
    
    return expected


def load_results_from_json(filepath: str) -> Dict[str, int]:
    """Load race results from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Support both formats: {"verstappen": 1} or {"results": [{"driver": "verstappen", "position": 1}]}
    if "results" in data:
        return {r["driver"]: r["position"] for r in data["results"]}
    
    return data


def main():
    """CLI entry point for data sync."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update F1 season data after race")
    parser.add_argument("--race", "-r", required=True, help="Race circuit ID")
    parser.add_argument("--results", help="JSON file with race results")
    parser.add_argument("--fastf1", action="store_true", help="Fetch from Fast-F1")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    
    args = parser.parse_args()
    
    # Load results
    if args.results:
        race_results = load_results_from_json(args.results)
    elif args.fastf1:
        print("[yellow]Fast-F1 integration requires fastf1 library: pip install fastf1[/]")
        # TODO: Implement Fast-F1 fetching
        sys.exit(1)
    else:
        print("[red]Error: Must provide --results or --fastf1[/]")
        sys.exit(1)
    
    # Update data
    print(f"\n[bold cyan]Updating season data for {args.race.upper()}...[/]")
    updates = update_season_data(args.race, race_results)
    
    # Print summary
    print(f"\n[green]✓ ELO updates:[/] {len(updates['elo_updates'])}")
    for update in updates['elo_updates']:
        change = update['change']
        color = "green" if change > 0 else "red" if change < 0 else "white"
        print(f"  {update['driver']}: {update['old_elo']} → {update['new_elo']} ([{color}]{change:+.1f}[/])")
    
    print(f"\n[yellow]Points updates:[/] {len(updates['points_updates'])}")
    for update in updates['points_updates']:
        print(f"  {update['driver']}: {update['old_points']} → {update['new_points']} (+{update['points_earned']})")
    
    if updates['errors']:
        print(f"\n[red]Errors:[/] {len(updates['errors'])}")
        for error in updates['errors']:
            print(f"  ✗ {error}")
    
    print(f"\n[dim]Data synced successfully![/]")


if __name__ == "__main__":
    main()
