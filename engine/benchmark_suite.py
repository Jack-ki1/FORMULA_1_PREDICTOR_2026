"""
Comprehensive Benchmark Suite for F1 Prediction System.

Evaluates prediction accuracy across multiple metrics:
  1. Brier Score (probability calibration)
  2. Log-Loss (probabilistic prediction quality)
  3. Top-1/Top-3/Top-5 accuracy (classification)
  4. Kendall's Tau rank correlation (ordering quality)
  5. Mean Average Error on finishing positions
  6. Model comparison across all prediction sources
  7. Calibration curves and reliability diagrams

Can be used to compare Monte Carlo, XGBoost, Plackett-Luce,
and Ensemble predictions.
"""

import logging
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)

# Optional imports
try:
    from scipy.stats import kendalltau
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False

try:
    import optuna
    _OPTUNA_AVAILABLE = True
except ImportError:
    _OPTUNA_AVAILABLE = False


# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""
    seasons: List[int] = field(default_factory=lambda: [2022, 2023, 2024, 2025, 2026])
    n_simulations: int = 10000
    use_vectorized: bool = True
    use_xgboost: bool = True
    use_plackett_luce: bool = True
    use_ensemble: bool = True
    verbose: bool = True
    output_dir: str = "benchmark_results"


@dataclass
class RaceMetrics:
    """Metrics for a single race prediction."""
    race_name: str
    circuit_id: str

    # Brier scores (lower is better, perfect = 0)
    win_brier: float = 0.0
    top3_brier: float = 0.0
    top10_brier: float = 0.0
    dnf_brier: float = 0.0
    avg_brier: float = 0.0

    # Log-loss (lower is better)
    win_logloss: float = 0.0
    top3_logloss: float = 0.0

    # Accuracy metrics
    top1_accuracy: bool = False   # Winner correct?
    top3_accuracy: float = 0.0   # How many of top 3 correct (0-1)
    top5_accuracy: float = 0.0   # How many of top 5 correct (0-1)

    # Rank correlation
    kendall_tau: float = 0.0     # -1 to 1
    avg_position_error: float = 0.0

    # Calibration
    calibration_error: float = 0.0


@dataclass
class ModelBenchmarkSummary:
    """Summary of benchmark results for a single model."""
    model_name: str
    n_races: int

    # Aggregated metrics
    avg_win_brier: float = 0.0
    avg_top3_brier: float = 0.0
    avg_brier: float = 0.0
    avg_logloss: float = 0.0

    top1_accuracy_rate: float = 0.0
    top3_accuracy_rate: float = 0.0
    top5_accuracy_rate: float = 0.0

    avg_kendall_tau: float = 0.0
    avg_position_error: float = 0.0
    avg_calibration_error: float = 0.0

    # Performance scores (normalized 0-100)
    overall_score: float = 0.0
    brier_score_performance: float = 0.0
    ranking_performance: float = 0.0
    calibration_performance: float = 0.0


# ── Metric Calculators ──────────────────────────────────────────────────────

def calculate_brier_score(
    predicted_probs: List[float],
    actual_outcomes: List[int],
) -> float:
    """
    Calculate Brier Score.

    Brier = (1/n) * sum((p_i - o_i)^2)
    - Perfect: 0.0
    - Always-guess-0.5: 0.25
    - Always-wrong: 1.0

    Args:
        predicted_probs: List of predicted probabilities [0, 1]
        actual_outcomes: List of binary outcomes (0 or 1)

    Returns:
        Brier score
    """
    if not predicted_probs or len(predicted_probs) != len(actual_outcomes):
        return 0.0
    return float(np.mean([(p - o) ** 2 for p, o in zip(predicted_probs, actual_outcomes)]))


def calculate_log_loss(
    predicted_probs: List[float],
    actual_outcomes: List[int],
    eps: float = 1e-15,
) -> float:
    """
    Calculate Log-Loss (cross-entropy).

    LL = -(1/n) * sum(o_i * log(p_i) + (1-o_i) * log(1-p_i))

    Args:
        predicted_probs: List of predicted probabilities
        actual_outcomes: List of binary outcomes
        eps: Epsilon for numerical stability

    Returns:
        Log-loss value
    """
    if not predicted_probs or len(predicted_probs) != len(actual_outcomes):
        return 0.0

    probs = np.clip(predicted_probs, eps, 1 - eps)
    outcomes = np.array(actual_outcomes)
    return float(-np.mean(outcomes * np.log(probs) + (1 - outcomes) * np.log(1 - probs)))


