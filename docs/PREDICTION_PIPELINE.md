# Prediction Pipeline

```
Race request
  → Resolve race/session (calendar_2026, validated race_id)
  → Resolve authoritative data (ProviderRegistry federated, provenance)
  → Construct PredictionSnapshot {race_id, session, timestamp, data_cutoff, grid, weather(rich), lineup, model_version, feature_version, simulation_count, random_seed, config_hash}
  → Validate snapshot
  → Feature engineering (FeatureEngineer → DataFrame)
  → ML inference (ModelZoo, ensemble, OOF weights)
  → Statistical + pace models
  → Monte Carlo (10k sims, dnf/tyre/weather/SC/strategy aware)
  → Calibration (isotonic/Platt) → enforce sum
  → Scenario simulation (baseline vs scenario diff)
  → Confidence & data-quality {model certainty, data completeness 0-1, volatility, weather uncertainty}
  → Explainability (feature-grounded reasons per driver)
  → Cache (key = hash(race+session+snapshot+model+feature+weather+grid+config), TTL 3600 but invalidates on data/model version change)
  → API response {prediction_id, race, session, snapshot, model, probabilities, dnf, expected_finish, explanations, simulation, provenance}
```

Observable: `X-Request-ID`, `X-Response-Time`, `X-Prediction-Latency`, `/metrics`, provider latency per provenance.
