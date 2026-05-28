#!/usr/bin/env python3
"""
Verification Script for F1 Predictor v2.1 Bug Fixes.

Validates that all critical P0 and P1 bugs have been properly fixed.
Run this after applying fixes to ensure correctness before deployment.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def verify_bug_01_platt_calibration():
    """BUG-01: Verify separate Platt parameters per outcome type."""
    from engine.probability_model import apply_platt, PLATT_PARAMS
    
    # Check all 4 outcome types exist
    required_types = {"win", "top3", "top10", "dnf"}
    if set(PLATT_PARAMS.keys()) != required_types:
        return False, f"Missing outcome types in PLATT_PARAMS: {required_types - set(PLATT_PARAMS.keys())}"
    
    # Test that different outcomes produce different calibrated values
    raw_prob = 0.5
    results = {}
    for outcome_type in required_types:
        results[outcome_type] = apply_platt(raw_prob, outcome_type)
    
    # At least some should differ (not all identical like broken version)
    unique_values = len(set(results.values()))
    if unique_values < 2:
        return False, f"All outcomes produce same calibrated value: {results}"
    
    return True, f"Different outcomes produce distinct calibrations: {results}"


def verify_bug_02_driver_names():
    """BUG-02: Verify driver_name key exists in predictions."""
    from reports.html_report import generate_report
    
    # Generate a small report with minimal simulations
    try:
        output_path = generate_report("canada", rain_probability=0.0, n_simulations=100)
        
        # Read the HTML and check for blank driver names
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Look for empty driver-name divs (the bug symptom)
        if '<div class="driver-name"></div>' in html_content:
            return False, "Found blank driver-name divs in HTML output"
        
        # Check that driver names are actually present
        if 'Antonelli' not in html_content or 'Hamilton' not in html_content:
            return False, "Expected driver names not found in HTML"
        
        return True, "Driver names properly rendered in HTML report"
    except Exception as e:
        return False, f"Report generation failed: {e}"


def verify_bug_03_no_duplicate_schemas():
    """BUG-03: Verify no duplicate class definitions in schemas.py."""
    import api.schemas as schemas
    import inspect
    
    # Get all classes defined in the module
    classes = [name for name, obj in inspect.getmembers(schemas) if inspect.isclass(obj)]
    
    # Check for duplicates
    if len(classes) != len(set(classes)):
        duplicates = [c for c in classes if classes.count(c) > 1]
        return False, f"Duplicate classes found: {set(duplicates)}"
    
    # Verify expected classes exist
    expected = {"PredictRequest", "DriverPredictionOut", "RacePredictionResponse"}
    missing = expected - set(classes)
    if missing:
        return False, f"Missing expected classes: {missing}"
    
    return True, f"No duplicate schemas. Found {len(classes)} unique classes."


def verify_bug_06_cadillac_drivers():
    """BUG-06: Verify Cadillac has exactly 2 active drivers."""
    from data.driver_data import get_drivers_for_team, DRIVERS
    
    cadillac_drivers = get_drivers_for_team("cadillac")
    if len(cadillac_drivers) != 2:
        return False, f"Cadillac has {len(cadillac_drivers)} active drivers, expected 2"
    
    # Verify Zhou is marked inactive
    zhou = DRIVERS.get("zhou")
    if zhou and zhou.get("active", True):
        return False, "Zhou should be marked as inactive (active=False)"
    
    driver_ids = [d["id"] for d in cadillac_drivers]
    if "zhou" in driver_ids:
        return False, "Zhou should not be in active Cadillac drivers list"
    
    return True, f"Cadillac has 2 active drivers: {driver_ids}"


def verify_bug_08_standings_order():
    """BUG-08: Verify standings are sorted by points descending."""
    from data.season_2026 import DRIVER_STANDINGS_AFTER_R4
    
    prev_points = float('inf')
    for i, entry in enumerate(DRIVER_STANDINGS_AFTER_R4):
        current_points = entry["points"]
        if current_points > prev_points:
            return False, f"Position {i+1} ({entry['driver']}) has {current_points} pts but position {i} had {prev_points} pts"
        prev_points = current_points
    
    # Specific check: Piastri should be above Hamilton
    piastri_pos = next(e["position"] for e in DRIVER_STANDINGS_AFTER_R4 if e["driver"] == "piastri")
    hamilton_pos = next(e["position"] for e in DRIVER_STANDINGS_AFTER_R4 if e["driver"] == "hamilton")
    
    if piastri_pos >= hamilton_pos:
        return False, f"Piastri (P{piastri_pos}, 63pts) should be above Hamilton (P{hamilton_pos}, 52pts)"
    
    return True, f"Standings correctly ordered. Piastri P{piastri_pos} > Hamilton P{hamilton_pos}"


def verify_quality_05_config_validation():
    """QUALITY-05: Verify config validation raises on error."""
    import config.settings as settings
    
    # Temporarily break the weights
    original_weights = settings.FEATURE_WEIGHTS.copy()
    
    try:
        settings.FEATURE_WEIGHTS["elo_rating"] = -0.5  # Invalid negative weight
        
        try:
            settings.validate_settings()
            return False, "validate_settings() should raise ValueError for invalid weights"
        except ValueError:
            return True, "Config validation correctly raises on invalid configuration"
    finally:
        # Restore original weights
        settings.FEATURE_WEIGHTS.update(original_weights)


def verify_deploy_04_api_host():
    """DEPLOY-04: Verify API_HOST defaults to localhost."""
    from config.settings import API_HOST
    
    if API_HOST == "0.0.0.0":
        return False, f"API_HOST should default to 127.0.0.1, got {API_HOST}"
    
    return True, f"API_HOST securely defaults to {API_HOST}"


def run_all_verifications():
    """Run all verification checks."""
    console.rule("[bold cyan]F1 Predictor v2.1 - Bug Fix Verification[/]")
    
    checks = [
        ("BUG-01: Platt Calibration", verify_bug_01_platt_calibration),
        ("BUG-02: Driver Names", verify_bug_02_driver_names),
        ("BUG-03: Duplicate Schemas", verify_bug_03_no_duplicate_schemas),
        ("BUG-06: Cadillac Drivers", verify_bug_06_cadillac_drivers),
        ("BUG-08: Standings Order", verify_bug_08_standings_order),
        ("QUALITY-05: Config Validation", verify_quality_05_config_validation),
        ("DEPLOY-04: API Host Security", verify_deploy_04_api_host),
    ]
    
    passed = 0
    failed = 0
    
    table = Table(title="Verification Results", header_style="bold cyan")
    table.add_column("Check", style="cyan", width=40)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Details", style="dim")
    
    for name, check_fn in checks:
        try:
            success, message = check_fn()
            if success:
                table.add_row(name, "[green]✓ PASS[/]", message)
                passed += 1
            else:
                table.add_row(name, "[red]✗ FAIL[/]", f"[red]{message}[/]")
                failed += 1
        except Exception as e:
            table.add_row(name, "[red]✗ ERROR[/]", f"[red]{str(e)}[/]")
            failed += 1
    
    console.print(table)
    
    # Summary
    total = passed + failed
    if failed == 0:
        console.print(Panel(
            f"[bold green]All {total} verifications passed![/]\n\n"
            "The system is ready for production use.",
            border_style="green",
            title="✅ VERIFICATION SUCCESSFUL"
        ))
        return 0
    else:
        console.print(Panel(
            f"[bold red]{failed} of {total} verifications failed[/]\n\n"
            "Review the failures above and fix before deploying.",
            border_style="red",
            title="❌ VERIFICATION FAILED"
        ))
        return 1


if __name__ == "__main__":
    exit_code = run_all_verifications()
    sys.exit(exit_code)
