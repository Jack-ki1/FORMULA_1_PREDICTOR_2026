"""
Ensemble predictor - blends model zoo outputs.
Combines predictions from multiple models into a single calibrated output.
"""
import numpy as np
from typing import Dict, List, Any, Optional
from backend.app.engine.ml_models import model_zoo


class EnsemblePredictor:
    """
    Ensemble predictor that combines outputs from multiple models.
    Uses weighted averaging or meta-learning for final predictions.
    """
    
    def __init__(self):
        self.model_zoo = model_zoo
        self.weights = {
            'gradient_boosting': 0.5,
            'random_forest': 0.3,
            'logistic_regression': 0.2,
        }
        self.meta_learner = None
    
    def set_weights(self, weights: Dict[str, float]):
        """Set ensemble weights for models."""
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in weights.items()}
    
    def ensemble_predictions(
        self,
        predictions: Dict[str, np.ndarray],
        method: str = 'weighted_average',
    ) -> np.ndarray:
        """
        Ensemble predictions from multiple models.
        
        Args:
            predictions: Dictionary of model predictions
            method: Ensemble method ('weighted_average', 'voting', 'meta_learner')
        
        Returns:
            Ensembled predictions
        """
        if not predictions:
            return np.array([])
        
        if method == 'weighted_average':
            return self._weighted_average(predictions)
        elif method == 'voting':
            return self._voting(predictions)
        elif method == 'meta_learner':
            return self._meta_learner_predictions(predictions)
        else:
            return self._weighted_average(predictions)
    
    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Weighted average of predictions."""
        ensemble = np.zeros_like(list(predictions.values())[0])
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 0.0)
            ensemble += weight * pred
        
        return ensemble
    
    def _voting(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Majority voting for classification."""
        # Convert probabilities to class predictions
        class_predictions = {}
        for model_name, pred in predictions.items():
            class_predictions[model_name] = np.argmax(pred, axis=1)
        
        # Majority vote
        ensemble = []
        for i in range(len(class_predictions[list(predictions.keys())[0]])):
            votes = [class_predictions[model][i] for model in predictions.keys()]
            ensemble.append(max(set(votes), key=votes.count))
        
        return np.array(ensemble)
    
    def _meta_learner_predictions(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Use meta-learner if available, otherwise fall back to weighted average."""
        if self.meta_learner is not None:
            # Stack predictions for meta-learner
            stacked = np.column_stack(predictions.values())
            return self.meta_learner.predict_proba(stacked)
        else:
            return self._weighted_average(predictions)
    
    def train_meta_learner(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        base_predictions: Dict[str, np.ndarray],
    ):
        """
        Train a meta-learner on base model predictions.
        
        Args:
            X_train: Original training features
            y_train: Training labels
            base_predictions: Predictions from base models
        """
        from sklearn.linear_model import LogisticRegression
        
        # Stack base predictions
        stacked_train = np.column_stack(base_predictions.values())
        
        # Train meta-learner
        self.meta_learner = LogisticRegression(random_state=42)
        self.meta_learner.fit(stacked_train, y_train)
    
    def get_ensemble_weights(self) -> Dict[str, float]:
        """Get current ensemble weights."""
        return self.weights.copy()
    
    def optimize_weights(
        self,
        validation_predictions: Dict[str, np.ndarray],
        validation_labels: np.ndarray,
    ) -> Dict[str, float]:
        """
        Optimize ensemble weights based on validation performance.
        
        Args:
            validation_predictions: Predictions on validation set
            validation_labels: True labels
        
        Returns:
            Optimized weights
        """
        from scipy.optimize import minimize
        
        def objective(weights):
            # Normalize weights
            weights = weights / np.sum(weights)
            
            # Calculate ensemble predictions
            ensemble = self._weighted_average_with_weights(
                validation_predictions,
                weights,
            )
            
            # Calculate accuracy (negative for minimization)
            accuracy = np.mean(np.argmax(ensemble, axis=1) == validation_labels)
            return -accuracy
        
        # Initial weights
        initial_weights = np.array(list(self.weights.values()))
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            bounds=[(0.01, 1.0)] * len(initial_weights),
            method='L-BFGS-B',
        )
        
        # Update weights
        optimized_weights = result.x / np.sum(result.x)
        self.weights = dict(zip(self.weights.keys(), optimized_weights))
        
        return self.weights
    
    def _weighted_average_with_weights(
        self,
        predictions: Dict[str, np.ndarray],
        weights: np.ndarray,
    ) -> np.ndarray:
        """Weighted average with custom weights."""
        ensemble = np.zeros_like(list(predictions.values())[0])
        
        for i, (model_name, pred) in enumerate(predictions.items()):
            ensemble += weights[i] * pred
        
        return ensemble
    
    def get_model_contributions(
        self,
        predictions: Dict[str, np.ndarray],
    ) -> Dict[str, float]:
        """
        Calculate contribution of each model to ensemble.
        
        Args:
            predictions: Model predictions
        
        Returns:
            Model contributions
        """
        ensemble = self.ensemble_predictions(predictions)
        
        contributions = {}
        for model_name, pred in predictions.items():
            # Calculate correlation with ensemble
            if len(pred.shape) > 1:
                pred_class = np.argmax(pred, axis=1)
                ensemble_class = np.argmax(ensemble, axis=1)
            else:
                pred_class = pred
                ensemble_class = ensemble
            
            correlation = np.corrcoef(pred_class, ensemble_class)[0, 1]
            contributions[model_name] = correlation if not np.isnan(correlation) else 0.0
        
        return contributions


# Global ensemble predictor instance
ensemble_predictor = EnsemblePredictor()
