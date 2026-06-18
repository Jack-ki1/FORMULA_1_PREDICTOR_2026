"""
Probability Calibration Utility.

Uses Platt scaling to calibrate raw prediction probabilities against historical outcomes.
Improves probability accuracy by learning systematic biases in the model.

Usage:
    python scripts/calibrate_probabilities.py --season 2025

This script:
1. Loads evaluated predictions from database
2. Fits Platt scaling parameters (A, B) for each outcome type
3. Reports calibration quality metrics
4. Saves calibrated parameters for use in future predictions
"""

import sys
import os
import json
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_evaluated_predictions(season: int = 2026) -> List[Dict]:
    """Load all evaluated predictions from database."""
    from database.models import SessionLocal, Prediction, create_database
    from sqlalchemy.exc import OperationalError
    
    # Ensure database tables exist
    try:
        create_database()
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
    
    db = SessionLocal()
    try:
        predictions = db.query(Prediction).filter(
            Prediction.brier_score.isnot(None),
            Prediction.actual_position.isnot(None)
        ).all()
        
        return [
            {
                "driver_id": p.driver_id,
                "win_probability": p.win_probability,
                "top3_probability": p.top3_probability,
                "top10_probability": p.top10_probability,
                "dnf_probability": p.dnf_probability,
                "actual_position": p.actual_position,
            }
            for p in predictions
        ]
    except OperationalError as e:
        if "no such table" in str(e):
            print("\n❌ Database not initialized!")
            print("\nTo initialize the database:")
            print("  py main.py migrate-db")
            print("\nThen store some predictions:")
            print("  py main.py predict --race canada --store")
            print("\nAfter a race completes, evaluate it:")
            print("  py main.py evaluate-race --race canada --results results.json")
            print("\nThen run calibration again.")
            return []
        else:
            raise
    finally:
        db.close()


def fit_calibration_params(predictions: List[Dict], outcome_type: str = "top3") -> Tuple[float, float]:
    """
    Fit Platt scaling parameters for specified outcome type.
    
    Args:
        predictions: List of prediction dictionaries with actual outcomes
        outcome_type: One of "win", "top3", "top10", "dnf"
    
    Returns:
        Tuple of (A, B) Platt scaling parameters
    """
    from engine.calibration import platt_scale
    
    # Extract raw probabilities and binary outcomes
    raw_probs = []
    outcomes = []
    
    for pred in predictions:
        actual_pos = pred["actual_position"]
        
        if outcome_type == "win":
            raw_probs.append(pred["win_probability"])
            outcomes.append(1.0 if actual_pos == 1 else 0.0)
        elif outcome_type == "top3":
            raw_probs.append(pred["top3_probability"])
            outcomes.append(1.0 if actual_pos <= 3 else 0.0)
        elif outcome_type == "top10":
            raw_probs.append(pred["top10_probability"])
            outcomes.append(1.0 if actual_pos <= 10 else 0.0)
        elif outcome_type == "dnf":
            raw_probs.append(pred["dnf_probability"])
            outcomes.append(1.0 if actual_pos > 20 else 0.0)
        else:
            raise ValueError(f"Unknown outcome type: {outcome_type}")
    
    if not raw_probs:
        return 1.0, 0.0  # Default no-calibration
    
    # Fit Platt scaling
    A, B = platt_scale(raw_probs, outcomes)
    
    return A, B


def evaluate_calibration(predictions: List[Dict], A: float, B: float, 
                        outcome_type: str = "top3") -> Dict:
    """
    Evaluate calibration quality using Brier score before and after calibration.
    
    Returns:
        Dictionary with calibration metrics
    """
    from engine.calibration import brier_score
    import math
    
    raw_probs = []
    outcomes = []
    calibrated_probs = []
    
    for pred in predictions:
        actual_pos = pred["actual_position"]
        
        if outcome_type == "top3":
            raw_prob = pred["top3_probability"]
            outcome = 1.0 if actual_pos <= 3 else 0.0
        else:
            continue
        
        # Apply Platt scaling
        eps = 1e-9
        raw_prob_clamped = max(eps, min(1 - eps, raw_prob))
        log_odds = math.log(raw_prob_clamped / (1 - raw_prob_clamped))
        calibrated_prob = 1.0 / (1.0 + math.exp(-(A * log_odds + B)))
        calibrated_prob = max(eps, min(1 - eps, calibrated_prob))
        
        raw_probs.append(raw_prob)
        calibrated_probs.append(calibrated_prob)
        outcomes.append(int(outcome))
    
    # Handle empty data
    if not raw_probs:
        print(f"  [WARN] No data available for {outcome_type.upper()} calibration")
        return {
            "outcome_type": outcome_type,
            "n_samples": 0,
            "brier_before_calibration": 0.0,
            "brier_after_calibration": 0.0,
            "improvement_pct": 0.0,
            "platt_A": A,
            "platt_B": B,
        }
    
    # Calculate Brier scores
    brier_before = brier_score(raw_probs, outcomes)
    brier_after = brier_score(calibrated_probs, outcomes)
    
    improvement = ((brier_before - brier_after) / brier_before * 100) if brier_before > 0 else 0
    
    return {
        "outcome_type": outcome_type,
        "n_samples": len(raw_probs),
        "brier_before_calibration": round(brier_before, 4),
        "brier_after_calibration": round(brier_after, 4),
        "improvement_pct": round(improvement, 2),
        "platt_A": round(A, 4),
        "platt_B": round(B, 4),
    }


