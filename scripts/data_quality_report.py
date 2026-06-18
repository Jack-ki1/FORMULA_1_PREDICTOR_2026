"""Data quality and consistency checks for F1 Predictor."""

import sys
import os

# Add project root to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List

from config.settings import validate_settings
from data.circuit_data import CIRCUITS, get_all_circuits, get_circuit
from data.driver_data import get_all_drivers
from engine.feature_engineering import compute_all_drivers
from engine.predictor import PredictionRequest, predict


def _check_driver_ids(drivers: List[dict]) -> List[str]:
    ids = [driver.get("id") for driver in drivers]
    duplicates = {item for item in ids if ids.count(item) > 1}
    return sorted(duplicates)


def run_all_checks() -> None:
    print("Running F1 Predictor data quality checks...")
    errors = []
    warnings = []

    # Settings validation
    settings_report = validate_settings()
    if not settings_report["valid"]:
        errors.extend(settings_report["errors"])

    # Driver data validation
    drivers = get_all_drivers()
    if not drivers:
        errors.append("No drivers found in data.driver_data")
    else:
        duplicate_ids = _check_driver_ids(drivers)
        if duplicate_ids:
            errors.append(f"Duplicate driver IDs found: {duplicate_ids}")
        for driver in drivers:
            if not driver.get("id") or not driver.get("name"):
                errors.append(f"Driver entry missing required fields: {driver}")

    # Circuit data validation
    circuits = get_all_circuits()
    if not circuits:
        errors.append("No circuits found in data.circuit_data")
    else:
        for circuit in circuits:
            try:
                get_circuit(circuit["id"])
            except Exception as exc:
                errors.append(f"Circuit lookup failed for {circuit['id']}: {exc}")

    # Feature engine sanity check (warning only - may need FastF1 setup)
    try:
        comp = compute_all_drivers("canada", rain_probability=0.15)
        if not comp:
            warnings.append("Feature engine returned no driver scores for canada")
    except Exception as exc:
        warnings.append(f"Feature engine test skipped: {exc}")

    # Prediction engine smoke test (warning only - may need FastF1 setup)
    try:
        sample = predict(PredictionRequest(circuit_id="canada", rain_probability=0.15, n_simulations=250, seed=42))
        if "predictions" not in sample or not sample["predictions"]:
            warnings.append("Prediction engine returned no predictions for canada")
    except Exception as exc:
        warnings.append(f"Prediction engine test skipped: {exc}")

    print("\nData quality summary")
    print("--------------------")
    if errors:
        print(f"Errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("No errors found.")

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        raise SystemExit(1)
    print("\nAll checks passed successfully.")


def run_quality_check() -> dict:
    """
    Run quality checks and return results as a dictionary.
    
    Returns:
        Dictionary with 'errors', 'warnings', and 'passed' status
    """
    from io import StringIO
    
    # Capture output instead of printing
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    errors = []
    warnings = []
    passed = True
    
    try:
        # Settings validation
        settings_report = validate_settings()
        if not settings_report["valid"]:
            errors.extend(settings_report["errors"])
            passed = False

        # Driver data validation
        drivers = get_all_drivers()
        if not drivers:
            errors.append("No drivers found in data.driver_data")
            passed = False
        else:
            duplicate_ids = _check_driver_ids(drivers)
            if duplicate_ids:
                errors.append(f"Duplicate driver IDs found: {duplicate_ids}")
                passed = False
            for driver in drivers:
                if not driver.get("id") or not driver.get("name"):
                    errors.append(f"Driver entry missing required fields: {driver}")
                    passed = False

        # Circuit data validation
        circuits = get_all_circuits()
        if not circuits:
            errors.append("No circuits found in data.circuit_data")
            passed = False
        else:
            for circuit in circuits:
                try:
                    get_circuit(circuit["id"])
                except Exception as exc:
                    errors.append(f"Circuit lookup failed for {circuit['id']}: {exc}")
                    passed = False

        # Feature engine sanity check
        try:
            comp = compute_all_drivers("canada", rain_probability=0.15)
            if not comp:
                errors.append("Feature engine returned no driver scores for canada")
                passed = False
        except Exception as exc:
            errors.append(f"Feature engine failed: {exc}")
            passed = False

        # Prediction engine smoke test
        try:
            sample = predict(PredictionRequest(circuit_id="canada", rain_probability=0.15, n_simulations=250, seed=42))
            if "predictions" not in sample or not sample["predictions"]:
                errors.append("Prediction engine returned no predictions for canada")
                passed = False
        except Exception as exc:
            errors.append(f"Prediction engine smoke test failed: {exc}")
            passed = False
            
    except Exception as e:
        errors.append(f"Quality check failed: {str(e)}")
        passed = False
    finally:
        sys.stdout = old_stdout
    
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }