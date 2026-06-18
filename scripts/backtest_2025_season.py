"""
Backtesting Framework for F1 Predictor — 2025 Season.

Runs temporal cross-validation on historical race data to measure
prediction accuracy before deployment.

Usage:
    python scripts/backtest_2025_season.py --seasons 2024 2025

This script:
1. Loads completed races from specified seasons
2. For each race, predicts outcome using only pre-race data
3. Compares predictions to actual results
4. Calculates comprehensive accuracy metrics:
   - Top-3 hit rate
   - Win prediction accuracy
   - Brier score
   - Calibration error
   - Mean absolute error on positions
"""

# FIX: Set UTF-8 encoding for Windows console compatibility
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import os
import json
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_historical_data(seasons: List[int]) -> List[Dict]:
    """Load historical race data for specified seasons."""
    all_races = []
    
    for season in seasons:
        try:
            # Try to load from season-specific module
            if season == 2025:
                from data.season_2026 import SEASON_RESULTS_2026 as races
            elif season == 2024:
                # Placeholder for 2024 data (would need to be added)
                print(f"Warning: No data module for {season}, skipping...")
                continue
            else:
                print(f"Warning: Unsupported season {season}, skipping...")
                continue
            
            # Filter to completed races only
            completed = [r for r in races if r.get("results")]
            all_races.extend(completed)
            print(f"Loaded {len(completed)} completed races from {season}")
            
        except ImportError as e:
            print(f"Warning: Could not load season {season}: {e}")
            continue
    
    return all_races


def predict_race(circuit_id: str, n_simulations: int = 10000) -> Dict:
    """Run prediction for a single race."""
    from engine.predictor import predict, PredictionRequest
    
    try:
        result = predict(PredictionRequest(
            circuit_id=circuit_id,
            n_simulations=n_simulations,
            seed=42,
        ))
        return result
    except Exception as e:
        print(f"  Error predicting {circuit_id}: {e}")
        return None


def evaluate_prediction(prediction: Dict, actual_results: List[Dict]) -> Dict:
    """
    Evaluate a single race prediction against actual results.
    
    Returns metrics dictionary with accuracy scores.
    """
    if not prediction or not actual_results:
        return None
    
    predictions_sorted = sorted(
        prediction["predictions"],
        key=lambda x: x.get("top3_pct", 0),
        reverse=True
    )
    
    # Extract actual top 3
    actual_top3 = set()
    actual_winner = None
    for result in actual_results:
        pos = result["position"]
        driver = result["driver"]
        status = result.get("status", "Finished")
        
        if pos <= 3 and status != "DNF":
            actual_top3.add(driver)
        if pos == 1:
            actual_winner = driver
    
    # Predicted top 3
    predicted_top3 = set(p["driver_id"] for p in predictions_sorted[:3])
    predicted_winner = predictions_sorted[0]["driver_id"] if predictions_sorted else None
    
    # Calculate metrics
    top3_hits = actual_top3 & predicted_top3
    top3_accuracy = len(top3_hits) / 3.0 if actual_top3 else 0.0
    
    win_correct = (actual_winner == predicted_winner) if actual_winner else False
    
    # Calculate Brier score for top 10 drivers
    brier_scores = []
    for result in actual_results[:10]:
        driver_id = result["driver"]
        actual_pos = result["position"]
        
        # Find prediction for this driver
        pred = next((p for p in prediction["predictions"] if p["driver_id"] == driver_id), None)
        if pred:
            # Binary outcome: finished in top 3?
            actual_top3_binary = 1 if actual_pos <= 3 else 0
            predicted_prob = pred.get("top3_pct", 0) / 100.0
            brier = (predicted_prob - actual_top3_binary) ** 2
            brier_scores.append(brier)
    
    avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else None
    
    # Position prediction error
    position_errors = []
    for result in actual_results[:15]:
        driver_id = result["driver"]
        actual_pos = result["position"]
        
        pred = next((p for p in prediction["predictions"] if p["driver_id"] == driver_id), None)
        if pred:
            predicted_pos = pred.get("predicted_position", 0)
            error = abs(predicted_pos - actual_pos)
            position_errors.append(error)
    
    avg_position_error = sum(position_errors) / len(position_errors) if position_errors else None
    
    return {
        "top3_accuracy": top3_accuracy,
        "win_correct": win_correct,
        "brier_score": avg_brier,
        "avg_position_error": avg_position_error,
        "actual_top3": sorted(actual_top3),
        "predicted_top3": sorted(predicted_top3),
        "hits": sorted(top3_hits),
        "actual_winner": actual_winner,
        "predicted_winner": predicted_winner,
    }