def run_calibration(season: int = 2026):
    """Run full calibration analysis."""
    print("="*70)
    print("PROBABILITY CALIBRATION ANALYSIS")
    print("="*70)
    
    # Load data
    print("\nLoading evaluated predictions...")
    predictions = load_evaluated_predictions(season)
    
    if not predictions:
        print("\n[ERROR] No evaluated predictions found!")
        print("\nTo enable calibration:")
        print("  1. Store predictions: py main.py predict --race <circuit> --store")
        print("  2. After race, evaluate: py main.py evaluate-race --race <circuit> --results results.json")
        print("  3. Run calibration again")
        return
    
    print(f"Loaded {len(predictions)} evaluated predictions")
    
    # Fit calibration for each outcome type
    print("\nFitting Platt scaling parameters...")
    print("-"*70)
    
    calibration_results = {}
    
    for outcome_type in ["win", "top3", "top10", "dnf"]:
        print(f"\nCalibrating {outcome_type.upper()} probabilities...")
        
        # Fit parameters
        A, B = fit_calibration_params(predictions, outcome_type)
        
        # Evaluate
        metrics = evaluate_calibration(predictions, A, B, outcome_type)
        calibration_results[outcome_type] = metrics
        
        if metrics["n_samples"] == 0:
            print(f"  [SKIP] No data available for {outcome_type.upper()}")
            continue
        
        print(f"  Samples: {metrics['n_samples']}")
        print(f"  Platt A: {metrics['platt_A']:.4f}, B: {metrics['platt_B']:.4f}")
        print(f"  Brier Before: {metrics['brier_before_calibration']:.4f}")
        print(f"  Brier After:  {metrics['brier_after_calibration']:.4f}")
        print(f"  Improvement:  {metrics['improvement_pct']:.1f}%")
    
    # Summary
    print("\n" + "="*70)
    print("CALIBRATION SUMMARY")
    print("="*70)
    
    # Filter out skipped outcome types (n_samples == 0)
    valid_results = {k: v for k, v in calibration_results.items() if v["n_samples"] > 0}
    
    if not valid_results:
        print("\n[ERROR] No outcome types have sufficient data for calibration!")
        print("  Need at least some evaluated predictions with actual results.")
        return
    
    avg_improvement = sum(m["improvement_pct"] for m in valid_results.values()) / len(valid_results)
    
    print(f"\nAverage Calibration Improvement: {avg_improvement:.1f}%")
    print(f"Outcome types calibrated: {len(valid_results)}/4")
    
    if avg_improvement > 5:
        print("[PASS] Calibration provides significant improvement")
        print("  -> Consider integrating Platt scaling into prediction pipeline")
    elif avg_improvement > 0:
        print("[WARN] Calibration provides minor improvement")
        print("  -> May not be worth added complexity")
    else:
        print("[INFO] Calibration shows no improvement")
        print("  -> Model is already well-calibrated or needs more data")
    
    # Save calibration parameters
    output_file = f"calibration_params_{season}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "season": season,
            "n_predictions": len(predictions),
            "parameters": {
                k: {"A": v["platt_A"], "B": v["platt_B"]}
                for k, v in calibration_results.items()
            },
            "metrics": calibration_results,
        }, f, indent=2)
    
    print(f"\n[SUCCESS] Calibration parameters saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calibrate F1 prediction probabilities")
    parser.add_argument("--season", "-s", type=int, default=2026, help="Season to calibrate (default: 2026)")
    
    args = parser.parse_args()
    
    run_calibration(season=args.season)
