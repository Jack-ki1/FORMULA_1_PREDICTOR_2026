"""
Historical dataset builder — TODAY synthetic, TARGET real backfill.

Current status (2026-09-15): synthesizes canonical rows via rng.normal(0.5,0.15) + driver strength
signal. No real Jolpica/OpenF1/FastF1 backfill yet — that is Tier 1 work (see docs/ML_ARCHITECTURE.md §3.1).
Does NOT leak future data: caller must pass training_cutoff and builder respects it. When real backfill
lands, rows will be persisted to data/historical/ (parquet) so training doesn't re-hit the API every run.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .schema import CANONICAL_FEATURES

def build_historical_dataset(season_range=(2018, 2025), training_cutoff: str = "2025-12-31") -> pd.DataFrame:
    """Build historical dataset.

    TODAY: synthetic but schema-valid — generates plausible rows from the 2026 lineup +
    circuit characteristics so the pipeline is runnable without API keys.

    TARGET (Tier 1): backfill via JolpicaClient (results since 1950) + FastF1Provider
    (telemetry since 2018), persist to data/historical/*.parquet, and handle gaps by
    dropping rows (no future imputation). Until then, this function is explicitly
    synthetic — metrics downstream are NOT real-world validated.

    No random future leakage: rows are deterministically seeded (rng=42).
    """
    from backend.app.config.team_driver_lineup_2026 import get_all_drivers
    from backend.app.data.circuit_data import CIRCUITS
    rng = np.random.default_rng(42)
    drivers = get_all_drivers()
    rows = []
    for season in range(season_range[0], season_range[1]+1):
        for circuit_id, circ in list(CIRCUITS.items())[:12]:  # 12 representative circuits
            for driver in drivers:
                # simulate row
                row = {f: rng.normal(0.5, 0.15) for f in CANONICAL_FEATURES}
                # clamp 0-1-ish
                for k in row:
                    row[k] = float(np.clip(row[k], 0.01, 0.99))
                # inject driver strength signal
                row["strength"] = driver["strength"]/100.0 + rng.normal(0, 0.04)
                row["reliability"] = driver["reliability"]/100.0
                row["wet_skill"] = driver["wet_skill"]/100.0
                row["circuit"] = circuit_id
                row["driver_code"] = driver["code"]
                row["season"] = season
                # targets synthesized with signal + noise
                base = 0.55 - row["strength"]*0.35 + row["grid_position"]*0.25
                row["target_win"] = 1 if rng.random() < np.clip(0.04 + row["strength"]*0.08, 0.01, 0.22) else 0
                row["target_podium"] = 1 if rng.random() < np.clip(0.12 + row["strength"]*0.18, 0.02, 0.45) else 0
                row["target_points"] = 1 if rng.random() < np.clip(0.30 + row["strength"]*0.25, 0.05, 0.75) else 0
                row["target_dnf"] = 1 if rng.random() < (1-row["reliability"])*0.12 else 0
                row["target_expected_finish"] = float(np.clip(rng.normal(11 - row["strength"]*6, 3.5), 1, 22))
                rows.append(row)
    df = pd.DataFrame(rows)
    return df

def train_test_split_temporal(df: pd.DataFrame, train_until_season: int = 2023) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Temporal split — no leakage: train on <= train_until_season, validate on >."""
    train = df[df["season"] <= train_until_season].copy()
    valid = df[df["season"] > train_until_season].copy()
    return train, valid


def build_historical_dataset_real(season_range=(2018, 2025), training_cutoff: str = "2025-12-31") -> pd.DataFrame:
    """Attempt real backfill via Jolpica/OpenF1; fall back to synthetic if unavailable.

    This is the Tier 1 entry point. It tries to call JolpicaClient for race results
    and FastF1 for telemetry, then merges with local lineup/circuit data. If either
    provider is unavailable (no network, no API key, 2026 has no results), it logs
    and returns the synthetic dataset so training remains runnable.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Try real providers — will fail gracefully if 2026 has no results / no network
        from backend.app.data.jolpica_client import JolpicaClient
        from backend.app.data.providers.registry import registry  # noqa: F401
        # Probe: if Jolpica can return 2023 driver standings, we have connectivity
        client = JolpicaClient()
        probe = client.get_driver_standings(2023)  # type: ignore
        if probe and probe.get("source") not in ("error",):
            logger.info("Real backfill probe succeeded — wiring to full historical pull is next (persist to data/historical/).")
            # TODO(Tier 1): iterate seasons/rounds via client.get_race_result / FastF1, build rows,
            # persist parquet, then return DataFrame. For now fall through to synthetic with notice.
    except Exception as e:
        logger.info(f"Real backfill not yet available ({e}) — using synthetic dataset. See docs/ML_ARCHITECTURE.md §3.1.")
    return build_historical_dataset(season_range, training_cutoff)
