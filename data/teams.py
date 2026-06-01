"""
Canonical Team Registry for F1 Predictor 2026.

Provides a single source of truth for team identifiers across the codebase.
Prevents mismatches between driver_data.py, feature_engineering.py, and season_2026.py.

Usage:
    from data.teams import normalize_team
    
    # Normalize various team name formats to canonical ID
    team_id = normalize_team("racing_bulls")  # Returns "rb"
    team_id = normalize_team("alphatauri")    # Returns "rb"
    team_id = normalize_team("rb")            # Returns "rb"
"""

CANONICAL_TEAM_IDS = {
    "mercedes",
    "red_bull",
    "ferrari",
    "mclaren",
    "williams",
    "alpine",
    "haas",
    "rb",              # Racing Bulls (formerly AlphaTauri)
    "audi",
    "aston_martin",
    "cadillac",
    "kick_sauber",
}

TEAM_ALIASES = {
    "racing_bulls": "rb",
    "alphatauri": "rb",
    "alpha_tauri": "rb",
    "toro_rosso": "rb",
    "minardi": "rb",
}


def normalize_team(team_id: str) -> str:
    """
    Normalize team identifier to canonical form.
    
    Args:
        team_id: Team identifier (may be alias or canonical)
    
    Returns:
        Canonical team ID
    
    Raises:
        ValueError: If team_id is not recognized
    """
    normalized = TEAM_ALIASES.get(team_id.lower(), team_id.lower())
    if normalized not in CANONICAL_TEAM_IDS:
        raise ValueError(f"Unknown team: {team_id!r}. Valid teams: {sorted(CANONICAL_TEAM_IDS)}")
    return normalized


def get_all_teams() -> list:
    """Return sorted list of all canonical team IDs."""
    return sorted(CANONICAL_TEAM_IDS)


if __name__ == "__main__":
    print("F1 Predictor 2026 - Team Registry")
    print("=" * 50)
    print("\nCanonical Teams:")
    for team in get_all_teams():
        print(f"  - {team}")
    
    print("\nTeam Aliases:")
    for alias, canonical in sorted(TEAM_ALIASES.items()):
        print(f"  {alias:20s} → {canonical}")
    
    print("\nTest normalization:")
    test_cases = ["racing_bulls", "alphatauri", "rb", "mercedes", "invalid_team"]
    for tc in test_cases:
        try:
            result = normalize_team(tc)
            print(f"  {tc:20s} → {result}")
        except ValueError as e:
            print(f"  {tc:20s} → ERROR: {e}")
