#!/usr/bin/env python
"""
Backtesting script for the 2025 F1 season.

This script runs predictions for past races and compares them to actual results
to evaluate model performance.
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from engine.predictor import predict, PredictionRequest
from config.settings import REPORT_CONFIG


def run_backtest(smoke_mode: bool = False, output_dir: str = None) -> Dict:
    """
    Run backtesting for the 2025 season.
    
    Args:
        smoke_mode: If True, run only a couple races quickly
        output_dir: Output directory for results
    
    Returns:
        Dictionary containing aggregated metrics
    """
    # Define races to backtest (simplified example)
    races_to_test = [
        {"circuit_id": "australia", "actual_results": [1, 2, 3, 4, 5]},  # Placeholder results
        {"circuit_id": "china", "actual_results": [2, 1, 4, 3, 6]},
        {"circuit_id": "bahrain", "actual_results": [1, 3, 2, 5, 4]},
        # Add more races as needed
    ]
    
    if smoke_mode:
        # Only run first two races in smoke mode
        races_to_test = races_to_test[:2]
        print("SMOKE MODE: Running only a subset of races for quick testing")
    
    per_race_metrics = []
    total_predictions = 0
    correct_predictions = 0
    
    print(f"Starting backtest for {len(races_to_test)} races...")
    
    for i, race in enumerate(races_to_test):
        print(f"Processing race {i+1}/{len(races_to_test)}: {race['circuit_id']}")
        
        # Create prediction request
        request = PredictionRequest(
            circuit_id=race["circuit_id"],
            n_simulations=2000,  # Lower for backtesting speed
            output_format="full"
        )
        
        # Run prediction
        result = predict(request)
        
        # Compare to actual results (this is a simplified comparison)
        # In a real implementation, you'd have more sophisticated evaluation metrics
        race_correct = 0
        for j, pred_driver in enumerate(result["predictions"][:len(race["actual_results"])]):
            actual_pos = race["actual_results"][j]
            if pred_driver["predicted_position"] == actual_pos:
                race_correct += 1
        
        total_predictions += len(race["actual_results"])
        correct_predictions += race_correct
        
        race_metric = {
            "circuit_id": race["circuit_id"],
            "correct_predictions": race_correct,
            "total_predictions": len(race["actual_results"]),
            "accuracy": race_correct / len(race["actual_results"]) if len(race["actual_results"]) > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        per_race_metrics.append(race_metric)
        print(f"  Accuracy: {race_correct}/{len(race['actual_results'])} ({race_metric['accuracy']:.2%})")
    
    # Calculate overall metrics
    overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    aggregate_metrics = {
        "smoke_mode": smoke_mode,
        "total_races": len(races_to_test),
        "total_predictions": total_predictions,
        "correct_predictions": correct_predictions,
        "overall_accuracy": overall_accuracy,
        "per_race_metrics": per_race_metrics,
        "timestamp": datetime.now().isoformat(),
        "model_version": "2026_prediction_engine_v1"  # Placeholder for model version tracking
    }
    
    # Save metrics to disk
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save per-race metrics
        race_metrics_file = os.path.join(
            output_dir, 
            f"backtest_2025_per_race_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(race_metrics_file, 'w') as f:
            json.dump(per_race_metrics, f, indent=2)
        
        # Save aggregate metrics
        agg_metrics_file = os.path.join(
            output_dir, 
            f"backtest_2025_aggregate_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(agg_metrics_file, 'w') as f:
            json.dump(aggregate_metrics, f, indent=2)
        
        print(f"Metrics saved to {output_dir}/")
        print(f"  - Per-race metrics: {os.path.basename(race_metrics_file)}")
        print(f"  - Aggregate metrics: {os.path.basename(agg_metrics_file)}")
    
    return aggregate_metrics


def main():
    parser = argparse.ArgumentParser(description="Backtest the 2025 F1 season predictions")
    parser.add_argument("--smoke", action="store_true", 
                       help="Run only a couple races quickly for testing")
    parser.add_argument("--output-dir", default=None, 
                       help="Output directory for metrics (defaults to config setting)")
    
    args = parser.parse_args()
    
    # Use provided output directory or fall back to config
    output_dir = args.output_dir or REPORT_CONFIG.output_dir
    
    print("Starting backtesting for 2025 F1 season...")
    if args.smoke:
        print("SMOKE MODE ENABLED: Will run only a subset of races")
    
    metrics = run_backtest(smoke_mode=args.smoke, output_dir=output_dir)
    
    print("\nBacktesting completed!")
    print(f"Overall accuracy: {metrics['overall_accuracy']:.2%}")
    print(f"Total races tested: {metrics['total_races']}")
    print(f"Total predictions: {metrics['total_predictions']}")
    print(f"Correct predictions: {metrics['correct_predictions']}")


if __name__ == "__main__":
    main()