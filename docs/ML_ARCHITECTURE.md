# ML Architecture

```
Historical dataset (2018-2025, builder respects training_cutoff)
  → Feature engineering (feature-v8, 30+ features: driver/constructor/circuit/session + interactions)
  → Model zoo (GradientBoosting, RandomForest, LogisticRegression; XGBoost/LightGBM deps installed)
    → train per target (win/podium/points/dnf/expected_finish/qual_pos/pace)
  → OOF ensemble (optimize_weights on validation via scipy L-BFGS-B, never on train)
  → Calibration (IsotonicRegression / Platt; Brier/ECE/reliability)
  → Registry (training/model_registry/registry.json, champion/challenger)
  → Production inference (orchestrator: ML 45% + MC 55% → calibrated → MC simulation)
```

- ML is **not** decorative: `predictor.py` calls `_try_ml_predictions` → `ModelZoo.predict_all` → `_blend`; if no artifact, returns `statistical_fallback` and marks `prediction_source`.
- Training: `python -m training.pipelines.train` (temporal split 2018-2023 train / 2024+ valid).
- Validation: `docs/ML_VALIDATION.md` (season holdout, rolling-origin, group holdouts); random CV forbidden.
- Calibration required before display; Brier/logloss/ECE measured.
- ONNX: optional export `scripts/export_onnx.py` after validation; input schema from `feature_engineer.get_feature_names()`.

