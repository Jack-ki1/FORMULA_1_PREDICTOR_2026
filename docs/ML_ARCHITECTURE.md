# ML Architecture — status: heuristic production, ML not yet on real data

> **Ground truth (2026-09-15):** Heuristic Monte Carlo + hand-tuned `strength` ratings are the production path.
> ML zoo / ensemble / calibration code exists and is legitimately built (`calibration.py` Isotonic, `ensemble_predictor.py` L-BFGS-B) but `training/datasets/builder.py` currently synthesizes labels via `rng.normal(0.5, 0.15)` — no real Jolpica/FastF1 backfill yet. Fresh clone has no `cache/model_cache/*.pkl` → `is_trained=False` → `statistical_fallback`. Honest metrics: **not yet validated on real data**.

```
Historical dataset (2018-2025, builder respects training_cutoff) — TODAY: synthetic; TARGET: Jolpica+FastF1 backfill
  → Feature engineering (feature-v8, 30+ features: driver/constructor/circuit/session + interactions)
  → Model zoo (GradientBoosting, RandomForest, LogisticRegression; XGBoost/LightGBM deps installed)
    → train per target (win/podium/points/dnf/expected_finish/qual_pos/pace)
  → OOF ensemble (optimize_weights on validation via scipy L-BFGS-B, never on train)
  → Calibration (IsotonicRegression / Platt; Brier/ECE/reliability) — not yet measured on real holdout
  → Registry (training/model_registry/registry.json, champion/challenger) — metrics synthetic until 3.1 lands
  → Production inference (orchestrator: ML 45% + MC 55% → calibrated → MC simulation) — currently always fallback
```

- ML is wired: `predictor.py` calls `_try_ml_predictions` → `ModelZoo.predict_all` → `_blend`; if no artifact, returns `statistical_fallback` and marks `prediction_source`. But wiring ≠ validation.
- Training: `python -m training.pipelines.train` (temporal split 2018-2023 train / 2024+ valid) — today synthetic, target §3.1 real backfill.
- Validation: `docs/ML_VALIDATION.md` (season holdout, rolling-origin, group holdouts); random CV forbidden. No model may claim production until it beats a naive baseline on a temporal holdout.
- Calibration required before display; Brier/logloss/ECE must be computed from real `y_valid`, not hardcoded.
- ONNX: **not ready** — `scripts/export_onnx.py` is a stub; no `onnx/onnxruntime` runtime import. Do not claim ONNX-ready until export + inference round-trip is tested.

