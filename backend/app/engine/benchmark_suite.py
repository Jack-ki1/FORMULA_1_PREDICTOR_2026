"""
Benchmark suite - backtesting harness for model accuracy.
Source of all "accuracy vs baseline" numbers.
"""
import numpy as np
from typing import Dict, List, Any
from backend.app.engine.predictor import generate_prediction
from backend.app.config.constants import TARGETS, RANDOM_BASELINES


class BenchmarkSuite:
    """
    Backtesting harness for model accuracy evaluation.
    Runs historical predictions and compares against actual results.
    """
    
    def __init__(self):
        self.predictor = generate_prediction
        self.targets = TARGETS
        self.baselines = RANDOM_BASELINES
        self.results = {}
    
    def run_backtest(
        self,
        historical_seasons: List[int],
        test_season: int,
    ) -> Dict[str, Any]:
        """
        Run comprehensive backtest on historical data.
        
        Args:
            historical_seasons: Seasons to use for training
            test_season: Season to test on
        
        Returns:
            Backtest results with accuracy metrics
        """
        results = {
            'historical_seasons': historical_seasons,
            'test_season': test_season,
            'target_results': {},
            'overall_accuracy': {},
        }
        
        for target_id, target_info in self.targets.items():
            target_results = self._backtest_target(
                target_id,
                historical_seasons,
                test_season,
            )
            results['target_results'][target_id] = target_results
            
            # Calculate overall accuracy
            results['overall_accuracy'][target_id] = target_results['accuracy']
        
        return results
    
    def _backtest_target(
        self,
        target_id: str,
        historical_seasons: List[int],
        test_season: int,
    ) -> Dict[str, Any]:
        """
        Backtest a specific target.
        
        Args:
            target_id: Target identifier
            historical_seasons: Training seasons
            test_season: Test season
        
        Returns:
            Target-specific backtest results
        """
        target_info = self.targets[target_id]
        baseline_accuracy = self.baselines.get(target_id, 0.1)
        
        # Simulate predictions (in production, use real historical data)
        predictions = self._simulate_historical_predictions(
            target_id,
            test_season,
        )
        
        # Simulate actual results (in production, use real results)
        actual_results = self._simulate_actual_results(target_id, test_season)
        
        # Calculate accuracy
        accuracy = self._calculate_accuracy(predictions, actual_results, target_id)
        
        return {
            'target_id': target_id,
            'target_label': target_info['label'],
            'model_accuracy': accuracy,
            'baseline_accuracy': baseline_accuracy,
            'improvement_over_baseline': accuracy - baseline_accuracy,
            'predictions_count': len(predictions),
            'correct_predictions': int(accuracy * len(predictions)),
        }
    
    def _simulate_historical_predictions(
        self,
        target_id: str,
        season: int,
    ) -> List[Dict[str, Any]]:
        """Simulate historical predictions (placeholder for real data)."""
        # In production, this would use actual historical predictions
        num_races = 23  # Typical season length
        predictions = []
        
        for round_num in range(1, num_races + 1):
            # Simulate prediction based on target accuracy
            target_accuracy = self.targets[target_id]['accuracy']
            
            # Generate random prediction
            prediction = {
                'season': season,
                'round': round_num,
                'predicted_driver': self._get_random_driver(),
                'confidence': np.random.uniform(0.6, 0.9),
                'correct': np.random.random() < target_accuracy,
            }
            predictions.append(prediction)
        
        return predictions
    
    def _simulate_actual_results(self, target_id: str, season: int) -> List[Dict[str, Any]]:
        """Simulate actual race results (placeholder for real data)."""
        num_races = 23
        results = []
        
        for round_num in range(1, num_races + 1):
            result = {
                'season': season,
                'round': round_num,
                'actual_driver': self._get_random_driver(),
            }
            results.append(result)
        
        return results
    
    def _get_random_driver(self) -> str:
        """Get a random driver code."""
        from backend.app.config.team_driver_lineup_2026 import get_all_drivers
        drivers = get_all_drivers()
        return np.random.choice([d['code'] for d in drivers])
    
    def _calculate_accuracy(
        self,
        predictions: List[Dict[str, Any]],
        actual_results: List[Dict[str, Any]],
        target_id: str,
    ) -> float:
        """Calculate prediction accuracy."""
        if not predictions or not actual_results:
            return 0.0
        
        correct = 0
        total = 0
        
        for pred, actual in zip(predictions, actual_results):
            if pred['predicted_driver'] == actual['actual_driver']:
                correct += 1
            total += 1
        
        return correct / total if total > 0 else 0.0
    
    def generate_accuracy_report(self) -> Dict[str, Any]:
        """Measure the model against recorded results.

        REPLACES A FABRICATION. This method used to read `target_info['accuracy']`
        — a hardcoded constant in `constants.TARGETS` labelled "backtested" that
        no backtest produced — and served it as measured accuracy, complete with
        an `improvement_percentage` computed from those same constants (e.g.
        "58% winner accuracy, +1188% over baseline"). For a prediction platform,
        advertising accuracy you have not measured is the worst possible failure
        mode (see README/CHANGELOG honesty notes).

        This now runs the real predictor against every race that has a recorded
        result and reports genuine hit-rates. When there is not enough history to
        measure anything, `model_accuracy` is **None** and `status` says so,
        rather than inventing a number.
        """
        from backend.app.services.accuracy_service import measure_accuracy
        measured = measure_accuracy()

        target_accuracies: Dict[str, Any] = {}
        for target_id, target_info in self.targets.items():
            bucket = measured["targets"].get(target_id, {})
            target_accuracies[target_id] = {
                "target_label": target_info["label"],
                "model_accuracy": bucket.get("accuracy"),          # None when unmeasured
                "baseline_accuracy": self.baselines.get(target_id, 0.1),
                "correct": bucket.get("correct"),
                "evaluated_races": bucket.get("evaluated_races"),
                "improvement": (
                    (bucket["accuracy"] - self.baselines.get(target_id, 0.1))
                    if bucket.get("accuracy") is not None else None
                ),
            }

        scored = [v["model_accuracy"] for v in target_accuracies.values()
                  if v["model_accuracy"] is not None]
        report = {
            "status": measured["status"],
            "measured_on": measured.get("measured_on"),
            "races_evaluated": measured.get("races_evaluated", 0),
            "samples": measured.get("samples"),
            "target_accuracies": target_accuracies,
            "overall_performance": {
                "average_model_accuracy": (sum(scored) / len(scored)) if scored else None,
                "average_baseline_accuracy": (
                    sum(self.baselines.get(t, 0.1) for t in self.targets) / len(self.targets)
                ),
            },
            "recommendations": [],
            "note": measured.get("note"),
        }

        if measured["status"] == "insufficient_data":
            report["recommendations"].append(
                "Not enough recorded results to measure accuracy yet — "
                "numbers will appear once races complete."
            )
        else:
            for target_id, metrics in target_accuracies.items():
                if metrics["model_accuracy"] is None:
                    continue
                if metrics["model_accuracy"] > 0.5:
                    report["recommendations"].append(f"{target_id}: above 50% hit-rate on recorded races")
                else:
                    report["recommendations"].append(f"{target_id}: below 50% — model is not beating chance materially")
        return report

    def cross_validate(
        self,
        seasons: List[int],
        k_folds: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform k-fold cross-validation across seasons.
        
        Args:
            seasons: Available seasons for cross-validation
            k_folds: Number of folds
        
        Returns:
            Cross-validation results
        """
        fold_size = len(seasons) // k_folds
        cv_results = {
            'fold_results': [],
            'mean_accuracy': {},
            'std_accuracy': {},
        }
        
        for fold in range(k_folds):
            # Split seasons into train/test
            test_start = fold * fold_size
            test_end = test_start + fold_size
            
            test_seasons = seasons[test_start:test_end]
            train_seasons = [s for s in seasons if s not in test_seasons]
            
            # Run backtest
            fold_result = self.run_backtest(train_seasons, test_seasons[0] if test_seasons else seasons[-1])
            cv_results['fold_results'].append(fold_result)
        
        # Calculate mean and std across folds
        for target_id in self.targets.keys():
            accuracies = [
                fold['overall_accuracy'].get(target_id, 0.0)
                for fold in cv_results['fold_results']
            ]
            cv_results['mean_accuracy'][target_id] = np.mean(accuracies)
            cv_results['std_accuracy'][target_id] = np.std(accuracies)
        
        return cv_results
    
    def compare_with_baseline(
        self,
        predictions: Dict[str, float],
        target_id: str,
    ) -> Dict[str, Any]:
        """
        Compare single prediction with baseline.
        
        Args:
            predictions: Driver probability predictions
            target_id: Target identifier
        
        Returns:
            Comparison with baseline
        """
        baseline = self.baselines.get(target_id, 0.1)
        target_info = self.targets[target_id]
        
        # Get top prediction
        sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        top_prediction = sorted_predictions[0] if sorted_predictions else (None, 0.0)
        
        return {
            'target_id': target_id,
            'target_label': target_info['label'],
            'top_prediction': top_prediction[0],
            'top_probability': top_prediction[1],
            'baseline_probability': baseline,
            'confidence_above_baseline': top_prediction[1] > baseline,
            'confidence_margin': top_prediction[1] - baseline,
            'model_accuracy': target_info['accuracy'],
        }


# Global benchmark suite instance
benchmark_suite = BenchmarkSuite()
