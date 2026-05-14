"""
End-of-Season Archive Script.

Archives all 2026 data and prepares the project for the 2027 season.

Usage:
  python scripts/archive_season.py --season 2026
  python scripts/archive_season.py --season 2026 --prepare-next   # also sets up 2027
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import json
import shutil
import math
from pathlib import Path
from datetime import date
from rich.console import Console
from rich.panel import Panel

console = Console()

DATA_DIR = Path(__file__).parent.parent / "data"


def apply_elo_decay(current_elos: dict, decay: float = 0.10, mean: float = 1500) -> dict:
    """
    Decay ELO ratings toward the mean at the start of a new season.
    Prevents over-anchoring on previous-season performance.
    new_elo = old_elo + decay * (mean - old_elo)
    """
    return {d: round(elo + decay * (mean - elo), 1) for d, elo in current_elos.items()}


def archive_season(season: int):
    """Copy current season files into historical archive."""
    archive_dir = DATA_DIR / "historical" / str(season)
    archive_dir.mkdir(parents=True, exist_ok=True)

    files_to_archive = [
        DATA_DIR / f"season_{season}.py",
        DATA_DIR / "driver_data.py",
        DATA_DIR / "circuit_data.py",
        DATA_DIR / f"calendar_{season}.py",
    ]

    archived = []
    for src in files_to_archive:
        if src.exists():
            dst = archive_dir / f"FINAL_{src.name}"
            shutil.copy2(src, dst)
            archived.append(str(dst))

    console.print(f"[green]✓ Archived {len(archived)} files to {archive_dir}/[/]")
    for f in archived:
        console.print(f"  {f}")


def prepare_next_season(current_season: int, decay: float):
    """Generate starter files for the next season."""
    next_season = current_season + 1
    console.print(f"\n[cyan]Preparing {next_season} season files…[/]")

    # Load current driver data
    sys.path.insert(0, str(DATA_DIR.parent))
    from data.driver_data import DRIVERS

    # Apply ELO decay
    current_elos = {d_id: d["elo"] for d_id, d in DRIVERS.items()}
    new_elos = apply_elo_decay(current_elos, decay=decay)

    console.print(f"\n[bold]ELO ratings after {decay*100:.0f}% decay toward {1500}:[/]")
    for d_id, new_elo in sorted(new_elos.items(), key=lambda x: -x[1])[:10]:
        old = current_elos[d_id]
        console.print(f"  {d_id:15s}  {old} → {new_elo}  ({new_elo - old:+.1f})")

    # Write next season file template
    next_season_file = DATA_DIR / f"season_{next_season}.py"
    template = f'''"""
{next_season} F1 Season — Race Results Database.
Auto-generated from archive_season.py at end of {current_season} season.
"""

SEASON_RESULTS_{next_season}: list = []
# Add race results here after each round

DRIVER_STANDINGS_AFTER_R0: list = [
    # Reset to 0 points — update after each race
    {chr(10).join(f'    {{"position": {i+1}, "driver": "{d_id}", "points": 0}},' for i, d_id in enumerate(list(DRIVERS.keys())))}
]

CONSTRUCTOR_STANDINGS_AFTER_R0: list = [
    # Reset to 0 — update after each race
]
'''
    with open(next_season_file, "w") as f:
        f.write(template)

    console.print(f"\n[green]✓ Created {next_season_file.name}[/]")

    # Print ELO update instructions
    console.print(Panel(
        f"Manual steps for {next_season} season:\n\n"
        "1. Apply the ELO values above to [cyan]data/driver_data.py[/]\n"
        f"2. Update driver rosters (departures, rookies, seat changes)\n"
        f"3. Create [cyan]data/calendar_{next_season}.py[/] with the new schedule\n"
        "4. Reset constructor strengths in [cyan]engine/feature_engineering.py[/]\n"
        "   based on pre-season testing performance\n"
        f"5. Run: python scripts/recalibrate_model.py --season {current_season} --fit-platt\n"
        "   to refit calibration on full completed season",
        title=f"[bold]{next_season} Season Preparation Checklist[/]",
    ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--prepare-next", action="store_true", help="Also set up next season files")
    parser.add_argument("--elo-decay", type=float, default=0.10, help="ELO decay rate toward mean")
    args = parser.parse_args()

    console.rule(f"[bold cyan]End-of-Season Archive — {args.season}[/]")
    archive_season(args.season)

    if args.prepare_next:
        prepare_next_season(args.season, args.elo_decay)

    console.print(f"\n[bold green]✓ Season {args.season} archive complete[/]\n")


if __name__ == "__main__":
    main()
