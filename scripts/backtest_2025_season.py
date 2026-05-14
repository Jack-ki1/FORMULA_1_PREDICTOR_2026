"""
2025 Season Backtest Script.

Demonstrates temporal cross-validation — training window expands race by race.
Requires historical prediction snapshots in data/historical/2025/.

Structure expected:
  data/historical/2025/
    round_01_bahrain_predictions.json
    round_01_bahrain_outcomes.json
    round_02_jeddah_predictions.json
    ...

Each predictions JSON: list of {round, driver_id, win_prob, top3_prob, top10_prob}
Each outcomes JSON: list of {round, driver_id, position}
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

from engine.calibration import (
    temporal_cross_validate,
    brier_score,
    log_loss,
    generate_calibration_report,
)

console = Console()

HISTORICAL_DIR = Path(__file__).parent.parent / "data" / "historical" / "2025"


def load_historical_data() -> tuple:
    """
    Load all prediction and outcome files from disk.
    Returns (all_predictions, all_outcomes).
    """
    if not HISTORICAL_DIR.exists():
        console.print(f"[red]Historical data dir not found: {HISTORICAL_DIR}[/]")
        console.print("[dim]Create the directory and populate with round prediction/outcome JSON files.[/]")
        return [], []

    all_preds, all_outcomes = [], []
    pred_files = sorted(HISTORICAL_DIR.glob("*_predictions.json"))

    for pf in pred_files:
        of = Path(str(pf).replace("_predictions.json", "_outcomes.json"))
        if not of.exists():
            console.print(f"[yellow]Missing outcomes file for {pf.name}[/]")
            continue
        with open(pf) as f:
            all_preds.extend(json.load(f))
        with open(of) as f:
            all_outcomes.extend(json.load(f))

    return all_preds, all_outcomes


def run_backtest(min_train_races: int = 4) -> dict:
    console.rule("[bold cyan]2025 Season Backtest — Temporal Cross-Validation[/]")
    console.print(f"Historical data dir: {HISTORICAL_DIR}\n")

    all_preds, all_outcomes = load_historical_data()

    if not all_preds:
        console.print("[yellow]No historical data found. Showing framework demonstration.[/]\n")
        _demo_framework()
        return {}

    fold_results = temporal_cross_validate(all_preds, all_outcomes, min_train_races)

    table = Table(title="Backtest Results — Per-Fold Metrics", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
    table.add_column("Round", justify="center")
    table.add_column("Drivers", justify="center")
    table.add_column("Win Brier↓", justify="center")
    table.add_column("Win LogLoss↓", justify="center")
    table.add_column("Top3 Brier↓", justify="center")
    table.add_column("Top3 LogLoss↓", justify="center")

    for f in fold_results:
        table.add_row(
            str(f["test_round"]),
            str(f["n_drivers"]),
            f"[green]{f['win_brier']:.4f}[/]" if f["win_brier"] < 0.05 else str(f["win_brier"]),
            str(f["win_logloss"]),
            str(f["top3_brier"]),
            str(f["top3_logloss"]),
        )

    console.print(table)

    if fold_results:
        avg_win_brier = sum(f["win_brier"] for f in fold_results) / len(fold_results)
        avg_top3_brier = sum(f["top3_brier"] for f in fold_results) / len(fold_results)
        console.print(f"\n[bold]Season averages:[/]  Win Brier = {avg_win_brier:.4f}  |  Top-3 Brier = {avg_top3_brier:.4f}")
        console.print("[dim]Reference: Perfect model = 0.000 · Baseline (uniform) ≈ 0.048 for win prediction[/]")

    return {"folds": fold_results}


def _demo_framework():
    """Show calibration concepts with synthetic data."""
    import random
    rng = random.Random(2026)

    probs = [rng.uniform(0, 1) for _ in range(200)]
    outcomes = [1 if rng.random() < p else 0 for p in probs]

    bs = brier_score(probs, outcomes)
    ll = log_loss(probs, outcomes)
    cal = generate_calibration_report(probs, outcomes, n_bins=5)

    console.print("[bold]Calibration framework demo (synthetic data)[/]")
    console.print(f"  Brier score: {bs:.4f}  |  Log-loss: {ll:.4f}\n")

    table = Table(title="Calibration Bins", box=box.SIMPLE)
    table.add_column("Bin")
    table.add_column("N")
    table.add_column("Mean Predicted")
    table.add_column("Actual Rate")
    table.add_column("Cal. Error")

    for row in cal:
        err_str = f"[red]{row['calibration_error']:.4f}[/]" if row["calibration_error"] > 0.1 else f"{row['calibration_error']:.4f}"
        table.add_row(row["bin"], str(row["n"]),
                      str(row["mean_predicted"]), str(row["actual_rate"]), err_str)

    console.print(table)
    console.print("\n[dim]Replace synthetic data with real historical prediction snapshots to run a full backtest.[/]")


if __name__ == "__main__":
    run_backtest()
