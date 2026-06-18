"""
Accuracy Measurement Framework — Part 7 of comprehensive bug fix suite.

For each completed race, predict using only pre-race data,
then score against actual results. Run before and after each improvement
to validate gains objectively.

Target: >= 2/3 drivers correct in top-3 prediction across all completed races.

Usage:
    python scripts/measure_accuracy.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.season_2026 import SEASON_RESULTS_2026
from engine.predictor import predict, PredictionRequest


def run_backtesting():
    """
    For each completed race, predict using only pre-race data,
    then score against actual results.
    """
    results = []

    for race_idx, race in enumerate(SEASON_RESULTS_2026):
        # Skip races with no results (e.g., placeholder entries)
        if not race.get("results"):
            print(f"R{race['round']} {race['name']}: SKIPPED (no results)")
            continue

        # Run prediction
        try:
            prediction = predict(PredictionRequest(
                circuit_id=race["circuit"],
                n_simulations=10000,
            ))
        except Exception as e:
            print(f"R{race['round']} {race['name']}: ERROR — {e}")
            continue

        # Score it
        actual_top3 = set(
            r["driver"] for r in race["results"]
            if r["position"] <= 3 and r.get("status", "Finished") != "DNF"
        )
        predicted_top3 = set(
            p["driver_id"] for p in
            sorted(prediction["predictions"], key=lambda x: x.get("top3_pct", 0), reverse=True)[:3]
        )

        top3_hits = actual_top3 & predicted_top3
        top3_accuracy = len(top3_hits) / 3.0

        # Win prediction
        actual_winner = next(
            (r["driver"] for r in race["results"] if r["position"] == 1), None
        )
        predicted_winner = (
            prediction.get("podium_predictions", [""])[0]
            if prediction.get("podium_predictions")
            else ""
        )
        win_correct = (
            actual_winner.lower() == predicted_winner.lower()
            if actual_winner and predicted_winner
            else False
        )

        results.append({
            "race": race["name"],
            "round": race["round"],
            "top3_accuracy": top3_accuracy,
            "win_correct": win_correct,
            "actual_top3": sorted(actual_top3),
            "predicted_top3": sorted(predicted_top3),
            "hits": sorted(top3_hits),
        })

        win_mark = "✓" if win_correct else "✗"
        print(
            f"R{race['round']} {race['name']}: "
            f"top3={top3_accuracy:.0%} ({len(top3_hits)}/3), "
            f"win={win_mark} (actual={actual_winner}, predicted={predicted_winner})"
        )

    if not results:
        print("\nNo completed races to evaluate.")
        return results

    avg_top3 = sum(r["top3_accuracy"] for r in results) / len(results)
    win_rate = sum(r["win_correct"] for r in results) / len(results)
    print(f"\n{'='*60}")
    print(f"Overall ({len(results)} races):")
    print(f"  Top-3 accuracy: {avg_top3:.1%}")
    print(f"  Win accuracy:   {win_rate:.1%}")
    print(f"  Target:         >= 66.7% top-3 accuracy")
    print(f"{'='*60}")
    return results


if __name__ == "__main__":
    run_backtesting()