def calculate_kendall_tau(
    predicted_ranking: List[str],
    actual_ranking: List[str],
) -> float:
    """
    Calculate Kendall's Tau rank correlation coefficient.

    Measures the similarity between predicted and actual finishing order.
    - 1.0: Perfect agreement
    - 0.0: Random
    - -1.0: Perfect disagreement

    Args:
        predicted_ranking: Driver IDs in predicted order (first = winner)
        actual_ranking: Driver IDs in actual finishing order

    Returns:
        Kendall's Tau (-1 to 1)
    """
    if not predicted_ranking or not actual_ranking:
        return 0.0

    # Create rank arrays for common drivers
    common_drivers = set(predicted_ranking) & set(actual_ranking)
    if len(common_drivers) < 3:
        return 0.0

    pred_ranks = {d: i for i, d in enumerate(predicted_ranking) if d in common_drivers}
    actual_ranks = {d: i for i, d in enumerate(actual_ranking) if d in common_drivers}

    common_list = list(common_drivers)
    pred_order = [pred_ranks[d] for d in common_list]
    actual_order = [actual_ranks[d] for d in common_list]

    if _SCIPY_AVAILABLE:
        tau, _ = kendalltau(pred_order, actual_order)
        return float(tau) if not math.isnan(tau) else 0.0
    else:
        # Manual Kendall Tau calculation
        n = len(common_list)
        concordant = 0
        discordant = 0
        for i in range(n):
            for j in range(i + 1, n):
                if (pred_order[i] - pred_order[j]) * (actual_order[i] - actual_order[j]) > 0:
                    concordant += 1
                else:
                    discordant += 1
        total = concordant + discordant
        return (concordant - discordant) / total if total > 0 else 0.0


def calculate_calibration_error(
    predicted_probs: List[float],
    actual_outcomes: List[int],
    n_bins: int = 10,
) -> float:
    """
    Calculate calibration error (ECE - Expected Calibration Error).

    Measures how well predicted probabilities match actual frequencies.
    Lower is better (perfect = 0.0).

    Args:
        predicted_probs: Predicted probabilities
        actual_outcomes: Binary outcomes
        n_bins: Number of probability bins

    Returns:
        Expected calibration error
    """
    if len(predicted_probs) < n_bins * 2:
        return 0.0

    bins = [[] for _ in range(n_bins)]
    for p, o in zip(predicted_probs, actual_outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, o))

    errors = []
    for b in bins:
        if len(b) < 2:
            continue
        mean_pred = np.mean([p for p, _ in b])
        actual_rate = np.mean([o for _, o in b])
        weight = len(b) / len(predicted_probs)
        errors.append(weight * abs(mean_pred - actual_rate))

    return float(np.sum(errors)) if errors else 0.0


# ── Historical Data Loader ──────────────────────────────────────────────────

class HistoricalDataLoader:
    """Loads historical race results for benchmarking."""

    def __init__(self):
        self._results_cache: Dict[int, List[Dict]] = {}

    def load_season(self, season: int) -> List[Dict]:
        """
        Load completed race results for a season.

        Args:
            season: Season year (2022-2026)

        Returns:
            List of race dicts with results
        """
        if season in self._results_cache:
            return self._results_cache[season]

        # Try bundled 2026 data first
        if season == 2026:
            try:
                from data.season_2026 import SEASON_RESULTS_2026
                races = [
                    r for r in SEASON_RESULTS_2026
                    if r.get("results") and len(r["results"]) >= 10
                ]
                self._results_cache[season] = races
                logger.info(f"Loaded {len(races)} completed races from {season}")
                return races
            except Exception as e:
                logger.warning(f"Could not load {season} bundled data: {e}")

        # Try Jolpica API for historical seasons
        try:
            from data.jolpica_client import get_jolpica_client
            client = get_jolpica_client()
            races = []

            # Get season schedule
            schedule = client.get_season_schedule(season)
            for race in schedule:
                round_num = race.get("round", 0)
                try:
                    race_result = client.get_race_results(season, round_num)
                    if race_result and race_result.get("results"):
                        from data.live_updater import _ERGAST_CODE_TO_OUR_ID
                        mapped_results = []
                        for r in race_result["results"]:
                            code = r.get("driver_code", "")
                            our_id = _ERGAST_CODE_TO_OUR_ID.get(code, code.lower())
                            mapped_results.append({
                                "driver": our_id,
                                "position": r.get("position", 0),
                                "status": r.get("status", "Finished"),
                                "points": r.get("points", 0),
                            })
                        races.append({
                            "round": round_num,
                            "circuit": race.get("circuit_id", "").lower(),
                            "name": race.get("race_name", f"Round {round_num}"),
                            "date": race.get("date", ""),
                            "results": mapped_results,
                        })
                except Exception:
                    continue

            self._results_cache[season] = races
            logger.info(f"Loaded {len(races)} races from {season} via Jolpica API")
            return races

        except Exception as e:
            logger.warning(f"Could not load season {season}: {e}")
            return []


