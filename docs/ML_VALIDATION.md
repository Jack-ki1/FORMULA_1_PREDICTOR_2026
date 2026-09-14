# ML Validation — Temporal, No Leakage

> This is authoritative for model evaluation. Any model claiming production status must satisfy this.

## Principle

A system trained on future race data must NEVER evaluate itself on earlier races.

Random `KFold` / `StratifiedKFold` is **forbidden** for the principal F1 models.

## Splits

### Season Holdout (primary)

```
Train: 2018-2022 → Validate: 2023
Train: 2018-2023 → Validate: 2024
Train: 2018-2024 → Validate: 2025
Production training: all eligible historical data (≤ training_cutoff)
```

### Rolling-Origin (deep evaluation)

```
Fold 1: train 2018-2021 validate 2022
Fold 2: train 2018-2022 validate 2023
Fold 3: train 2018-2023 validate 2024
```

### Group Holdouts

- **Race-weekend group holdout:** entire weekend (FP1→Race) held out together.
- **Constructor holdout:** one constructor's rows held out to test generalization to upgrades.
- **Driver holdout:** one driver's rows held out to test driver generalization.
- **Circuit holdout:** one circuit held out to test circuit suitability generalization.

## Leakage Checks

- `training_cutoff` stored in every model artifact metadata; validator asserts `max(row.season) ≤ training_cutoff_year`.
- Feature builder asserts no future `recent_form`, `circuit_history`, or `teammate_delta` from after cutoff.
- `builder.train_test_split_temporal` enforces `season ≤ train_until`.

## Metrics

Per target (`win`, `podium`, `points`, `dnf`, `expected_finish`, `qual_pos`):

```
Brier score, log loss, ECE, reliability curve,
top1_accuracy, podium_accuracy, MAE (expected finish), AUC
```

Ensemble weights are optimized on **out-of-fold (OOF)** base-model predictions, never on training data.

## Promotion

```
new race → append → validate → candidate training (OOF) → backtest → calibration → compare to champion
→ promote only if Brier/logloss/accuracy better on holdout + calibration improves
```

Uses champion/challenger pattern.

## Artifacts

Every production model stores:

```json
{"model_id":"win-probability-v12","version":"12","trained_at":"...","training_cutoff":"2024-12-31","feature_version":"feature-v8","dataset_version":"dataset-v14","algorithm":"lightgbm","metrics":{"log_loss":0.31,"brier":0.12}}
```
