"""
Post-Race Update Script.

Automates the most tedious maintenance task: after each race, update
  1. Season results in data/season_2026.py
  2. Driver ELO ratings
  3. Recent form arrays
  4. Championship standings

Usage:
  python scripts/post_race_update.py --round 5 --circuit canada \
    --results "antonelli:1,russell:2,norris:3,piastri:4,verstappen:5,\
               hamilton:6,bearman:7,leclerc:DNF"

  # With sprint flag
  python scripts/post_race_update.py --round 5 --circuit canada --sprint \
    --results "antonelli:1,norris:2,piastri:3"

  # Dry-run (preview changes without writing)
  python scripts/post_race_update.py --round 5 --circuit canada \
    --results "..." --dry-run
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import math
import copy
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# ELO K-factor
K = 32


def parse_results(results_str: str) -> list:
    """
    Parse "driver:pos,driver:pos" string into a list of dicts.
    DNF is recorded as position None.
    """
    entries = []
    if not results_str:
        return entries
    for part in results_str.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        driver_id, pos_str = part.split(":", 1)
        pos = None if pos_str.upper() == "DNF" else int(pos_str)
        entries.append({"driver": driver_id.strip(), "position": pos, "dnf": pos is None})
    return entries


def compute_elo_updates(results: list, current_elos: dict) -> dict:
    """
    Pairwise ELO update based on finishing order.
    Each finisher is compared against every other finisher.
    Returns {driver_id: new_elo}.
    """
    finishers = [(r["driver"], r["position"]) for r in results if r["position"] is not None]
    finishers.sort(key=lambda x: x[1])  # sort by position

    elo_deltas = {d: 0.0 for d, _ in finishers}

    for i, (d1, p1) in enumerate(finishers):
        for j, (d2, p2) in enumerate(finishers):
            if i == j:
                continue
            elo1 = current_elos.get(d1, 1500)
            elo2 = current_elos.get(d2, 1500)
            expected = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
            actual = 1.0 if p1 < p2 else 0.0  # lower pos = better finish
            elo_deltas[d1] += K / len(finishers) * (actual - expected)

    updated = {}
    for d, delta in elo_deltas.items():
        old = current_elos.get(d, 1500)
        updated[d] = round(old + delta, 1)
    return updated


def points_for_position(pos: int, sprint: bool = False) -> int:
    """Return championship points for a finishing position."""
    if sprint:
        pts_map = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
    else:
        pts_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    return pts_map.get(pos, 0)


def load_driver_elos() -> dict:
    """Load current ELO ratings from driver data."""
    from data.driver_data import DRIVERS
    return {d_id: d["elo"] for d_id, d in DRIVERS.items()}


def generate_season_result_entry(round_num: int, circuit: str, race_date: str,
                                  sprint: bool, results: list) -> dict:
    """Build a season result entry ready to paste into season_2026.py."""
    result_entries = []
    for r in results:
        pts = 0 if r["dnf"] else points_for_position(r["position"], sprint)
        result_entries.append({
            "driver": r["driver"],
            "position": r["position"],
            "grid": None,  # set manually
            "points": pts,
            "dnf": r["dnf"],
            "fastest_lap": False,
        })
    return {
        "round": round_num,
        "circuit": circuit,
        "name": f"{circuit.replace('_', ' ').title()} Grand Prix",
        "date": race_date,
        "sprint": sprint,
        "results": result_entries,
    }


def save_historical_snapshot(round_num: int, circuit: str, predictions: dict, outcomes: list):
    """Save a prediction snapshot for backtesting."""
    hist_dir = Path(__file__).parent.parent / "data" / "historical" / "2026"
    hist_dir.mkdir(parents=True, exist_ok=True)
    fname = hist_dir / f"round_{round_num:02d}_{circuit}_outcomes.json"
    with open(fname, "w") as f:
        json.dump(outcomes, f, indent=2)
    console.print(f"[dim]Historical snapshot saved → {fname}[/]")


def main():
    parser = argparse.ArgumentParser(description="Post-race update tool")
    parser.add_argument("--round", type=int, required=True, help="Race round number")
    parser.add_argument("--circuit", type=str, required=True, help="Circuit ID")
    parser.add_argument("--results", type=str, default="", help="driver:pos,... (DNF = no position)")
    parser.add_argument("--sprint", action="store_true", help="Mark as sprint race results")
    parser.add_argument("--date", type=str, default=str(date.today()), help="Race date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    parser.add_argument("--update-elo", action="store_true", default=True, help="Recalculate ELO")
    args = parser.parse_args()

    results = parse_results(args.results)
    if not results:
        console.print("[yellow]No results provided. Use --results 'driver:pos,...'[/]")
        return

    console.rule(f"[bold cyan]Post-Race Update — Round {args.round} · {args.circuit.upper()}[/]")

    # Show parsed results
    t = Table(title="Parsed Results", box=box.SIMPLE)
    t.add_column("Driver"); t.add_column("Position"); t.add_column("DNF"); t.add_column("Points")
    for r in sorted(results, key=lambda x: (x["position"] or 99)):
        pts = 0 if r["dnf"] else points_for_position(r["position"], args.sprint)
        t.add_row(r["driver"],
                  str(r["position"] or "—"),
                  "[red]YES[/]" if r["dnf"] else "No",
                  str(pts))
    console.print(t)

    # ELO update preview
    if args.update_elo:
        current_elos = load_driver_elos()
        new_elos = compute_elo_updates(results, current_elos)
        elo_t = Table(title="ELO Changes", box=box.SIMPLE)
        elo_t.add_column("Driver"); elo_t.add_column("Old ELO"); elo_t.add_column("New ELO"); elo_t.add_column("Delta")
        for d, new_elo in new_elos.items():
            old = current_elos.get(d, 1500)
            delta = new_elo - old
            colour = "green" if delta > 0 else "red"
            elo_t.add_row(d, str(old), str(new_elo), f"[{colour}]{delta:+.1f}[/]")
        console.print(elo_t)

    # Season result entry snippet
    entry = generate_season_result_entry(args.round, args.circuit, args.date, args.sprint, results)
    console.print("\n[bold]Season result entry (paste into data/season_2026.py):[/]")
    console.print(json.dumps(entry, indent=4))

    if args.dry_run:
        console.print("\n[yellow]Dry-run mode: no files were modified.[/]")
        return

    # Save historical snapshot for backtesting
    outcomes_for_backtest = [
        {"round": args.round, "driver_id": r["driver"], "position": r["position"]}
        for r in results if not r["dnf"]
    ]
    save_historical_snapshot(args.round, args.circuit, {}, outcomes_for_backtest)

    console.print(f"\n[bold]Next steps:[/]")
    console.print("  1. Paste the season result entry above into [cyan]data/season_2026.py[/]")
    console.print("  2. Update DRIVER_STANDINGS and CONSTRUCTOR_STANDINGS in [cyan]data/season_2026.py[/]")
    if args.update_elo:
        console.print("  3. Apply the ELO changes to [cyan]data/driver_data.py[/]")
    console.print("  4. Run [cyan]python main.py predict --race <next_race>[/] to preview next event\n")


if __name__ == "__main__":
    main()
