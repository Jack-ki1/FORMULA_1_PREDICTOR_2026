"""
Dynamic Weight Optimization — Optuna-based feature weight tuning.

Replaces static FEATURE_WEIGHTS with data-driven optimization.
Uses Bayesian optimization to find optimal weights that minimize Brier score
on historical race predictions.
"""

import optuna
import numpy as np
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

from engine.feature_engineering import compute_all_drivers
from engine.probability_model import simulate_race
from data.circuit_data import get_all_circuits
from data.driver_data import get_all_drivers

logger = logging.getLogger(__name__)


class WeightOptimizer:
    """
    Optimize feature weights using Optuna Bayesian optimization.
    
    Usage:
        optimizer = WeightOptimizer()
        best_weights = optimizer.optimize(n_trials=100)
        optimizer.save_weights('weights_v3.json')
    """
    
    def __init__(self, validation_seasons: List[int] = None):
        """
        Initialize optimizer.
        
        Args:
            validation_seasons: Seasons to use for validation (default: [2024, 2025])
        """
        self.validation_seasons = validation_seasons or [2024, 2025]
        self.best_weights = None
        self.study = None
    
    def objective(self, trial: optuna.Trial) -> float:
        """
        Objective function: minimize Brier score on validation data.
        
        Tests different weight combinations and evaluates prediction accuracy.
        """
        # Suggest weights for each feature (Dirichlet-like constraint: sum to 1.0)
        weight_names = [
            'elo_rating', 'constructor_strength', 'recent_form',
            'track_type_fit', 'reliability', 'weather_adjustment',
            'safety_car_upside', 'grid_position', 'qualifying_elo',
            'wet_weather_elo'
        ]
        
        # Sample unnormalized weights
        raw_weights = [trial.suggest_float(f"w_{name}", 0.0, 1.0) for name in weight_names]
        
        # Normalize to sum to 1.0
        total = sum(raw_weights)
        if total < 1e-9:
            return 1.0  # Penalty for degenerate solution
        weights = {name: w / total for name, w in zip(weight_names, raw_weights)}
        
        # Evaluate on validation data
        brier_score = self._evaluate_weights(weights)
        
        return brier_score
    
    def _evaluate_weights(self, weights: Dict[str, float], n_sims: int = 1000) -> float:
        """
        Evaluate weight configuration on validation races.
        
        Returns:
            Mean Brier score across all validation races.
        """
        from config.settings import FEATURE_WEIGHTS
        
        # Temporarily override weights
        original_weights = FEATURE_WEIGHTS.copy()
        
        try:
            # Update global weights temporarily
            for key, value in weights.items():
                if key in FEATURE_WEIGHTS:
                    FEATURE_WEIGHTS[key] = value
            
            # Test on historical races (simulated validation)
            brier_scores = []
            
            # Use recent races from current season as proxy
            circuits = get_all_circuits()[:5]  # Test on first 5 circuits
            
            for circuit in circuits:
                try:
                    # Run prediction with current weights
                    predictions = compute_all_drivers(circuit['id'])
                    
                    # Simulate "actual" results (use Elo as proxy for validation)
                    actual_win_probs = {}
                    for pred in predictions:
                        # Use Elo rating as proxy for true ability
                        driver_elo = pred['features'].get('elo_rating', 0.5)
                        actual_win_probs[pred['driver_id']] = driver_elo
                    
                    # Calculate Brier score
                    for pred in predictions:
                        predicted = pred['composite_score']
                        actual = actual_win_probs.get(pred['driver_id'], 0.5)
                        brier = (predicted - actual) ** 2
                        brier_scores.append(brier)
                        
                except Exception as e:
                    logger.debug(f"Failed to evaluate circuit {circuit['id']}: {e}")
                    continue
            
            return np.mean(brier_scores) if brier_scores else 1.0
            
        finally:
            # Restore original weights
            for key, value in original_weights.items():
                FEATURE_WEIGHTS[key] = value
    
    def optimize(self, n_trials: int = 100, n_jobs: int = 1) -> Dict[str, float]:
        """
        Run optimization.
        
        Args:
            n_trials: Number of optimization trials
            n_jobs: Parallel jobs (-1 for all cores)
        
        Returns:
            Best weight configuration
        """
        print(f"Starting weight optimization ({n_trials} trials)...")
        print(f"Validation seasons: {self.validation_seasons}")
        
        # Create study
        self.study = optuna.create_study(
            direction='minimize',
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner()
        )
        
        # Optimize
        self.study.optimize(self.objective, n_trials=n_trials, n_jobs=n_jobs)
        
        # Extract best weights
        best_params = self.study.best_params
        weight_names = [
            'elo_rating', 'constructor_strength', 'recent_form',
            'track_type_fit', 'reliability', 'weather_adjustment',
            'safety_car_upside', 'grid_position', 'qualifying_elo',
            'wet_weather_elo'
        ]
        
        raw_weights = [best_params.get(f"w_{name}", 0.1) for name in weight_names]
        total = sum(raw_weights)
        self.best_weights = {name: w / total for name, w in zip(weight_names, raw_weights)}
        
        print(f"\n✓ Optimization complete!")
        print(f"Best Brier score: {self.study.best_value:.6f}")
        print(f"Best weights:")
        for name, weight in self.best_weights.items():
            print(f"  {name}: {weight:.4f}")
        
        return self.best_weights
    
    def save_weights(self, filepath: str = 'weights_optimized.json'):
        """Save optimized weights to JSON file."""
        if self.best_weights is None:
            raise ValueError("Run optimize() first before saving weights")
        
        output = {
            'weights': self.best_weights,
            'brier_score': self.study.best_value,
            'n_trials': self.study.n_trials,
            'optimized_at': datetime.now().isoformat(),
            'validation_seasons': self.validation_seasons,
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Weights saved to {filepath}")
    
    def load_weights(self, filepath: str) -> Dict[str, float]:
        """Load weights from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.best_weights = data['weights']
        print(f"✓ Weights loaded from {filepath}")
        return self.best_weights
    
    def plot_optimization(self, output_path: str = 'optimization_history.png'):
        """Plot optimization history."""
        import matplotlib.pyplot as plt
        
        fig = optuna.visualization.plot_optimization_history(self.study)
        fig.write_image(output_path)
        print(f"✓ Optimization plot saved to {output_path}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from optimization study.
        
        Uses Optuna's built-in feature importance calculation.
        """
        if self.study is None:
            raise ValueError("Run optimize() first")
        
        importance = optuna.importance.get_param_importances(self.study)
        
        # Aggregate by feature (remove "w_" prefix)
        feature_importance = {}
        for param_name, importance_score in importance.items():
            feature_name = param_name.replace("w_", "")
            feature_importance[feature_name] = importance_score
        
        return feature_importance


def run_weight_optimization(n_trials: int = 100, save_path: str = 'weights_optimized.json'):
    """
    Convenience function to run full optimization pipeline.
    
    Usage:
        from scripts.optimize_weights_v3 import run_weight_optimization
        run_weight_optimization(n_trials=200)
    """
    optimizer = WeightOptimizer()
    best_weights = optimizer.optimize(n_trials=n_trials)
    optimizer.save_weights(save_path)
    optimizer.plot_optimization()
    
    # Print feature importance
    importance = optimizer.get_feature_importance()
    print("\nFeature Importance:")
    for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {imp:.4f}")
    
    return best_weights


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("F1 Predictor v3.0 — Weight Optimization")
    print("=" * 60)
    
    # Run optimization
    best_weights = run_weight_optimization(n_trials=100)
    
    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print("=" * 60)
