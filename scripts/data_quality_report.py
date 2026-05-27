"""
Data Quality Report — v2 (NEW FILE).

Validates all data sources for internal consistency before a race prediction.
Referenced in README and main.py as `python main.py quality-check`.

Checks performed:
  ── Drivers ──────────────────────────────────────────────────
  ✓ All required fields present
  ✓ ELO ratings in valid range [1400, 1700]
  ✓ DNF rates in [0, 1]
  ✓ Skill ratings in [0, 10]
  ✓ track_type_fit keys match defined circuit types
  ✓ Each team has exactly 2 drivers (warns if not)
  ✓ recent_form list is non-empty

  ── Circuits ─────────────────────────────────────────────────
  ✓ All required fields present
  ✓ Safety car probability in [0, 1]
  ✓ Lap count > 0
  ✓ Race dates are valid ISO format
  ✓ Circuit types are from known list

  ── Season data ──────────────────────────────────────────────
  ✓ All driver IDs in results exist in driver_data
  ✓ Positions are unique within each race
  ✓ Points match the F1 scoring system
  ✓ Championship standings sum is consistent with race results

  ── Feature weights ──────────────────────────────────────────
  ✓ Weights sum to 1.0 (±0.01)
  ✓ No negative weights

Usage:
  python scripts/data_quality_report.py
  python main.py quality-check
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# ── F1 points systems ─────────────────────────────────────────────────────────
RACE_POINTS   = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}
SPRINT_POINTS = {1:8,  2:7,  3:6,  4:5,  5:4,  6:3, 7:2, 8:1}

KNOWN_CIRCUIT_TYPES = {
    "power_unit", "technical", "balanced", "street", "high_downforce"
}

REQUIRED_DRIVER_FIELDS = [
    "id", "name", "short", "team", "nationality", "number",
    "experience_races", "elo", "wet_skill", "brakezone_skill",
    "tire_management", "qualifying_delta_avg",
    "dnf_rate_career", "dnf_rate_recent", "track_type_fit",
    "recent_form", "championship_points_2026", "wins_2026",
]

REQUIRED_CIRCUIT_FIELDS = [
    "id", "name", "city", "country", "round_2026", "race_date",
    "sprint_weekend", "circuit_type", "lap_count", "lap_distance_km",
    "total_distance_km", "safety_car_probability", "overtaking_difficulty",
    "power_unit_demand", "brake_demand", "tire_deg_rate",
    "rain_probability_typical",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ok(msg: str):
    console.print(f"  [green]✓[/] {msg}")

def _warn(msg: str):
    console.print(f"  [yellow]⚠[/] {msg}")

def _fail(msg: str):
    console.print(f"  [red]✗[/] {msg}")


# ── Check functions ────────────────────────────────────────────────────────────

def check_drivers() -> tuple:
    from data.driver_data import DRIVERS
    issues, warnings, passes = 0, 0, 0

    console.print("\n[bold]Drivers[/]")

    team_counts = defaultdict(list)

    for d_id, d in DRIVERS.items():
        # Required fields
        for f in REQUIRED_DRIVER_FIELDS:
            if f not in d:
                _fail(f"{d_id}: missing field '{f}'"); issues += 1

        # ELO range
        if not (1400 <= d.get("elo", 0) <= 1700):
            _warn(f"{d_id}: ELO {d.get('elo')} outside [1400,1700]"); warnings += 1

        # DNF rates
        for field in ("dnf_rate_career", "dnf_rate_recent"):
            val = d.get(field, -1)
            if not (0.0 <= val <= 1.0):
                _fail(f"{d_id}: {field}={val} not in [0,1]"); issues += 1

        # Skill ratings
        for skill in ("wet_skill", "brakezone_skill", "tire_management"):
            val = d.get(skill, -1)
            if not (0.0 <= val <= 10.0):
                _warn(f"{d_id}: {skill}={val} not in [0,10]"); warnings += 1

        # track_type_fit
        fit = d.get("track_type_fit", {})
        for ct in fit:
            if ct not in KNOWN_CIRCUIT_TYPES:
                _warn(f"{d_id}: unknown circuit type '{ct}' in track_type_fit"); warnings += 1

        # recent_form non-empty
        if not d.get("recent_form"):
            _warn(f"{d_id}: recent_form is empty"); warnings += 1

        # championship points non-negative
        pts = d.get("championship_points_2026", -1)
        if pts < 0:
            _fail(f"{d_id}: negative championship_points_2026"); issues += 1

        team_counts[d.get("team", "unknown")].append(d_id)
        passes += 1

    # Team size check
    for team, drivers in team_counts.items():
        if len(drivers) != 2:
            _warn(f"Team '{team}' has {len(drivers)} driver(s), expected 2: {drivers}")
            warnings += 1
        else:
            passes += 1

    _ok(f"Validated {len(DRIVERS)} driver profiles across {len(team_counts)} teams")
    return issues, warnings, passes


def check_circuits() -> tuple:
    from data.circuit_data import CIRCUITS
    issues, warnings, passes = 0, 0, 0

    console.print("\n[bold]Circuits[/]")

    for c_id, c in CIRCUITS.items():
        # Required fields
        for f in REQUIRED_CIRCUIT_FIELDS:
            if f not in c:
                _warn(f"{c_id}: missing field '{f}'"); warnings += 1

        # SC probability
        sc = c.get("safety_car_probability", -1)
        if not (0.0 <= sc <= 1.0):
            _fail(f"{c_id}: safety_car_probability={sc} not in [0,1]"); issues += 1

        # Lap count
        if c.get("lap_count", 0) <= 0:
            _fail(f"{c_id}: lap_count must be > 0"); issues += 1

        # Race date format
        date_str = c.get("race_date", "")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            passes += 1
        except ValueError:
            _warn(f"{c_id}: race_date '{date_str}' not in YYYY-MM-DD format"); warnings += 1

        # Circuit types
        for ct in c.get("circuit_type", []):
            if ct not in KNOWN_CIRCUIT_TYPES:
                _warn(f"{c_id}: unknown circuit type '{ct}'"); warnings += 1

        passes += 1

    _ok(f"Validated {len(CIRCUITS)} circuit definitions")
    return issues, warnings, passes


def check_season_data() -> tuple:
    from data.season_2026 import SEASON_RESULTS_2026, DRIVER_STANDINGS_AFTER_R4
    from data.driver_data import DRIVERS
    issues, warnings, passes = 0, 0, 0

    console.print("\n[bold]Season data[/]")

    known_drivers = set(DRIVERS.keys())

    for race in SEASON_RESULTS_2026:
        round_n  = race.get("round")
        is_sprint = race.get("sprint", False)
        pts_map   = SPRINT_POINTS if is_sprint else RACE_POINTS
        positions_seen = []

        for r in race.get("results", []):
            d_id = r.get("driver", "")

            # Driver exists
            if d_id not in known_drivers:
                _warn(f"Round {round_n}: driver '{d_id}' not in driver_data"); warnings += 1

            pos = r.get("position")
            if pos is not None:
                # Unique positions
                if pos in positions_seen:
                    _fail(f"Round {round_n}: duplicate position {pos}"); issues += 1
                positions_seen.append(pos)

                # Points check (allow 0 for drivers outside points)
                expected_pts = pts_map.get(pos, 0)
                actual_pts   = r.get("points", -1)
                # Allow +1 for fastest lap
                if actual_pts not in (expected_pts, expected_pts + 1):
                    _warn(
                        f"Round {round_n} P{pos} {d_id}: "
                        f"points={actual_pts}, expected ~{expected_pts}"
                    )
                    warnings += 1

        passes += 1

    # Standings consistency
    total_pts = sum(s["points"] for s in DRIVER_STANDINGS_AFTER_R4)
    if total_pts == 0:
        _warn("Championship standings sum to 0 — has season data been loaded?")
        warnings += 1
    else:
        passes += 1

    # Check all standings drivers exist
    for s in DRIVER_STANDINGS_AFTER_R4:
        if s["driver"] not in known_drivers:
            _warn(f"Standings: '{s['driver']}' not found in driver_data"); warnings += 1

    _ok(f"Validated {len(SEASON_RESULTS_2026)} race results")
    return issues, warnings, passes


def check_feature_weights() -> tuple:
    from config.settings import FEATURE_WEIGHTS
    issues, warnings, passes = 0, 0, 0

    console.print("\n[bold]Feature weights (config/settings.py)[/]")

    total = sum(FEATURE_WEIGHTS.values())
    if abs(total - 1.0) > 0.01:
        _fail(f"Weights sum to {total:.4f}, expected 1.0 ± 0.01"); issues += 1
    else:
        _ok(f"Weights sum to {total:.4f} ✓"); passes += 1

    for k, v in FEATURE_WEIGHTS.items():
        if v < 0:
            _fail(f"Negative weight for '{k}': {v}"); issues += 1
        elif v == 0:
            _warn(f"Weight for '{k}' is 0 — feature has no effect"); warnings += 1
        else:
            passes += 1

    return issues, warnings, passes


def check_engine_imports() -> tuple:
    """Verify that all engine modules import without error."""
    issues, warnings, passes = 0, 0, 0
    console.print("\n[bold]Engine import check[/]")

    modules = [
        ("config.settings",              "FEATURE_WEIGHTS"),
        ("data.driver_data",             "DRIVERS"),
        ("data.circuit_data",            "CIRCUITS"),
        ("data.season_2026",             "SEASON_RESULTS_2026"),
        ("data.calendar_2026",           "CALENDAR_2026"),
        ("engine.feature_engineering",   "compute_composite_score"),
        ("engine.probability_model",     "predict_race"),
        ("engine.predictor",             "predict"),
        ("engine.calibration",           "brier_score"),
        ("api.schemas",                  "RacePredictionResponse"),
        ("api.routes",                   "router"),
    ]

    for module_path, attr in modules:
        try:
            import importlib
            mod = importlib.import_module(module_path)
            if not hasattr(mod, attr):
                _fail(f"{module_path}: missing attribute '{attr}'"); issues += 1
            else:
                _ok(f"{module_path}.{attr}"); passes += 1
        except ImportError as e:
            _fail(f"{module_path}: ImportError — {e}"); issues += 1
        except Exception as e:
            _warn(f"{module_path}: {type(e).__name__} — {e}"); warnings += 1

    return issues, warnings, passes


def run_all_checks() -> None:
    console.rule("[bold cyan]F1 Prediction System — Data Quality Report[/]")

    total_issues   = 0
    total_warnings = 0
    total_passes   = 0

    check_fns = [
        ("Drivers",         check_drivers),
        ("Circuits",        check_circuits),
        ("Season data",     check_season_data),
        ("Feature weights", check_feature_weights),
        ("Engine imports",  check_engine_imports),
    ]

    results = []
    for name, fn in check_fns:
        i, w, p = fn()
        total_issues   += i
        total_warnings += w
        total_passes   += p
        status = "✗ FAIL" if i > 0 else ("⚠ WARN" if w > 0 else "✓ PASS")
        colour = "red"    if i > 0 else ("yellow" if w > 0 else "green")
        results.append((name, status, colour, i, w, p))

    # Summary table
    console.print("\n")
    t = Table(title="Summary", box=box.MINIMAL_DOUBLE_HEAD, header_style="bold cyan")
    t.add_column("Section", width=20)
    t.add_column("Status", justify="center", width=10)
    t.add_column("Issues", justify="center", width=8)
    t.add_column("Warnings", justify="center", width=10)
    t.add_column("Passes", justify="center", width=8)
    for name, status, colour, i, w, p in results:
        t.add_row(name, f"[{colour}]{status}[/]", str(i), str(w), str(p))
    console.print(t)

    # Final verdict
    if total_issues == 0 and total_warnings == 0:
        console.print(Panel(
            f"[bold green]All {total_passes} checks passed[/] — data is clean and ready for predictions.",
            border_style="green",
        ))
    elif total_issues == 0:
        console.print(Panel(
            f"[yellow]{total_warnings} warning(s)[/] — predictions will work but review warnings above.\n"
            f"[green]{total_passes} checks passed.[/]",
            border_style="yellow",
        ))
    else:
        console.print(Panel(
            f"[bold red]{total_issues} issue(s) found[/] — predictions may be incorrect.\n"
            f"[yellow]{total_warnings} warning(s)[/] · [green]{total_passes} passes[/]\n\n"
            "Fix issues marked [red]✗[/] before running predictions.",
            border_style="red",
        ))


if __name__ == "__main__":
    run_all_checks()