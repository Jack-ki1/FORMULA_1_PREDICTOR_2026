"""
Data-integrity invariants for the 2026 grid.

Deliberately tiny, boring assertions. They exist because a *silent* data bug —
Racing Bulls listed with three drivers — shipped and quietly ran every Monte
Carlo over a 23-entrant grid instead of 22, diluting every probability in the
app (modify.md section 1.5). A one-line test would have caught it.
"""
from collections import Counter

from backend.app.config.team_driver_lineup_2026 import (
    TEAMS_2026,
    get_all_drivers,
    get_driver_count,
    get_team_count,
)
from backend.app.config.constants import grid_size


def test_grid_is_exactly_two_drivers_per_team():
    for team in TEAMS_2026:
        assert len(team["drivers"]) == 2, (
            f"{team['id']} has {len(team['drivers'])} drivers "
            f"({[d['code'] for d in team['drivers']]}) — must be exactly 2"
        )


def test_grid_size_is_22():
    assert get_team_count() == 11
    assert get_driver_count() == 22
    assert len(get_all_drivers()) == 22
    assert grid_size() == 22


def test_no_duplicate_driver_codes_or_numbers():
    drivers = get_all_drivers()
    codes = [d["code"] for d in drivers]
    numbers = [d["number"] for d in drivers]
    assert len(codes) == len(set(codes)), f"duplicate codes: {[c for c in codes if codes.count(c) > 1]}"
    assert len(numbers) == len(set(numbers)), f"duplicate numbers: {[n for n in numbers if numbers.count(n) > 1]}"


def test_tsunoda_is_not_a_third_racing_bulls_driver():
    # Regression for the exact bug. Racing Bulls 2026 is Lawson + Lindblad.
    racing_bulls = next(t for t in TEAMS_2026 if t["id"] == "racingbulls")
    codes = {d["code"] for d in racing_bulls["drivers"]}
    assert codes == {"LAW", "LIN"}, f"Racing Bulls lineup drifted: {codes}"
    counts = Counter(d["code"] for d in get_all_drivers())
    assert counts["TSU"] == 0, "TSU should not appear on the 2026 grid"


def test_standings_are_consistent_with_the_grid():
    """The standings table must not reference a driver who is not on the grid."""
    from backend.app.data.season_2026 import DRIVER_STANDINGS_2026
    grid_codes = {d["code"] for d in get_all_drivers()}
    standing_codes = {row["driver_code"] for row in DRIVER_STANDINGS_2026}
    unknown = standing_codes - grid_codes
    assert not unknown, f"standings reference drivers not on the grid: {unknown}"
    assert len(DRIVER_STANDINGS_2026) == 22
