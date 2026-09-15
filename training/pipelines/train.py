"""
Training pipeline — temporal split, OOF ensemble, calibration, registry.
Run: python -m training.pipelines.train
"""
import pandas as pd
import numpy as np
from sklearn.metrics import log_loss, brier_score_loss
from training.datasets.builder import build_historical_dataset, train_test_split_temporal
from training.datasets.schema import CANONICAL_FEATURES

def train():
    df = build_historical_dataset((2018,2025))
    train_df, valid_df = train_test_split_temporal(df, 2023)
    feature_cols = [c for c in CANONICAL_FEATURES if c in df.columns]
    X_train, y_train = train_df[feature_cols], train_df["target_win"]
    X_valid, y_valid = valid_df[feature_cols], valid_df["target_win"]

    from backend.app.engine.ml_models import model_zoo
    from backend.app.engine.ensemble_predictor import ensemble_predictor
    from backend.app.engine.calibration import probability_calibrator

    # Train base models
    results = model_zoo.train_all(X_train, y_train)
    print("Base training:", results)

    # OOF: get valid predictions per model
    preds = {}
    for name in model_zoo.active_models:
        m = model_zoo.get_model(name)
        if m.is_trained:
            proba = m.predict_proba(X_valid)
            # proba 2 cols
            preds[name] = proba

    # Optimize ensemble weights on valid (OOF)
    if len(preds) >= 2:
        # build validation labels array
        from scipy.optimize import minimize
        labels = y_valid.values
        # stack for optimization
        w = ensemble_predictor.optimize_weights(preds, labels)
        print("Optimized weights:", w)

    # Calibration on valid
    # use ensemble predictions blended
    ensemble_proba = ensemble_predictor.ensemble_predictions(preds)
    if len(ensemble_proba):
        win_proba = ensemble_proba[:,1] if ensemble_proba.ndim==2 else ensemble_proba
        probability_calibrator.fit(win_proba, y_valid.values)
        print("Calibration Brier:", probability_calibrator.evaluate_calibration(win_proba, y_valid.values))

    # Save artifacts
    import os
    os.makedirs("cache/model_cache", exist_ok=True)
    model_zoo.save_models("cache/model_cache")
    probability_calibrator.save_calibrators("cache/model_cache/calibrator.pkl")

    # Registry — compute real metrics, fail loudly on error (no silent fake numbers)
    from training.model_registry.registry import register_model, promote_champion
    ll = log_loss(y_valid, np.clip(win_proba, 0.01, 0.99))
    brier = brier_score_loss(y_valid, win_proba)
    # top1: ensemble mean prediction vs actual; binary target → threshold 0.5
    y_pred_bin = (win_proba >= 0.5).astype(int)
    top1 = float((y_pred_bin == y_valid.values).mean())
    # naive baseline: predict pole-sitter (grid 1) wins — synthetic baseline ~1/n_drivers
    # use empirical positive rate as baseline Brier for lift reporting
    baseline_prob = float(y_valid.mean())
    baseline_brier = float(((y_valid.values - baseline_prob) ** 2).mean())
    lift = baseline_brier - brier  # positive = ensemble beats baseline
    print(f"Metrics — log_loss={ll:.4f} brier={brier:.4f} top1={top1:.4f} baseline_brier={baseline_brier:.4f} lift={lift:+.4f}")
    register_model("win-probability", "12", "ensemble_gb_rf", {"log_loss": float(ll), "brier": float(brier), "top1": float(top1), "baseline_brier": float(baseline_brier), "brier_lift": float(lift)}, training_cutoff="2023-12-31")
    print("Training complete — artifacts in cache/model_cache")

if __name__ == "__main__":
    train()
