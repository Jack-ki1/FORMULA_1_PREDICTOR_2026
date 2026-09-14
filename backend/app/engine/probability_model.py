"""
Probability model - session/target-aware probability shaping.
Applies chaos level, target exponent, and calibration to raw model outputs.
"""
import logging
import json
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional, Any
from backend.app.config.constants import TARGETS
from backend.app.config.feature_weights import feature_weights as fw_module
from backend.app.data.session_context import build_session_context
from backend.app.data.validation import validate_probability_data
from backend.app.data.fallback import FallbackStrategy
from backend.app.models.prediction import Prediction, PredictionMetadata
from backend.app.database.client import DatabaseClient
from backend.app.cache.redis import get_cache

logger = logging.getLogger(__name__)


class ProbabilityModel:
    """
    Shapes raw model outputs into calibrated probabilities.
    Handles chaos level, target-specific exponents, and probability calibration.
    """
    
    def __init__(self):
        self.targets = TARGETS
        self.calibration_params = {}
    
    def shape_probabilities(
        self,
        raw_scores: Dict[str, float],
        target_id: str,
        chaos_level: float = 50,
        feature_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Shape raw scores into calibrated probabilities.
        
        Args:
            raw_scores: Dictionary of driver codes to raw scores
            target_id: Target identifier (winner, podium, points, q3)
            chaos_level: Chaos level (0-100) for uncertainty
            feature_weights: Feature weight overrides
        
        Returns:
            Dictionary of driver codes to calibrated probabilities
        """
        target = self.targets.get(target_id.lower())
        if not target:
            raise ValueError(f"Unknown target: {target_id}")
        
        weights = feature_weights or fw_module.get_defaults()
        chaos_factor = fw_module.get_chaos_factor(chaos_level)
        
        # Apply target-specific exponent with chaos adjustment
        eff_exp = target['exp'] * chaos_factor
        
        # Apply exponent transformation to scores
        shaped_scores = {}
        for driver_code, score in raw_scores.items():
            shaped_scores[driver_code] = np.power(max(0.01, score), eff_exp)
        
        # Normalize to sum to target sum (e.g., 1 for winner, 3 for podium)
        total_score = sum(shaped_scores.values())
        if total_score == 0:
            # Equal probabilities if all scores are zero
            num_drivers = len(raw_scores)
            equal_prob = target['sum'] / num_drivers
            logger.debug(f"All scores zero, using equal probabilities: {equal_prob} for {num_drivers} drivers")
            return {code: equal_prob for code in raw_scores.keys()}
        
        probabilities = {}
        for driver_code, shaped_score in shaped_scores.items():
            raw_prob = (shaped_score / total_score) * target['sum']
            # Membership targets (podium/points/Q3) are probabilities per
            # driver and may legitimately sum above one.  Capping each value
            # at .97 broke their required target total on small inputs.
            prob = min(0.97, raw_prob) if target['sum'] == 1 else min(1.0, raw_prob)
            logger.debug(f"Applying probability cap: original={raw_prob:.4f}, capped={prob:.4f}, target_sum={target['sum']}")
            probabilities[driver_code] = prob

        # Preserve the mathematical target total after membership caps.  This
        # matters for a small test field as well as for any reduced entry list.
        if target['sum'] > 1:
            remaining = target['sum'] - sum(probabilities.values())
            while remaining > 1e-10:
                eligible = [code for code, value in probabilities.items() if value < 1.0 - 1e-10]
                if not eligible:
                    break
                allocation = remaining / len(eligible)
                added = 0.0
                for code in eligible:
                    increment = min(allocation, 1.0 - probabilities[code])
                    probabilities[code] += increment
                    added += increment
                if added <= 1e-12:
                    logger.debug("Added value too small to continue distribution")
                    break
                remaining -= added
        
        return probabilities
    
    def apply_dnf_risk(
        self,
        probabilities: Dict[str, float],
        reliability_scores: Dict[str, float],
        reliability_influence: float = 50,
        weather: str = 'dry',
    ) -> Dict[str, float]:
        """
        Adjust probabilities based on DNF risk.
        
        Args:
            probabilities: Base probabilities
            reliability_scores: Driver reliability scores (0-100)
            reliability_influence: How much to weight reliability (0-100)
            weather: Weather condition
        
        Returns:
            Adjusted probabilities
        """
        influence_factor = reliability_influence / 50.0  # 50 = baseline
        
        adjusted = {}
        for driver_code, prob in probabilities.items():
            reliability = reliability_scores.get(driver_code, 50)
            
            # Calculate DNF risk
            risk_score = (100 - reliability) * influence_factor
            if weather == 'wet':
                risk_score += 6  # Additional risk in wet conditions
            elif weather == 'mixed':
                risk_score += 3
            
            # Adjust probability based on DNF risk
            dnf_factor = 1.0 - (risk_score / 200.0)  # Max 50% reduction
            adjusted[driver_code] = prob * dnf_factor
        
        # Renormalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def apply_grid_weight(
        self,
        probabilities: Dict[str, float],
        grid_positions: Dict[str, int],
        grid_weight: float = 55,
    ) -> Dict[str, float]:
        """
        Adjust probabilities based on grid position using empirical multiplier.
        
        Args:
            probabilities: Base probabilities
            grid_positions: Driver grid positions
            grid_weight: Weight for grid influence (0-100)
        
        Returns:
            Adjusted probabilities
        """
        from backend.app.config.constants import grid_prior_multiplier
        
        weight_factor = grid_weight / 100.0
        adjusted = {}
        
        for driver_code, prob in probabilities.items():
            grid_pos = grid_positions.get(driver_code)
            if grid_pos:
                mult = grid_prior_multiplier(grid_pos)
                grid_factor = 1.0 + (mult - 1.0) * weight_factor
                adjusted[driver_code] = prob * max(0.1, grid_factor)
            else:
                adjusted[driver_code] = prob
        
        # Renormalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def calibrate_probabilities(
        self,
        probabilities: Dict[str, float],
        target_id: str,
        calibration_params: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Apply calibration to probabilities using historical accuracy data.
        
        Args:
            probabilities: Base probabilities
            target_id: Target identifier
            calibration_params: Calibration parameters for target
        
        Returns:
            Calibrated probabilities
        """
        params = calibration_params or self.calibration_params.get(target_id, {})
        
        if not params:
            # No calibration parameters, return as-is
            return probabilities
        
        # Apply isotonic-like calibration
        # Simple version: scale based on historical accuracy
        target = self.targets.get(target_id.lower())
        if target:
            model_accuracy = target['accuracy']
            baseline_accuracy = target.get('baseline_accuracy', 0.1)
            
            # Calibration factor based on model vs baseline performance
            calib_factor = model_accuracy / max(baseline_accuracy, 0.01)
            
            calibrated = {}
            for driver_code, prob in probabilities.items():
                # Apply calibration with some smoothing
                calibrated[driver_code] = prob * calib_factor
            
            # Renormalize
            total = sum(calibrated.values())
            if total > 0:
                calibrated = {k: v / total for k, v in calibrated.items()}
            
            return calibrated
        
        return probabilities
    
    def get_confidence_score(
        self,
        probabilities: Dict[str, float],
        target_id: str,
    ) -> float:
        """
        Calculate confidence score for predictions.
        Higher confidence when probability is concentrated in few drivers.
        
        Args:
            probabilities: Driver probabilities
            target_id: Target identifier
        
        Returns:
            Confidence score (0-1)
        """
        target = self.targets.get(target_id.lower())
        if not target:
            return 0.5
        
        # Calculate entropy-based confidence
        probs = list(probabilities.values())
        probs = [p for p in probs if p > 0]  # Filter zero probabilities
        
        if not probs:
            return 0.0
        
        # Normalize probabilities
        total = sum(probs)
        if total == 0:
            return 0.0
        probs = [p / total for p in probs]
        
        # Calculate entropy
        entropy = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
        
        # Maximum entropy for uniform distribution
        max_entropy = np.log2(len(probs))
        
        # Confidence = 1 - (entropy / max_entropy)
        confidence = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        
        return confidence
    
    # Alias for convenience
    calculate_confidence = get_confidence_score
    
    def generate_prediction_summary(
        self,
        probabilities: Dict[str, float],
        target_id: str,
        confidence: float,
        source: str = 'model',
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive prediction summary.
        
        Args:
            probabilities: Driver probabilities
            target_id: Target identifier
            confidence: Confidence score
            source: Data source label
        
        Returns:
            Prediction summary dictionary
        """
        # Sort drivers by probability
        sorted_drivers = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        
        target = self.targets.get(target_id.lower())
        
        return {
            'target_id': target_id,
            'target_label': target['label'] if target else target_id,
            'predictions': [
                {
                    'driver_code': code,
                    'probability': prob,
                    'percentage': prob * 100,
                }
                for code, prob in sorted_drivers
            ],
            'confidence': confidence,
            'source': source,
            'top_prediction': sorted_drivers[0] if sorted_drivers else None,
            'target_info': target,
        }


# Global probability model instance
probability_model = ProbabilityModel()


def enforce_probability_sum(probabilities: Dict[str, float], tolerance: float = 1e-6) -> Dict[str, float]:
    """Enforce that probabilities sum to exactly 1.0."""
    try:
        total = sum(probabilities.values())
        
        if abs(total - 1.0) > tolerance:
            logger.warning(f"Probabilities sum to {total:.6f}, adjusting to sum to 1.0")
            
            # Adjust by scaling all probabilities
            if total > 0:
                adjusted_probabilities = {
                    driver: prob / total 
                    for driver, prob in probabilities.items()
                }
            else:
                # If total is zero, distribute equally
                num_drivers = len(probabilities)
                adjusted_probabilities = {
                    driver: 1.0 / num_drivers 
                    for driver in probabilities.keys()
                }
            
            return adjusted_probabilities
        
        return probabilities
        
    except Exception as e:
        logger.error(f"Error enforcing probability sum: {e}")
        raise


def calibrate_probabilities(probabilities: Dict[str, float], calibration_factor: float = 0.95) -> Dict[str, float]:
    """Apply probability calibration to reduce overconfidence."""
    try:
        calibrated = {}
        for driver, prob in probabilities.items():
            # Apply calibration: move towards uniform distribution
            uniform_prob = 1.0 / len(probabilities)
            calibrated[driver] = (prob * calibration_factor) + (uniform_prob * (1 - calibration_factor))
        
        # Enforce sum = 1.0 after calibration
        return enforce_probability_sum(calibrated)
        
    except Exception as e:
        logger.error(f"Error calibrating probabilities: {e}")
        raise


def calculate_confidence_intervals(probabilities: Dict[str, float], confidence_level: float = 0.95) -> Dict[str, Dict[str, float]]:
    """Calculate confidence intervals for probabilities using Monte Carlo simulation."""
    try:
        import random
        
        # Simulate multiple runs to get confidence intervals
        num_simulations = 1000
        simulations = []
        
        for _ in range(num_simulations):
            # Simulate a race outcome based on current probabilities
            outcomes = []
            for driver, prob in probabilities.items():
                # Generate random number and check if driver wins
                if random.random() < prob:
                    outcomes.append(driver)
            
            # Count wins for each driver
            win_counts = {}
            for driver in probabilities.keys():
                win_counts[driver] = outcomes.count(driver)
            
            # Convert to probabilities
            sim_probs = {driver: count / num_simulations for driver, count in win_counts.items()}
            simulations.append(sim_probs)
        
        # Calculate confidence intervals
        confidence_intervals = {}
        alpha = (1 - confidence_level) / 2
        lower_percentile = int(alpha * num_simulations)
        upper_percentile = int((1 - alpha) * num_simulations)
        
        for driver in probabilities.keys():
            driver_probs = [sim.get(driver, 0.0) for sim in simulations]
            driver_probs.sort()
            
            lower_bound = driver_probs[lower_percentile] if lower_percentile < len(driver_probs) else 0.0
            upper_bound = driver_probs[upper_percentile] if upper_percentile < len(driver_probs) else 1.0
            
            confidence_intervals[driver] = {
                'lower': round(lower_bound, 4),
                'upper': round(upper_bound, 4)
            }
        
        return confidence_intervals
        
    except Exception as e:
        logger.error(f"Error calculating confidence intervals: {e}")
        raise


def detect_model_drift(current_probabilities: Dict[str, float], historical_probabilities: Optional[Dict[str, float]] = None) -> float:
    """Detect model drift by comparing current vs historical probabilities."""
    try:
        if not historical_probabilities:
            # Use simple heuristic: variance of current probabilities
            probs_list = list(current_probabilities.values())
            if len(probs_list) < 2:
                return 0.0
            
            # Calculate variance
            mean = sum(probs_list) / len(probs_list)
            variance = sum((p - mean) ** 2 for p in probs_list) / len(probs_list)
            return variance
        
        # Calculate KL divergence between current and historical
        import math
        kl_divergence = 0.0
        for driver in current_probabilities.keys():
            current_p = current_probabilities.get(driver, 0.0)
            historical_p = historical_probabilities.get(driver, 0.0)
            
            if current_p > 0 and historical_p > 0:
                kl_divergence += current_p * math.log(current_p / historical_p)
        
        return kl_divergence
        
    except Exception as e:
        logger.error(f"Error detecting model drift: {e}")
        return 0.0


def save_prediction_metadata(race_id: str, session_type: str, probabilities: Dict[str, float], confidence_intervals: Optional[Dict[str, Dict[str, float]]] = None, model_drift_score: Optional[float] = None):
    """Save prediction metadata including validation information."""
    try:
        db_client = DatabaseClient()
        total_sum = sum(probabilities.values())
        
        # Determine validation status
        if abs(total_sum - 1.0) < 1e-6:
            status = "valid"
            errors = None
        else:
            status = "adjusted"
            errors = f"Original sum: {total_sum:.6f}, adjusted to 1.0"
        
        metadata = PredictionMetadata(
            race_id=race_id,
            session_type=session_type,
            total_probability_sum=total_sum,
            probability_validation_status=status,
            validation_errors=errors,
            model_drift_score=model_drift_score
        )
        
        with db_client.get_session() as db:
            db.add(metadata)
            db.commit()
            db.refresh(metadata)
        
        logger.info(f"Saved prediction metadata for race {race_id}: {status}")
        
    except Exception as e:
        logger.error(f"Error saving prediction metadata for race {race_id}: {e}")
        raise


def calculate_winner_probabilities(race_id: str, session_type: str) -> Dict[str, float]:
    """
    Calculate winner probabilities for a race session.
    
    Returns:
        Dictionary mapping driver codes to probabilities
    """
    try:
        logger.info(f"Calculating winner probabilities for race {race_id}, session {session_type}")
        
        # Build session context with all available data sources
        session_context = build_session_context(race_id, session_type)
        
        # Get all drivers for the season
        from backend.app.config.team_driver_lineup_2026 import get_all_drivers
        all_drivers = [d['code'] for d in get_all_drivers()]
        
        # Initialize probabilities
        probabilities = {}
        
        # Calculate base probabilities based on various factors
        for driver_code in all_drivers:
            # Get driver-specific data from session context
            driver_data = session_context.get('driver_data', {}).get(driver_code, {})
            
            # Calculate base probability (simplified example)
            base_probability = 0.1  # Default base probability
            
            # Adjust based on performance factors
            if 'performance_score' in driver_data:
                base_probability *= driver_data['performance_score']
            
            # Apply strength adjustments from session context
            strength_adjustment = session_context.get('strength_adjustments', {}).get(driver_code, 0.0)
            base_probability += strength_adjustment
            
            # Ensure probability is within valid range
            base_probability = max(0.0, min(1.0, base_probability))
            
            probabilities[driver_code] = base_probability
        
        # Normalize probabilities to sum to 1.0
        probabilities = enforce_probability_sum(probabilities)
        
        logger.info(f"Calculated winner probabilities for {len(probabilities)} drivers")
        return probabilities
        
    except Exception as e:
        logger.error(f"Error calculating winner probabilities: {e}")
        raise
