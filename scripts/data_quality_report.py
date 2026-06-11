"""Data quality and consistency checks for F1 Predictor."""

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

    # Feature engine sanity check with a light sample prediction
    try:
        comp = compute_all_drivers("canada", rain_probability=0.15)
        if not comp:
            errors.append("Feature engine returned no driver scores for canada")
    except Exception as exc:
        errors.append(f"Feature engine failed: {exc}")

    # Prediction engine smoke test
    try:
        sample = predict(PredictionRequest(circuit_id="canada", rain_probability=0.15, n_simulations=250, seed=42))
        if "predictions" not in sample or not sample["predictions"]:
            errors.append("Prediction engine returned no predictions for canada")
    except Exception as exc:
        errors.append(f"Prediction engine smoke test failed: {exc}")

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
