#!/usr/bin/env python
"""
Data Quality Report Script.

Generates a report on the quality of driver and circuit data,
including validation checks for missing fields, out-of-range values,
and probability fields outside [0,1].
"""

import sys
import os
from typing import List, Dict, Tuple
import logging

# Add project root to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.driver_data import DRIVERS, validate_driver_data_integrity
from data.circuit_data import CIRCUITS, validate_circuit_data_integrity
from config.settings import logger


def run_data_quality_report() -> Tuple[List[str], List[str]]:
    """
    Run data quality checks and return lists of issues and successes.
    """
    issues = []
    successes = []
    
    logger.info("Starting data quality report...")
    
    # Driver data checks
    logger.info("Checking driver data...")

    # Check for missing fields
    for driver_id, driver in DRIVERS.items():
        # Driver entries are dicts (see data/driver_data.py)
        name = driver.get("name")
        team = driver.get("team")
        nationality = driver.get("nationality")

        if not name:
            issues.append(f"Driver {driver_id}: Missing name")
        if not team:
            issues.append(f"Driver {driver_id}: Missing team")
        if not nationality:
            issues.append(f"Driver {driver_id}: Missing nationality")

        elo = driver.get("elo")
        if elo is None or not (1000 <= elo <= 2500):
            issues.append(f"Driver {driver_id}: ELO out of range: {elo}")

        # Check skill values
        wet_skill = driver.get("wet_skill")
        brakezone_skill = driver.get("brakezone_skill")
        tire_management = driver.get("tire_management")

        if wet_skill is None or not (0 <= wet_skill <= 10):
            issues.append(f"Driver {driver_id}: Wet skill out of range: {wet_skill}")
        if brakezone_skill is None or not (0 <= brakezone_skill <= 10):
            issues.append(f"Driver {driver_id}: Brake zone skill out of range: {brakezone_skill}")
        if tire_management is None or not (0 <= tire_management <= 10):
            issues.append(f"Driver {driver_id}: Tire management out of range: {tire_management}")

        # Check probability fields
        dnf_rate_career = driver.get("dnf_rate_career")
        dnf_rate_recent = driver.get("dnf_rate_recent")

        if dnf_rate_career is None or not (0 <= dnf_rate_career <= 1):
            issues.append(f"Driver {driver_id}: Career DNF rate out of [0,1]: {dnf_rate_career}")
        if dnf_rate_recent is None or not (0 <= dnf_rate_recent <= 1):
            issues.append(f"Driver {driver_id}: Recent DNF rate out of [0,1]: {dnf_rate_recent}")

    successes.append(f"Checked {len(DRIVERS)} drivers")

    
    # Circuit data checks
    logger.info("Checking circuit data...")
    
    for circuit_id, circuit in CIRCUITS.items():
        # Check required fields
        if not circuit.name:
            issues.append(f"Circuit {circuit_id}: Missing name")
        if not circuit.country:
            issues.append(f"Circuit {circuit_id}: Missing country")
        
        # Check probability fields
        if not (0 <= circuit.safety_car_probability <= 1):
            issues.append(f"Circuit {circuit_id}: Safety car probability out of [0,1]: {circuit.safety_car_probability}")
        if not (0 <= circuit.rain_probability_typical <= 1):
            issues.append(f"Circuit {circuit_id}: Rain probability out of [0,1]: {circuit.rain_probability_typical}")
        if not (0 <= circuit.wall_crash_probability_per_lap <= 1):
            issues.append(f"Circuit {circuit_id}: Wall crash probability out of [0,1]: {circuit.wall_crash_probability_per_lap}")
        
        # Check difficulty ranges
        if not (1 <= circuit.overtaking_difficulty <= 10):
            issues.append(f"Circuit {circuit_id}: Overtaking difficulty out of [1,10]: {circuit.overtaking_difficulty}")
        if not (0 <= circuit.power_unit_demand <= 10):
            issues.append(f"Circuit {circuit_id}: Power unit demand out of [0,10]: {circuit.power_unit_demand}")
        if not (0 <= circuit.brake_demand <= 10):
            issues.append(f"Circuit {circuit_id}: Brake demand out of [0,10]: {circuit.brake_demand}")
        if not (0 <= circuit.tire_deg_rate <= 10):
            issues.append(f"Circuit {circuit_id}: Tire degradation rate out of [0,10]: {circuit.tire_deg_rate}")
        if not (0 <= circuit.active_aero_demand <= 10):
            issues.append(f"Circuit {circuit_id}: Active aero demand out of [0,10]: {circuit.active_aero_demand}")
    
    successes.append(f"Checked {len(CIRCUITS)} circuits")
    
    # Run built-in validation functions
    try:
        validate_circuit_data_integrity()
        successes.append("Circuit data integrity check passed")
    except Exception as e:
        issues.append(f"Circuit data integrity check failed: {str(e)}")
    
    logger.info("Data quality report complete.")
    
    return issues, successes


def main():
    """Main function to run the data quality report."""
    print("Running Data Quality Report...\n")
    
    issues, successes = run_data_quality_report()
    
    print("SUCCESS CHECKS:")
    for success in successes:
        print(f"  ✓ {success}")
    
    print("\nISSUES FOUND:")
    if not issues:
        print("  No issues found!")
    else:
        for issue in issues:
            print(f"  ✗ {issue}")
    
    print(f"\nSummary: {len(successes)} checks passed, {len(issues)} issues found")
    
    if issues:
        print("\nRecommended actions:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")


if __name__ == "__main__":
    main()