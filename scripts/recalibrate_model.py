"""
Model Recalibration Script.

Runs every ~6 races to:
  1. Compute Brier score, log-loss, RPS across all completed rounds
  2. Refit Platt scaling parameters (A, B) on observed data
  3. Suggest updated FEATURE_WEIGHTS
  4. Print calibration curves

Usage:
  python scripts/recalibrate_model.py
  python scripts/recalibrate_model.py --fit-platt   # Update Platt params in code
  python scripts/recalibrate_model.py --season 2026
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import random
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from engine.calibration import (
    brier_score, log_loss, platt_scale,
    apply_platt_scale, generate_calibration_report,
    permutation_feature_importance,
)

console = Console()


def load_season_snapshots(season: int) -> tuple:
    """Load prediction snapshots and outcomes for a completed season."""
    hist_dir = Path(__file__).parent.parent / "data" / "historical" / str(season)
    if not hist_dir.exists():
        return [], []

    all_preds, all_outcomes = [], []
    for pf in sorted(hist_dir.glob("*_predictions.json")):
        of = Path(str(pf).replace("_predictions.json", "_outcomes.json"))
        if not of.exists():
            continue
        with open(pf) as f:
            all_preds.extend(json.load(f))
        with open(of) as f:
            all_outcomes.extend(json.load(f))
    return all_preds, all_outcomes


def synthetic_season_data(n_races: int = 4, n_drivers: int = 20) -> tuple:
    """Generate synthetic data for demonstration when no historical data exists."""
    rng = random.Random(2026)
    preds, outcomes = [], []
    for r in range(1, n_races + 1):
        for i in range(n_drivers):
            win_p = rng.uniform(0, 0.3) if i < 5 else rng.uniform(0, 0.05)
            top3_p = min(win_p * 4, 0.95)
            actual_pos = rng.randint(1, n_drivers)
            preds.append({
                "round": r, "driver_id": f"driver_{i:02d}",
                "win_prob": win_p, "top3_prob": top3_p, "top10_prob": min(top3_p * 2.5, 1.0)
            })
            outcomes.append({"round": r, "driver_id": f"driver_{i:02d}", "position": actual_pos})
    return preds, outcomes


def run_recalibration(season: int, fit_platt: bool = False):
    console.rule(f"[bold cyan]Model Recalibration — {season} Season[/]")

    preds, outcomes = load_season_snapshots(season)
    if not preds:
        console.print(f"[yellow]No historical snapshots found for {season}. Using synthetic data for demo.[/]\n")
        preds, outcomes = synthetic_season_data()

    # Build outcome lookup
    outcome_map = {(o["round"], o["driver_id"]): o["position"] for o in outcomes}

    win_probs, win_outcomes_list = [], []
    top3_probs, top3_outcomes_list = [], []

    for p in preds:
        key = (p["round"], p["driver_id"])
        if key not in outcome_map:
            continue
        actual_pos = outcome_map[key]
        win_probs.append(p["win_prob"])
        win_outcomes_list.append(1 if actual_pos == 1 else 0)
        top3_probs.append(p["top3_prob"])
        top3_outcomes_list.append(1 if actual_pos <= 3 else 0)

    if not win_probs:
        console.print("[red]No matched predictions found.[/]")
        return

    # Metrics
    win_bs = brier_score(win_probs, win_outcomes_list)
    win_ll = log_loss(win_probs, win_outcomes_list)
    top3_bs = brier_score(top3_probs, top3_outcomes_list)
    top3_ll = log_loss(top3_probs, top3_outcomes_list)

    metrics_t = Table(title="Prediction Accuracy Metrics", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
    metrics_t.add_column("Metric")
    metrics_t.add_column("Win")
    metrics_t.add_column("Top 3")
    metrics_t.add_column("Reference (random)")

    def colour_score(v, low=0.04, high=0.07):
        if v < low: return f"[green]{v:.4f}[/]"
        if v > high: return f"[red]{v:.4f}[/]"
        return f"[yellow]{v:.4f}[/]"

    metrics_t.add_row("Brier Score ↓",  colour_score(win_bs), colour_score(top3_bs, 0.12, 0.20), "≈ 0.048")
    metrics_t.add_row("Log-Loss ↓",     colour_score(win_ll, 0.10, 0.20), colour_score(top3_ll, 0.30, 0.60), "—")
    metrics_t.add_row("Sample size",     str(len(win_probs)), str(len(top3_probs)), "—")
    console.print(metrics_t)

    # Calibration report
    console.print("\n[bold]Win probability calibration:[/]")
    cal = generate_calibration_report(win_probs, win_outcomes_list, n_bins=5)
    cal_t = Table(box=box.SIMPLE, header_style="cyan")
    cal_t.add_column("Predicted bin"); cal_t.add_column("N"); cal_t.add_column("Mean Predicted")
    cal_t.add_column("Actual Rate"); cal_t.add_column("Cal. Error")
    for row in cal:
        err_c = "[red]" if row["calibration_error"] > 0.10 else ""
        cal_t.add_row(row["bin"], str(row["n"]),
                      str(row["mean_predicted"]), str(row["actual_rate"]),
                      f"{err_c}{row['calibration_error']:.4f}" + ("[/]" if err_c else ""))
    console.print(cal_t)

    # Platt scaling
    console.print("\n[bold]Platt scaling refit:[/]")
    A_win, B_win = platt_scale(win_probs, win_outcomes_list)
    A_top3, B_top3 = platt_scale(top3_probs, top3_outcomes_list)
    console.print(f"  Win:  A = [cyan]{A_win}[/]   B = [cyan]{B_win}[/]")
    console.print(f"  Top3: A = [cyan]{A_top3}[/]  B = [cyan]{B_top3}[/]")

    if fit_platt:
        # Write updated values back to probability_model.py
        model_path = Path(__file__).parent.parent / "engine" / "probability_model.py"
        content = model_path.read_text()
        content = content.replace(
            f"PLATT_A_WIN = {_current_platt_val(content, 'PLATT_A_WIN')}",
            f"PLATT_A_WIN = {A_win}"
        ).replace(
            f"PLATT_B_WIN = {_current_platt_val(content, 'PLATT_B_WIN')}",
            f"PLATT_B_WIN = {B_win}"
        ).replace(
            f"PLATT_A_TOP3 = {_current_platt_val(content, 'PLATT_A_TOP3')}",
            f"PLATT_A_TOP3 = {A_top3}"
        ).replace(
            f"PLATT_B_TOP3 = {_current_platt_val(content, 'PLATT_B_TOP3')}",
            f"PLATT_B_TOP3 = {B_top3}"
        )
        model_path.write_text(content)
        console.print("[green]✓ Platt parameters updated in engine/probability_model.py[/]")
    else:
        console.print("[dim]Re-run with --fit-platt to apply these values automatically.[/]")

    # Feature importance
    console.print("\n[bold]Feature importance (permutation — sample driver: antonelli):[/]")
    try:
        importance = permutation_feature_importance("antonelli", "canada")
        fi_t = Table(box=box.SIMPLE, header_style="cyan")
        fi_t.add_column("Feature"); fi_t.add_column("Importance (score drop)")
        for feat, imp in list(importance.items())[:6]:
            fi_t.add_row(feat, f"{imp:+.5f}")
        console.print(fi_t)
    except Exception as e:
        console.print(f"[dim]Feature importance unavailable: {e}[/]")

    console.print(Panel(
        f"Brier (win): [{'green' if win_bs < 0.04 else 'yellow' if win_bs < 0.07 else 'red'}]{win_bs:.4f}[/]\n"
        f"Brier (top3): [{'green' if top3_bs < 0.12 else 'yellow'}]{top3_bs:.4f}[/]\n\n"
        f"[dim]Suggested action: {'Model is well-calibrated ✓' if win_bs < 0.05 else 'Review FEATURE_WEIGHTS in config/settings.py'}[/]",
        title="[bold]Calibration Summary[/]",
    ))


def _current_platt_val(content: str, var_name: str) -> str:
    """Extract current Platt value from source code."""
    for line in content.split("\n"):
        if line.strip().startswith(var_name):
            return line.split("=")[1].strip()
    return "1.0"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--fit-platt", action="store_true")
    args = parser.parse_args()
    run_recalibration(args.season, args.fit_platt)
