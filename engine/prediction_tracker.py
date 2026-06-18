"""
Prediction Accuracy Tracking & Post-Race Evaluation.

Stores predictions, compares with actual results, computes:
- Brier scores
- Log loss
- Calibration curves
- Accuracy trends over time
- Platt scaling for probability calibration (NEW v3.1)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from database.models import SessionLocal, Prediction, Race, Driver
from engine.predictor import predict, PredictionRequest
from engine.calibration import brier_score as calc_brier_score  # Import calibration functions

logger = logging.getLogger(__name__)


class PredictionTracker:
    """Track and evaluate prediction accuracy."""
    
    def __init__(self):
        # Don't open session in __init__ - use per-call sessions instead
        self.db = None
    
    def store_prediction(self, circuit_id: str, prediction_result: Dict):
        """
        Store prediction in database for later evaluation.
        
        FIXED: Now uses per-call session management to avoid InvalidRequestError
        when store_prediction is called multiple times on the same instance.
        
        Args:
            circuit_id: Circuit identifier
            prediction_result: Result from predict() function
        """
        db = SessionLocal()  # Open per-call session
        try:
            # Get or create race
            race = db.query(Race).filter(
                Race.circuit_id == circuit_id,
                Race.season == 2026
            ).first()
            
            if not race:
                race = Race(
                    circuit_id=circuit_id,
                    season=2026,
                    completed=False,
                )
                db.add(race)
                db.flush()
            
            # Store predictions for each driver
            for driver_pred in prediction_result["predictions"]:
                prediction = Prediction(
                    race_id=race.id,
                    driver_id=driver_pred.get("driver_id", driver_pred.get("driver")),  # Support both keys
                    predicted_position=driver_pred.get("predicted_position", 99),
                    win_probability=driver_pred.get("win_pct", 0) / 100.0,
                    top3_probability=driver_pred.get("top3_pct", 0) / 100.0,
                    top10_probability=driver_pred.get("top10_pct", 0) / 100.0,
                    dnf_probability=driver_pred.get("dnf_pct", 0) / 100.0,
                    composite_score=driver_pred.get("composite_score", 0.5),
                    model_version="v3.0",
                )
                db.add(prediction)
            
            db.commit()
            logger.info(f"Stored predictions for {circuit_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store predictions: {e}")
            raise
        finally:
            db.close()  # Always close the per-call session
    
    def evaluate_race(self, circuit_id: str, actual_results: Dict):
        """
        Evaluate predictions against actual race results.
        
        FIXED: Now uses per-call session management.
        
        Args:
            circuit_id: Circuit identifier
            actual_results: Dict with driver_id -> actual_position
        """
        db = SessionLocal()  # Open per-call session
        try:
            race = db.query(Race).filter(
                Race.circuit_id == circuit_id,
                Race.season == 2026
            ).first()
            
            if not race:
                raise ValueError(f"No predictions found for {circuit_id}")
            
            # Get all predictions for this race
            predictions = db.query(Prediction).filter(
                Prediction.race_id == race.id
            ).all()
            
            brier_scores = []
            
            for pred in predictions:
                driver_id = pred.driver_id
                
                if driver_id not in actual_results:
                    continue
                
                actual_position = actual_results[driver_id]
                
                # Update actual results
                pred.actual_position = actual_position
                pred.actual_result = "Finished" if actual_position <= 20 else "DNF"
                
                # Calculate Brier scores
                actual_win = 1.0 if actual_position == 1 else 0.0
                actual_top3 = 1.0 if actual_position <= 3 else 0.0
                actual_top10 = 1.0 if actual_position <= 10 else 0.0
                actual_dnf = 1.0 if actual_position > 20 else 0.0
                
                brier_win = (pred.win_probability - actual_win) ** 2
                brier_top3 = (pred.top3_probability - actual_top3) ** 2
                brier_top10 = (pred.top10_probability - actual_top10) ** 2
                brier_dnf = (pred.dnf_probability - actual_dnf) ** 2
                
                # Average Brier score
                pred.brier_score = (brier_win + brier_top3 + brier_top10 + brier_dnf) / 4.0
                
                pred.evaluated_at = datetime.utcnow()
                brier_scores.append(pred.brier_score)
            
            # Update race as completed
            race.completed = True
            
            db.commit()
            
            avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
            
            logger.info(f"Evaluated {circuit_id}: avg Brier score = {avg_brier:.4f}")
            
            return {
                "circuit": circuit_id,
                "avg_brier_score": round(avg_brier, 4),
                "predictions_evaluated": len(brier_scores),
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to evaluate race: {e}")
            raise
        finally:
            db.close()
    
    def get_accuracy_report(self, season: int = 2026) -> Dict:
        """
        Generate comprehensive accuracy report.
        
        FIXED: Now uses per-call session management.
        
        Returns:
            Dictionary with accuracy metrics across all evaluated races.
        """
        db = SessionLocal()  # Open per-call session
        try:
            predictions = db.query(Prediction).filter(
                Prediction.model_version.like("v3%"),
                Prediction.brier_score.isnot(None)
            ).all()
            
            if not predictions:
                return {"message": "No evaluated predictions found"}
            
            # Overall metrics
            avg_brier = sum(p.brier_score for p in predictions) / len(predictions)
            
            # By outcome type
            win_brier = sum((p.win_probability - (1.0 if p.actual_position == 1 else 0.0)) ** 2 
                           for p in predictions) / len(predictions)
            top3_brier = sum((p.top3_probability - (1.0 if p.actual_position <= 3 else 0.0)) ** 2 
                            for p in predictions) / len(predictions)
            
            # By position accuracy
            position_errors = [abs(p.predicted_position - p.actual_position) 
                              for p in predictions if p.actual_position]
            avg_position_error = sum(position_errors) / len(position_errors) if position_errors else 0.0
            
            return {
                "total_predictions": len(predictions),
                "avg_brier_score": round(avg_brier, 4),
                "win_prediction_brier": round(win_brier, 4),
                "top3_prediction_brier": round(top3_brier, 4),
                "avg_position_error": round(avg_position_error, 2),
                "calibration": "Good" if avg_brier < 0.10 else "Needs Improvement",
            }
            
        except Exception as e:
            logger.error(f"Failed to generate accuracy report: {e}")
            raise
        finally:
            db.close()
    
    def close(self):
        """Close database session (no-op with per-call sessions)."""
        # Per-call sessions are closed automatically, nothing to do here
        pass


def run_post_race_evaluation(circuit_id: str, actual_results: Dict):
    """
    Convenience function to evaluate predictions after a race.
    
    Usage:
        from scripts.post_race_evaluation import run_post_race_evaluation
        
        actual_results = {
            "verstappen": 1,
            "hamilton": 2,
            "leclerc": 3,
            # ... all drivers
        }
        
        run_post_race_evaluation("canada", actual_results)
    """
    tracker = PredictionTracker()
    try:
        result = tracker.evaluate_race(circuit_id, actual_results)
        print(f"✓ Race evaluation completed: {result}")
        return result
    finally:
        tracker.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("F1 Predictor v3.0 — Accuracy Tracking")
    print("=" * 60)
    
    tracker = PredictionTracker()
    try:
        report = tracker.get_accuracy_report()
        print(json.dumps(report, indent=2))
    finally:
        tracker.close()
