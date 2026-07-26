"""
F1 Predictor Engine — SOTA Prediction Modules.

Modules:
  - predictor.py:             Main prediction orchestrator (PredictionRequest, predict)
  - probability_model.py:     Monte Carlo simulation + SOTA ensemble blending
  - feature_engineering.py:   Driver feature computation (composite scores, ELO, form)
  - ml_models.py:             XGBoost LambdaMART + Plackett-Luce ranking [SOTA]
  - ensemble_predictor.py:    Meta-Blender Ensemble combining MC + ML + PL [SOTA]
  - hf_sentiment.py:          HuggingFace NLP for F1 news sentiment analysis [SOTA]
  - pit_strategy.py:          Advanced pit strategy & tire degradation simulation [SOTA]
  - benchmark_suite.py:       Comprehensive model evaluation and benchmarking [SOTA]
  - vectorized_simulation.py: NumPy-accelerated Monte Carlo
  - multi_dimensional_elo.py: Glicko-2 ELO rating system
  - calibration.py:           Platt scaling and calibration utilities
  - prediction_tracker.py:    Database-backed prediction accuracy tracking
"""

from engine import (
    predictor,
    probability_model,
    feature_engineering,
    ml_models,
    ensemble_predictor,
    hf_sentiment,
    pit_strategy,
    benchmark_suite,
    vectorized_simulation,
    multi_dimensional_elo,
    calibration,
    prediction_tracker,
)

__all__ = [
    "predictor",
    "probability_model",
    "feature_engineering",
    "ml_models",
    "ensemble_predictor",
    "hf_sentiment",
    "pit_strategy",
    "benchmark_suite",
    "vectorized_simulation",
    "multi_dimensional_elo",
    "calibration",
    "prediction_tracker",
]
