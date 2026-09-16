"""
Probability calibration using isotonic/Platt calibration.
Calibrates raw model outputs to better reflect true probabilities.
"""
import numpy as np
from typing import Dict, Any
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ProbabilityCalibrator:
    """
    Calibrates probability predictions using various methods.
    Ensures predicted probabilities reflect true likelihoods.
    """
    
    def __init__(self, method: str = 'isotonic'):
        """
        Initialize calibrator.
        
        Args:
            method: Calibration method ('isotonic', 'platt', 'sigmoid')
        """
        self.method = method
        self.calibrators = {}
        self.is_fitted = False
    
    def fit(
        self,
        raw_probabilities: np.ndarray,
        true_outcomes: np.ndarray,
        target_id: str = 'default',
    ):
        """
        Fit calibration model.
        
        Args:
            raw_probabilities: Raw model probabilities
            true_outcomes: True binary outcomes
            target_id: Target identifier for multiple calibrators
        """
        if self.method == 'isotonic':
            calibrator = IsotonicRegression(out_of_bounds='clip')
        elif self.method == 'platt':
            calibrator = LogisticRegression()
        else:
            calibrator = LogisticRegression()  # Default to Platt
        
        # Fit calibrator
        if self.method == 'isotonic':
            calibrator.fit(raw_probabilities, true_outcomes)
        else:
            # Platt scaling needs reshaped data
            calibrator.fit(raw_probabilities.reshape(-1, 1), true_outcomes)
        
        self.calibrators[target_id] = calibrator
        self.is_fitted = True
    
    def calibrate(
        self,
        raw_probabilities: np.ndarray,
        target_id: str = 'default',
    ) -> np.ndarray:
        """
        Calibrate raw probabilities.
        
        Args:
            raw_probabilities: Raw model probabilities
            target_id: Target identifier
        
        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted or target_id not in self.calibrators:
            return raw_probabilities  # Return as-is if not fitted
        
        calibrator = self.calibrators[target_id]
        
        if self.method == 'isotonic':
            calibrated = calibrator.predict(raw_probabilities)
        else:
            calibrated = calibrator.predict_proba(raw_probabilities.reshape(-1, 1))[:, 1]
        
        # Ensure probabilities are in valid range
        calibrated = np.clip(calibrated, 0.01, 0.99)
        
        return calibrated
    
    def calibrate_dict(
        self,
        raw_probabilities: Dict[str, float],
        target_id: str = 'default',
    ) -> Dict[str, float]:
        """
        Calibrate dictionary of probabilities.
        
        Args:
            raw_probabilities: Dictionary of raw probabilities
            target_id: Target identifier
        
        Returns:
            Dictionary of calibrated probabilities
        """
        if not self.is_fitted or target_id not in self.calibrators:
            return raw_probabilities
        
        # Convert to array, calibrate, convert back
        driver_codes = list(raw_probabilities.keys())
        probs_array = np.array(list(raw_probabilities.values()))
        
        calibrated_array = self.calibrate(probs_array, target_id)
        
        # Renormalize
        calibrated_array = calibrated_array / np.sum(calibrated_array)
        
        # Convert back to dictionary
        calibrated = dict(zip(driver_codes, calibrated_array))
        
        return calibrated
    
    def evaluate_calibration(
        self,
        calibrated_probabilities: np.ndarray,
        true_outcomes: np.ndarray,
    ) -> Dict[str, float]:
        """
        Evaluate calibration quality.
        
        Args:
            calibrated_probabilities: Calibrated probabilities
            true_outcomes: True binary outcomes
        
        Returns:
            Calibration metrics
        """
        # Brier score (lower is better)
        brier_score = np.mean((calibrated_probabilities - true_outcomes) ** 2)
        
        # Expected calibration error
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(calibrated_probabilities, bin_edges) - 1
        
        ece = 0.0
        for bin_idx in range(n_bins):
            mask = bin_indices == bin_idx
            if np.sum(mask) > 0:
                bin_prob = np.mean(calibrated_probabilities[mask])
                bin_outcome = np.mean(true_outcomes[mask])
                bin_weight = np.sum(mask) / len(true_outcomes)
                ece += bin_weight * abs(bin_prob - bin_outcome)
        
        return {
            'brier_score': brier_score,
            'expected_calibration_error': ece,
            'method': self.method,
        }
    
    def save_calibrators(self, filepath: str):
        """Save calibrators to disk."""
        import joblib
        joblib.dump({
            'method': self.method,
            'calibrators': self.calibrators,
            'is_fitted': self.is_fitted,
        }, filepath)
    
    def load_calibrators(self, filepath: str):
        """Load calibrators from disk."""
        import joblib
        data = joblib.load(filepath)
        self.method = data['method']
        self.calibrators = data['calibrators']
        self.is_fitted = data['is_fitted']


class MultiTargetCalibrator:
    """
    Manages calibration for multiple prediction targets.
    """
    
    def __init__(self):
        self.calibrators = {}
        self.targets = ['winner', 'podium', 'points', 'q3']
    
    def get_calibrator(self, target_id: str) -> ProbabilityCalibrator:
        """Get or create calibrator for a target."""
        if target_id not in self.calibrators:
            self.calibrators[target_id] = ProbabilityCalibrator()
        return self.calibrators[target_id]
    
    def calibrate_all(
        self,
        raw_predictions: Dict[str, Dict[str, float]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calibrate predictions for all targets.
        
        Args:
            raw_predictions: Dictionary of target IDs to driver probabilities
        
        Returns:
            Dictionary of calibrated predictions
        """
        calibrated = {}
        
        for target_id, predictions in raw_predictions.items():
            calibrator = self.get_calibrator(target_id)
            if calibrator.is_fitted:
                calibrated[target_id] = calibrator.calibrate_dict(predictions, target_id)
            else:
                calibrated[target_id] = predictions  # Return as-is if not fitted
        
        return calibrated
    
    def train_all(
        self,
        training_data: Dict[str, Any],
    ):
        """
        Train calibrators for all targets.
        
        Args:
            training_data: Training data with raw probabilities and true outcomes
        """
        for target_id in self.targets:
            if target_id in training_data:
                calibrator = self.get_calibrator(target_id)
                calibrator.fit(
                    training_data[target_id]['raw_probabilities'],
                    training_data[target_id]['true_outcomes'],
                    target_id,
                )


# Global calibrator instances
probability_calibrator = ProbabilityCalibrator()
multi_target_calibrator = MultiTargetCalibrator()