# ── Prediction Runner ───────────────────────────────────────────────────────

class PredictionRunner:
    """Runs predictions using available models for benchmarking."""

    @staticmethod
    def run_mc_prediction(circuit_id: str, n_simulations: int = 10000) -> Optional[List[Dict]]:
        """Run Monte Carlo simulation prediction."""
        try:
            from engine.predictor import predict, PredictionRequest
            result = predict(PredictionRequest(
                circuit_id=circuit_id,
                n_simulations=n_simulations,
                seed=42,
            ))
            return result.get("predictions", [])
        except Exception as e:
            logger.warning(f"MC prediction failed for {circuit_id}: {e}")
            return None

    @staticmethod
    def run_xgb_prediction(circuit_id: str) -> Optional[List[Dict]]:
        """Run XGBoost ranked prediction."""
        try:
            from engine.feature_engineering import compute_all_drivers
            from engine.ml_models import get_ml_predictions

            driver_features = compute_all_drivers(circuit_id)
            ml_result = get_ml_predictions(driver_features, circuit_id)

            predictions = []
            for r in ml_result.rankings:
                predictions.append({
                    "driver_id": r.driver_id,
                    "driver_name": r.driver_name,
                    "team": r.team,
                    "win_probability": r.pl_win_prob or (1.0 / max(len(ml_result.rankings), 1)),
                    "top3_probability": r.pl_top3_prob or (3.0 / max(len(ml_result.rankings), 1)),
                    "top10_probability": r.pl_top10_prob or (10.0 / max(len(ml_result.rankings), 1)),
                    "predicted_position": r.rank_position,
                })
            return predictions
        except Exception as e:
            logger.warning(f"XGBoost prediction failed for {circuit_id}: {e}")
            return None

    @staticmethod
    def run_ensemble_prediction(circuit_id: str, n_simulations: int = 10000) -> Optional[List[Dict]]:
        """Run ensemble prediction."""
        try:
            from engine.predictor import predict, PredictionRequest
            from engine.ensemble_predictor import EnsemblePredictor

            # Get MC predictions
            mc_result = predict(PredictionRequest(
                circuit_id=circuit_id,
                n_simulations=n_simulations,
                seed=42,
            ))
            mc_preds = mc_result.get("predictions", [])

            # Get XGBoost predictions
            from engine.feature_engineering import compute_all_drivers
            from engine.ml_models import get_ml_predictions
            driver_features = compute_all_drivers(circuit_id)
            ml_result = get_ml_predictions(driver_features, circuit_id)

            # Ensemble
            ensemble = EnsemblePredictor()
            ensemble_result = ensemble.predict(
                mc_predictions=mc_preds,
                xgb_rankings=ml_result.rankings if ml_result.rankings else None,
                pl_rankings=ml_result.rankings if ml_result.rankings else None,
                composite_scores=driver_features,
                circuit_id=circuit_id,
            )

            return [
                {
                    "driver_id": p.driver_id,
                    "driver_name": p.driver_name,
                    "team": p.team,
                    "win_probability": p.ensemble_win_prob,
                    "top3_probability": p.ensemble_top3_prob,
                    "top10_probability": p.ensemble_top10_prob,
                    "predicted_position": p.ensemble_position,
                }
                for p in ensemble_result.predictions
            ]
        except Exception as e:
            logger.warning(f"Ensemble prediction failed for {circuit_id}: {e}")
            return None


