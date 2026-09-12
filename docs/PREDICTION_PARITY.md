# Prediction Parity

Invariant: same inputs → same engine → same outputs (within tolerance).

## Engine Pipeline (preserved)

```
POST /api/v1/predictions (or /dashboard/api/predict-session)
  → PredictionService.generate → generate_prediction
    → resolve race, drivers, session, weather, feature_weights, simulation_count, AI
    → race: GridModel.get_grid_positions → _strength_based_grid (strength+noise) + MonteCarloSimulator.simulate_race → AI adjustment → chaos smoothing → calibrate → confidence_intervals → drift → save (non-fatal)
    → qualifying: GridModel + strength/wet/consistency/pressure (Q1 0.9/Q2 1.0/Q3 1.1)
    → practice: strength/wet/consistency + session multiplier (FP1 0.95/FP2 1.0/FP3 1.05)
```

## Golden Fixtures

`scripts/generate_golden_fixtures.py` writes deterministic fixtures to `tests/fixtures/golden/*.json` with:

- race_id, session_type, weather, grid_positions, feature_weights, simulation_count, AI disabled, seed (for Monte Carlo)
- captured output: winner/podium/points predictions, confidence, grid, metadata, source

For stochastic Monte Carlo, fixtures use fixed `seed` and `simulation_count`; parity checks use `abs(old-new) < 1e-6` for deterministic or distribution-level seeded equality.

## Validation

- `tests/test_prediction_parity.py`: compare legacy direct `generate_prediction` vs v1 API response (via test client) for same payload
- Compare: prediction target IDs, driver ordering, probabilities/percentages, confidence, grid, metadata, source, AI status, probability sums (≈1.0 for winner), latency not compared
- DB failure must not change result (engine catches)

## Run

```
python scripts/generate_golden_fixtures.py
pytest tests/test_prediction_parity.py -v
pytest tests/test_api_v1.py -v
```
