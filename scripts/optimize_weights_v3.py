"""
Weight Optimization using Optuna — v3.0.

Uses Bayesian optimization to find optimal FEATURE_WEIGHTS that minimize
Brier score across historical race predictions.

Usage:
    python scripts/optimize_weights_v3.py --trials 100 --output weights_optimized.json

This script:
1. Loads historical race results (2024-2025 seasons)
2. For each trial, proposes new feature weights via Optuna
3. Runs predictions on all historical races with those weights
4. Calculates Brier score against actual results
5. Returns weights that minimize prediction error
"""

# FIX: Set UTF-8 encoding for Windows console compatibility
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import os
import json
import logging
import argparse
from typing import Dict, List, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def calculate_brier_score(predicted_probs: List[float], actual_outcomes: List[int]) -> float:
    """Calculate mean Brier score for probability predictions."""
    if not predicted_probs:
        return 1.0  # Worst case
    
    n = len(predicted_probs)
    brier = sum((p - o) ** 2 for p, o in zip(predicted_probs, actual_outcomes)) / n
    return brier


def objective(trial, historical_races: List[Dict]) -> float:
    """
    Objective function for Optuna optimization.
    
    Proposes new feature weights and evaluates them against historical data.
    Returns mean Brier score (lower is better).
    """
    from config.settings import FEATURE_WEIGHTS
    
    # Suggest new weights for each feature
    weight_keys = list(FEATURE_WEIGHTS.keys())
    suggested_weights = {}
    
    for key in weight_keys:
        suggested_weights[key] = trial.suggest_float(key, 0.0, 2.0)
    
    # Normalize weights to sum to 1.0
    total = sum(suggested_weights.values())
    normalized_weights = {k: v / total for k, v in suggested_weights.items()}
    
    # Temporarily apply these weights
    original_weights = FEATURE_WEIGHTS.copy()
    FEATURE_WEIGHTS.update(normalized_weights)
    
    try:
        from engine.predictor import predict, PredictionRequest
        
        total_brier = 0.0
        num_evaluations = 0
        
        # Evaluate on each historical race
        for race in historical_races:
            if not race.get("results"):
                continue
            
            circuit_id = race["circuit"]
            actual_results = race["results"]
            
            try:
                # Run prediction with current weights
                prediction = predict(PredictionRequest(
                    circuit_id=circuit_id,
                    n_simulations=5000,  # Use fewer sims for speed during optimization
                    seed=42,
                ))
                
                # Calculate Brier score for this race
                for driver_result in actual_results[:10]:  # Top 10 finishers
                    driver_id = driver_result["driver"]
                    actual_position = driver_result["position"]
                    
                    # Find predicted probabilities for this driver
                    driver_pred = next(
                        (p for p in prediction["predictions"] if p["driver_id"] == driver_id),
                        None
                    )
                    
                    if driver_pred:
                        # Binary outcome: did they finish in top 3?
                        actual_top3 = 1 if actual_position <= 3 else 0
                        predicted_top3_prob = driver_pred.get("top3_pct", 0) / 100.0
                        
                        total_brier += (predicted_top3_prob - actual_top3) ** 2
                        num_evaluations += 1
            
            except Exception as e:
                # Skip races that fail to predict
                logger.warning(f"Prediction failed for {circuit_id}: {e}")
                continue
        
        avg_brier = total_brier / max(num_evaluations, 1)
        
    finally:
        # Restore original weights
        FEATURE_WEIGHTS.update(original_weights)
    
    return avg_brier


def run_weight_optimization(n_trials: int = 100, save_path: str = "weights_optimized.json") -> Dict:
    """
    Run Optuna optimization to find best feature weights.
    
    Args:
        n_trials: Number of optimization trials
        save_path: Path to save optimized weights
    
    Returns:
        Dictionary with optimized weights and performance metrics
    """
    try:
        import optuna
    except ImportError:
        print("Error: optuna not installed. Run: pip install optuna")
        sys.exit(1)
    
    # Load historical data
    print("Loading historical race data...")
    try:
        from data.season_2026 import SEASON_RESULTS_2026
        historical_races = SEASON_RESULTS_2026
        print(f"Loaded {len(historical_races)} historical races")
    except Exception as e:
        print(f"Warning: Could not load historical data: {e}")
        print("Using synthetic data for demonstration...")
        historical_races = []
    
    if not historical_races:
        print("\nNo historical data available for optimization.")
        print("To enable real optimization:")
        print("  1. Add completed race results to data/season_2026.py")
        print("  2. Or fetch live data via Jolpica API")
        print("\nReturning default weights...")
        from config.settings import FEATURE_WEIGHTS
        return {"weights": FEATURE_WEIGHTS, "brier_score": None, "note": "No historical data"}
    
    # Create Optuna study
    print(f"\nStarting optimization with {n_trials} trials...")
    study = optuna.create_study(
        direction='minimize',
        study_name='f1_feature_weights',
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # Run optimization
    study.optimize(
        lambda trial: objective(trial, historical_races),
        n_trials=n_trials,
        show_progress_bar=True
    )
    
    # Extract best weights
    best_params = study.best_params
    
    # Normalize best weights
    total = sum(best_params.values())
    optimized_weights = {k: round(v / total, 4) for k, v in best_params.items()}
    
    # Print results
    print("\n" + "="*70)
    print("OPTIMIZATION RESULTS")
    print("="*70)
    print(f"Best Brier Score: {study.best_value:.4f}")
    print(f"Number of Trials: {n_trials}")
    print(f"\nOptimized Weights:")
    for key, weight in sorted(optimized_weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key:30s}: {weight:.4f}")
    
    # Save to file
    result = {
        "weights": optimized_weights,
        "brier_score": round(study.best_value, 4),
        "n_trials": n_trials,
        "n_races_evaluated": len([r for r in historical_races if r.get("results")]),
    }
    
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[PASS] Optimized weights saved to: {save_path}")
    print("="*70)
    
    return result


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Optimize F1 prediction feature weights")
    parser.add_argument("--trials", "-t", type=int, default=100, help="Number of optimization trials")
    parser.add_argument("--output", "-o", default="weights_optimized.json", help="Output file path")
    
    args = parser.parse_args()
    
    result = run_weight_optimization(n_trials=args.trials, save_path=args.output)
    
    if result.get("brier_score") is None:
        print("\n[WARN] Optimization skipped due to missing historical data")
        sys.exit(0)
    else:
        print(f"\n[PASS] Optimization complete! Brier score: {result['brier_score']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