# ── Benchmark Engine ─────────────────────────────────────────────────────────

class BenchmarkEngine:
    """
    Core benchmark engine that evaluates prediction accuracy across models.
    """

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.data_loader = HistoricalDataLoader()
        self.results: Dict[str, List[RaceMetrics]] = {}

    def run_all(self) -> Dict[str, ModelBenchmarkSummary]:
        """
        Run full benchmark across all configured models and seasons.

        Returns:
            Dict of model_name -> ModelBenchmarkSummary
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE BENCHMARK")
        logger.info("=" * 60)

        all_races = []
        for season in self.config.seasons:
            races = self.data_loader.load_season(season)
            all_races.extend(races)

        if not all_races:
            logger.warning("No historical races available for benchmarking")
            return {}

        logger.info(f"Total races loaded: {len(all_races)}")

        # Run benchmarks for each active model
        if self.config.use_ensemble:
            logger.info("\n--- Benchmarking Ensemble ---")
            self._run_model("ensemble", all_races, PredictionRunner.run_ensemble_prediction)

        if self.config.use_xgboost:
            logger.info("\n--- Benchmarking XGBoost ---")
            self._run_model("xgboost", all_races, PredictionRunner.run_xgb_prediction)

        if True:  # Monte Carlo is always available
            logger.info("\n--- Benchmarking Monte Carlo ---")
            self._run_model("monte_carlo", all_races, PredictionRunner.run_mc_prediction)

        # Generate summaries
        summaries = {}
        for model_name in self.results:
            summary = self._generate_summary(model_name)
            summaries[model_name] = summary
            logger.info(f"\n{model_name.upper()} RESULTS:")
            logger.info(f"  Overall Score:      {summary.overall_score:.1f}/100")
            logger.info(f"  Brier Score:        {summary.avg_brier:.4f}")
            logger.info(f"  Top-1 Accuracy:     {summary.top1_accuracy_rate:.1%}")
            logger.info(f"  Top-3 Accuracy:     {summary.top3_accuracy_rate:.1%}")
            logger.info(f"  Top-5 Accuracy:     {summary.top5_accuracy_rate:.1%}")
            logger.info(f"  Kendall's Tau:      {summary.avg_kendall_tau:.3f}")
            logger.info(f"  Avg Position Error: {summary.avg_position_error:.2f}")

        # Save results
        self._save_results(summaries)

        logger.info("=" * 60)
        logger.info("BENCHMARK COMPLETE")
        logger.info("=" * 60)

        return summaries

    def _run_model(
        self,
        model_name: str,
        races: List[Dict],
        prediction_fn,
    ):
        """Run benchmark for a single model."""
        metrics_list = []
        total = len(races)

        for i, race in enumerate(races):
            circuit_id = race["circuit"]
            name = race.get("name", circuit_id)
            actual_results = race["results"]

            # Skip if not enough actual results
            if len(actual_results) < 5:
                continue

            # Get predictions
            predictions = prediction_fn(circuit_id)
            if not predictions:
                continue

            # Evaluate
            metrics = self._evaluate_single_race(
                name, circuit_id, predictions, actual_results
            )
            if metrics:
                metrics_list.append(metrics)

            if self.config.verbose and (i + 1) % 5 == 0:
                logger.info(f"  [{i+1}/{total}] {name}: Brier={metrics.avg_brier:.4f}")

        self.results[model_name] = metrics_list
        logger.info(f"  Completed {len(metrics_list)}/{total} races for {model_name}")

    def _evaluate_single_race(
        self,
        race_name: str,
        circuit_id: str,
        predictions: List[Dict],
        actual_results: List[Dict],
    ) -> Optional[RaceMetrics]:
        """Evaluate a single race prediction against actual results."""
        # Build lookup dicts
        pred_by_driver = {}
        for p in predictions:
            did = p.get("driver_id", "")
            pred_by_driver[did] = p

        actual_by_driver = {}
        for r in actual_results:
            did = r["driver"]
            actual_by_driver[did] = r

        # Find common drivers
        common = set(pred_by_driver.keys()) & set(actual_by_driver.keys())
        if len(common) < 3:
            return None

        # Calculate Brier scores for top-3 win
        win_probs = []
        win_outcomes = []
        top3_probs = []
        top3_outcomes = []
        top10_probs = []
        top10_outcomes = []

        for did in common:
            pred = pred_by_driver[did]
            actual = actual_by_driver[did]
            pos = actual["position"]

            win_probs.append(pred.get("win_probability", 0))
            win_outcomes.append(1 if pos == 1 else 0)

            top3_probs.append(pred.get("top3_probability", 0))
            top3_outcomes.append(1 if pos <= 3 else 0)

            top10_probs.append(pred.get("top10_probability", 0))
            top10_outcomes.append(1 if pos <= 10 else 0)

        win_brier = calculate_brier_score(win_probs, win_outcomes)
        top3_brier = calculate_brier_score(top3_probs, top3_outcomes)
        top10_brier = calculate_brier_score(top10_probs, top10_outcomes)
        avg_brier = (win_brier + top3_brier + top10_brier) / 3

        win_logloss = calculate_log_loss(win_probs, win_outcomes)

        # Top-1 accuracy
        actual_winner = None
        for r in actual_results:
            if r["position"] == 1:
                actual_winner = r["driver"]
                break

        pred_winner = None
        sorted_preds = sorted(predictions, key=lambda p: p.get("predicted_position", 999))
        if sorted_preds:
            pred_winner = sorted_preds[0].get("driver_id", "")

        top1_correct = actual_winner == pred_winner

        # Top-3 accuracy
        actual_top3 = {r["driver"] for r in actual_results if r["position"] <= 3}
        pred_sorted = sorted(predictions, key=lambda p: p.get("predicted_position", 999))
        pred_top3 = {p.get("driver_id", "") for p in pred_sorted[:3]}
        top3_hits = actual_top3 & pred_top3
        top3_acc = len(top3_hits) / 3.0

        # Top-5 accuracy
        actual_top5 = {r["driver"] for r in actual_results if r["position"] <= 5}
        pred_top5 = {p.get("driver_id", "") for p in pred_sorted[:5]}
        top5_hits = actual_top5 & pred_top5
        top5_acc = len(top5_hits) / 5.0

        # Kendall's Tau
        predicted_ranking = [p.get("driver_id", "") for p in pred_sorted]
        actual_ranking = sorted(actual_results, key=lambda r: r["position"])
        actual_ranking_ids = [r["driver"] for r in actual_ranking]
        kendall_tau = calculate_kendall_tau(predicted_ranking, actual_ranking_ids)

        # Average position error
        position_errors = []
        for r in actual_results[:15]:
            did = r["driver"]
            actual_pos = r["position"]
            pred = pred_by_driver.get(did)
            if pred:
                pred_pos = pred.get("predicted_position", 0)
                if pred_pos > 0:
                    position_errors.append(abs(pred_pos - actual_pos))
        avg_pos_error = float(np.mean(position_errors)) if position_errors else 0.0

        # Calibration error
        cal_error = calculate_calibration_error(win_probs, win_outcomes)

        return RaceMetrics(
            race_name=race_name,
            circuit_id=circuit_id,
            win_brier=round(win_brier, 4),
            top3_brier=round(top3_brier, 4),
            top10_brier=round(top10_brier, 4),
            avg_brier=round(avg_brier, 4),
            win_logloss=round(win_logloss, 4),
            top3_logloss=round(calculate_log_loss(top3_probs, top3_outcomes), 4),
            top1_accuracy=top1_correct,
            top3_accuracy=round(top3_acc, 4),
            top5_accuracy=round(top5_acc, 4),
            kendall_tau=round(kendall_tau, 4),
            avg_position_error=round(avg_pos_error, 2),
            calibration_error=round(cal_error, 4),
        )

    def _generate_summary(self, model_name: str) -> ModelBenchmarkSummary:
        """Generate aggregate summary for a model."""
        metrics_list = self.results.get(model_name, [])
        if not metrics_list:
            return ModelBenchmarkSummary(model_name=model_name, n_races=0)

        n = len(metrics_list)

        avg_win_brier = float(np.mean([m.win_brier for m in metrics_list]))
        avg_top3_brier = float(np.mean([m.top3_brier for m in metrics_list]))
        avg_brier = float(np.mean([m.avg_brier for m in metrics_list]))
        avg_logloss = float(np.mean([m.win_logloss for m in metrics_list]))

        top1_rate = float(np.mean([1.0 if m.top1_accuracy else 0.0 for m in metrics_list]))
        top3_rate = float(np.mean([m.top3_accuracy for m in metrics_list]))
        top5_rate = float(np.mean([m.top5_accuracy for m in metrics_list]))

        avg_kendall = float(np.mean([m.kendall_tau for m in metrics_list]))
        avg_pos_error = float(np.mean([m.avg_position_error for m in metrics_list]))
        avg_cal_error = float(np.mean([m.calibration_error for m in metrics_list]))

        # Calculate performance scores (normalized 0-100)
        brier_perf = max(0, min(100, (1.0 - avg_brier * 4) * 100))
        ranking_perf = max(0, min(100, (avg_kendall + 1) / 2 * 100))
        cal_perf = max(0, min(100, (1.0 - avg_cal_error * 5) * 100))

        overall = (brier_perf * 0.4 + ranking_perf * 0.35 + cal_perf * 0.25)

        return ModelBenchmarkSummary(
            model_name=model_name,
            n_races=n,
            avg_win_brier=round(avg_win_brier, 4),
            avg_top3_brier=round(avg_top3_brier, 4),
            avg_brier=round(avg_brier, 4),
            avg_logloss=round(avg_logloss, 4),
            top1_accuracy_rate=round(top1_rate, 4),
            top3_accuracy_rate=round(top3_rate, 4),
            top5_accuracy_rate=round(top5_rate, 4),
            avg_kendall_tau=round(avg_kendall, 4),
            avg_position_error=round(avg_pos_error, 2),
            avg_calibration_error=round(avg_cal_error, 4),
            overall_score=round(overall, 1),
            brier_score_performance=round(brier_perf, 1),
            ranking_performance=round(ranking_perf, 1),
            calibration_performance=round(cal_perf, 1),
        )

    def _save_results(self, summaries: Dict[str, ModelBenchmarkSummary]):
        """Save benchmark results to disk."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save summaries
        summary_data = {}
        for name, summary in summaries.items():
            summary_data[name] = {
                "model_name": summary.model_name,
                "n_races": summary.n_races,
                "avg_win_brier": summary.avg_win_brier,
                "avg_top3_brier": summary.avg_top3_brier,
                "avg_brier": summary.avg_brier,
                "avg_logloss": summary.avg_logloss,
                "top1_accuracy_rate": summary.top1_accuracy_rate,
                "top3_accuracy_rate": summary.top3_accuracy_rate,
                "top5_accuracy_rate": summary.top5_accuracy_rate,
                "avg_kendall_tau": summary.avg_kendall_tau,
                "avg_position_error": summary.avg_position_error,
                "avg_calibration_error": summary.avg_calibration_error,
                "overall_score": summary.overall_score,
            }

        path = output_dir / f"benchmark_summary_{timestamp}.json"
        with open(path, "w") as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Benchmark summary saved to {path}")

        # Save detailed metrics
        detailed = {}
        for name, metrics_list in self.results.items():
            detailed[name] = [
                {
                    "race_name": m.race_name,
                    "circuit_id": m.circuit_id,
                    "avg_brier": m.avg_brier,
                    "win_brier": m.win_brier,
                    "top3_brier": m.top3_brier,
                    "top1_accuracy": m.top1_accuracy,
                    "top3_accuracy": m.top3_accuracy,
                    "kendall_tau": m.kendall_tau,
                    "avg_position_error": m.avg_position_error,
                }
                for m in metrics_list
            ]

        detailed_path = output_dir / f"benchmark_detailed_{timestamp}.json"
        with open(detailed_path, "w") as f:
            json.dump(detailed, f, indent=2)
        logger.info(f"Detailed results saved to {detailed_path}")

    def compare_models(self) -> Dict[str, Any]:
        """
        Generate model comparison data for dashboard visualization.

        Returns:
            Dict with comparison data including heatmap-ready matrices
        """
        summaries = self.run_all()
        if not summaries:
            return {}

        model_names = list(summaries.keys())
        metrics = ["avg_brier", "top1_accuracy_rate", "top3_accuracy_rate",
                    "avg_kendall_tau", "overall_score"]

        comparison = {
            "models": model_names,
            "metrics": metrics,
            "values": {
                name: {m: getattr(s, m, 0) for m in metrics}
                for name, s in summaries.items()
            },
            "best_model": max(model_names, key=lambda n: summaries[n].overall_score),
            "best_brier": min(model_names, key=lambda n: summaries[n].avg_brier),
            "best_ranking": max(model_names, key=lambda n: summaries[n].avg_kendall_tau),
        }

        return comparison