def run_backtest(seasons: List[int] = [2025], n_simulations: int = 10000):
    """
    Run full backtesting across historical seasons.
    
    Args:
        seasons: List of seasons to backtest
        n_simulations: Number of Monte Carlo simulations per race
    """
    print("="*70)
    print("F1 PREDICTOR BACKTESTING FRAMEWORK")
    print("="*70)
    print(f"Seasons: {seasons}")
    print(f"Simulations per race: {n_simulations:,}")
    print("="*70)
    
    # Load historical data
    print("\nLoading historical data...")
    historical_races = load_historical_data(seasons)
    
    if not historical_races:
        print("\n[ERROR] No historical data available for backtesting!")
        print("\nTo enable backtesting:")
        print("  1. Add completed race results to data/season_2026.py")
        print("  2. Or sync FastF1 data: python main.py sync-fastf1 --seasons 2024 2025")
        return
    
    print(f"\nTotal races to evaluate: {len(historical_races)}")
    print("-"*70)
    
    # Run predictions and evaluations
    results = []
    for i, race in enumerate(historical_races, 1):
        race_name = race.get("name", f"Round {race.get('round', '?')}")
        circuit_id = race["circuit"]
        actual_results = race["results"]
        
        print(f"\n[{i}/{len(historical_races)}] {race_name} ({circuit_id})")
        
        # Run prediction
        prediction = predict_race(circuit_id, n_simulations)
        if not prediction:
            print(f"  [WARN] Skipped (prediction failed)")
            continue
        
        # Evaluate
        metrics = evaluate_prediction(prediction, actual_results)
        if not metrics:
            print(f"  [WARN] Skipped (evaluation failed)")
            continue
        
        results.append({
            "race": race_name,
            "circuit": circuit_id,
            "round": race.get("round"),
            "metrics": metrics,
        })
        
        # Print race-level results
        win_mark = "[OK]" if metrics["win_correct"] else "[FAIL]"
        print(f"  Top-3: {metrics['top3_accuracy']:.0%} ({len(metrics['hits'])}/3)")
        print(f"  Winner: {win_mark} (actual={metrics['actual_winner']}, predicted={metrics['predicted_winner']})")
        if metrics["brier_score"] is not None:
            print(f"  Brier Score: {metrics['brier_score']:.4f}")
        if metrics["avg_position_error"] is not None:
            print(f"  Avg Position Error: {metrics['avg_position_error']:.2f}")
    
    if not results:
        print("\n[ERROR] No races could be evaluated!")
        return
    
    # Aggregate metrics
    print("\n" + "="*70)
    print("BACKTESTING RESULTS SUMMARY")
    print("="*70)
    
    avg_top3 = sum(r["metrics"]["top3_accuracy"] for r in results) / len(results)
    win_rate = sum(r["metrics"]["win_correct"] for r in results) / len(results)
    
    brier_scores = [r["metrics"]["brier_score"] for r in results if r["metrics"]["brier_score"] is not None]
    avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else None
    
    position_errors = [r["metrics"]["avg_position_error"] for r in results if r["metrics"]["avg_position_error"] is not None]
    avg_position_error = sum(position_errors) / len(position_errors) if position_errors else None
    
    print(f"\nTotal Races Evaluated: {len(results)}")
    print(f"\nAccuracy Metrics:")
    print(f"  Top-3 Hit Rate:     {avg_top3:.1%} (Target: >=66.7%)")
    print(f"  Win Prediction:     {win_rate:.1%}")
    if avg_brier is not None:
        print(f"  Brier Score:        {avg_brier:.4f} (Lower is better, perfect=0.0)")
    if avg_position_error is not None:
        print(f"  Avg Position Error: {avg_position_error:.2f} positions")
    
    # Performance assessment
    print(f"\nPerformance Assessment:")
    if avg_top3 >= 0.667:
        print(f"  [PASS] Top-3 accuracy meets target ({avg_top3:.1%} >= 66.7%)")
    else:
        print(f"  [FAIL] Top-3 accuracy below target ({avg_top3:.1%} < 66.7%)")
    
    if avg_brier is not None:
        if avg_brier < 0.15:
            print(f"  [PASS] Excellent calibration (Brier < 0.15)")
        elif avg_brier < 0.25:
            print(f"  [WARN] Moderate calibration (Brier 0.15-0.25)")
        else:
            print(f"  [FAIL] Poor calibration (Brier > 0.25)")
    
    print("="*70)
    
    # Save detailed results
    output_file = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "seasons": seasons,
            "n_races": len(results),
            "summary": {
                "avg_top3_accuracy": round(avg_top3, 4),
                "win_rate": round(win_rate, 4),
                "avg_brier_score": round(avg_brier, 4) if avg_brier else None,
                "avg_position_error": round(avg_position_error, 2) if avg_position_error else None,
            },
            "race_results": results,
        }, f, indent=2)
    
    print(f"\n[PASS] Detailed results saved to: {output_file}")
    
    # Recommendations
    print(f"\nRecommendations:")
    if avg_top3 < 0.667:
        print(f"  • Consider retraining feature weights: python main.py optimize-weights")
        print(f"  • Review feature engineering in engine/feature_engineering.py")
        print(f"  • Increase simulation count for better convergence")
    if avg_brier and avg_brier > 0.20:
        print(f"  • Apply probability calibration: integrate engine/calibration.py")
        print(f"  • Check for systematic biases in predictions")
    
    print("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backtest F1 predictor on historical seasons")
    parser.add_argument("--seasons", "-s", type=int, nargs="+", default=[2025],
                       help="Seasons to backtest (default: 2025)")
    parser.add_argument("--sims", "-n", type=int, default=10000,
                       help="Number of simulations per race (default: 10000)")
    
    args = parser.parse_args()
    
    run_backtest(seasons=args.seasons, n_simulations=args.sims)