# ── CLI Helper ──────────────────────────────────────────────────────────────

def run_benchmark(
    seasons: Optional[List[int]] = None,
    n_simulations: int = 10000,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to run a full benchmark.

    Args:
        seasons: List of seasons to benchmark
        n_simulations: Number of MC simulations per race
        verbose: Whether to print progress

    Returns:
        Comparison data with summaries
    """
    config = BenchmarkConfig(
        seasons=seasons or [2022, 2023, 2024, 2025, 2026],
        n_simulations=n_simulations,
        verbose=verbose,
    )
    engine = BenchmarkEngine(config)
    return engine.compare_models()


def quick_benchmark(circuit_id: str = "canada") -> Dict[str, Any]:
    """
    Quick benchmark on a single circuit for testing.

    Args:
        circuit_id: Circuit to benchmark on

    Returns:
        Dict with per-model metrics
    """
    from engine.predictor import predict, PredictionRequest

    results = {}

    # MC only
    mc_result = predict(PredictionRequest(circuit_id=circuit_id, n_simulations=10000, seed=42))
    results["monte_carlo"] = {
        "predictions": [
            {"driver_id": p.get("driver_id"), "win_pct": p.get("win_pct", 0)}
            for p in mc_result["predictions"][:5]
        ],
        "podium": mc_result.get("podium_predictions", []),
    }

    # Try XGBoost
    try:
        from engine.feature_engineering import compute_all_drivers
        from engine.ml_models import get_ml_predictions
        driver_features = compute_all_drivers(circuit_id)
        ml_result = get_ml_predictions(driver_features, circuit_id)
        results["xgboost"] = {
            "predictions": [
                {
                    "driver_id": r.driver_id,
                    "rank_score": round(r.rank_score, 3),
                    "rank": r.rank_position,
                    "pl_win_pct": round(r.pl_win_prob * 100, 1),
                }
                for r in ml_result.rankings[:5]
            ],
            "model_used": ml_result.model_used,
        }
    except Exception as e:
        results["xgboost"] = {"error": str(e)}

    # Try Ensemble
    try:
        from engine.ensemble_predictor import EnsemblePredictor
        from engine.feature_engineering import compute_all_drivers

        driver_features = compute_all_drivers(circuit_id)
        mc_preds = mc_result.get("predictions", [])
        ml_result = results.get("xgboost", {}).get("predictions", [])

        # Need actual RankedDriver objects for ensemble
        from engine.ml_models import get_ml_predictions
        ml_result_full = get_ml_predictions(driver_features, circuit_id)

        ensemble = EnsemblePredictor()
        ensemble_result = ensemble.predict(
            mc_predictions=mc_preds,
            xgb_rankings=ml_result_full.rankings,
            pl_rankings=ml_result_full.rankings,
            composite_scores=driver_features,
            circuit_id=circuit_id,
        )
        results["ensemble"] = {
            "predictions": [
                {
                    "driver_id": p.driver_id,
                    "win_pct": round(p.ensemble_win_prob * 100, 1),
                    "top3_pct": round(p.ensemble_top3_prob * 100, 1),
                    "position": p.ensemble_position,
                    "confidence": p.confidence,
                }
                for p in ensemble_result.predictions[:5]
            ],
            "weights": ensemble_result.model_weights,
            "confidence": ensemble_result.ensemble_confidence,
            "winning_model": ensemble_result.winning_model,
        }
    except Exception as e:
        results["ensemble"] = {"error": str(e)}

    return results


__all__ = [
    "BenchmarkConfig", "BenchmarkEngine",
    "RaceMetrics", "ModelBenchmarkSummary",
    "HistoricalDataLoader", "PredictionRunner",
    "calculate_brier_score", "calculate_log_loss",
    "calculate_kendall_tau", "calculate_calibration_error",
    "run_benchmark", "quick_benchmark",
]

