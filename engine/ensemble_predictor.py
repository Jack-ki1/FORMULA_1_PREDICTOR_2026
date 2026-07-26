"""
Meta-Blender Ensemble Predictor for F1 Race Outcomes.

Combines multiple prediction sources into a calibrated ensemble:
  1. Monte Carlo Simulation (physics/simulation-based)
  2. XGBoost LambdaMART (Learning-to-Rank)
  3. Plackett-Luce Probabilistic Ranking
  4. Composite Score Heuristic (existing engine)

Dynamic weight optimization via Brier Score minimization.
Calibration-aware blending with performance tracking.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)

# Optional scipy dependency
_SCIPY_AVAILABLE = False
try:
    from scipy.optimize import minimize
    _SCIPY_AVAILABLE = True
except ImportError:
    pass

# ── Paths ────────────────────────────────────────────────────────────────────
ENSEMBLE_DIR = Path(__file__).resolve().parents[1] / "models"
ENSEMBLE_DIR.mkdir(parents=True, exist_ok=True)
ENSEMBLE_WEIGHTS_PATH = ENSEMBLE_DIR / "ensemble_weights.json"
ENSEMBLE_PERFORMANCE_PATH = ENSEMBLE_DIR / "ensemble_performance.json"


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class ModelSource:
    """Represents a single model/prediction source."""
    name: str                          # e.g., "monte_carlo", "xgboost", "plackett_luce"
    weight: float = 0.25               # Weight in ensemble (sum = 1.0)
    brier_score: float = float('inf')  # Historical Brier score (lower = better)
    n_evaluations: int = 0             # Number of times evaluated
    calibration_error: float = 0.0     # Mean calibration error
    enabled: bool = True               # Whether to include in ensemble


@dataclass
class EnsemblePrediction:
    """Single driver prediction from the ensemble."""
    driver_id: str
    driver_name: str
    team: str
    ensemble_win_prob: float
    ensemble_top3_prob: float
    ensemble_top10_prob: float
    ensemble_dnf_prob: float
    ensemble_position: int
    model_breakdown: Dict[str, float]  # Per-model win prob
    confidence: str                    # high/medium/low
    brier_weighted_score: float        # Weighted ensemble score


@dataclass
class EnsembleResult:
    """Full ensemble prediction result for a race."""
    predictions: List[EnsemblePrediction]
    model_weights: Dict[str, float]
    ensemble_confidence: float
    calibration_score: float
    num_sources: int
    winning_model: str                  # Best performing model for this race


# ── Performance Tracker ──────────────────────────────────────────────────────

class PerformanceTracker:
    """Tracks historical performance of each model source."""

    def __init__(self):
        self.history: Dict[str, List[Dict]] = defaultdict(list)
        self._load()

    def record_evaluation(
        self,
        model_name: str,
        predicted_probs: Dict[str, float],
        actual_outcome: int,
    ):
        """
        Record a prediction evaluation.

        Args:
            model_name: Source model name
            predicted_probs: Dict of driver_id -> predicted probability
            actual_outcome: 1 if event occurred, 0 otherwise
        """
        self.history[model_name].append({
            "predicted": predicted_probs,
            "actual": actual_outcome,
        })

    def get_brier_score(self, model_name: str) -> float:
        """Calculate Brier score from history."""
        records = self.history.get(model_name, [])
        if not records:
            return float('inf')
        scores = [
            (r["predicted"].get("win", 0) - r["actual"]) ** 2
            for r in records
        ]
        return np.mean(scores) if scores else float('inf')

    def get_calibration_error(self, model_name: str, n_bins: int = 10) -> float:
        """Calculate mean calibration error."""
        records = self.history.get(model_name, [])
        if len(records) < 10:
            return 0.0

        probs = [r["predicted"].get("win", 0) for r in records]
        outcomes = [r["actual"] for r in records]

        bins = [[] for _ in range(n_bins)]
        for p, o in zip(probs, outcomes):
            idx = min(int(p * n_bins), n_bins - 1)
            bins[idx].append((p, o))

        errors = []
        for b in bins:
            if len(b) < 2:
                continue
            mean_pred = np.mean([p for p, _ in b])
            actual_rate = np.mean([o for _, o in b])
            errors.append(abs(mean_pred - actual_rate))

        return np.mean(errors) if errors else 0.0

    def get_model_rankings(self) -> List[Tuple[str, float]]:
        """Rank models by Brier score (lower is better)."""
        scores = []
        for model_name in self.history:
            brier = self.get_brier_score(model_name)
            if brier < float('inf'):
                scores.append((model_name, brier))
        scores.sort(key=lambda x: x[1])
        return scores

    def save(self):
        """Save performance history to disk."""
        try:
            data = {k: v for k, v in self.history.items()}
            with open(ENSEMBLE_PERFORMANCE_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save performance history: {e}")

    def _load(self):
        """Load performance history from disk."""
        try:
            if ENSEMBLE_PERFORMANCE_PATH.exists():
                with open(ENSEMBLE_PERFORMANCE_PATH) as f:
                    data = json.load(f)
                self.history = defaultdict(list, data)
        except Exception as e:
            logger.warning(f"Failed to load performance history: {e}")


# ── Weight Optimizer ─────────────────────────────────────────────────────────

class WeightOptimizer:
    """Optimizes ensemble weights based on historical Brier scores."""

    def __init__(self):
        self.tracker = PerformanceTracker()

    def optimize_weights(
        self,
        model_names: List[str],
        method: str = "brier_inverse",
    ) -> Dict[str, float]:
        """
        Compute optimal weights for each model.

        Methods:
            - "brier_inverse": Weight inversely proportional to Brier score
            - "brier_softmax": Softmax over negative Brier scores
            - "equal": Equal weights (fallback)

        Args:
            model_names: List of model source names
            method: Weighting method

        Returns:
            Dict of model_name -> weight
        """
        if method == "brier_inverse":
            return self._brier_inverse_weights(model_names)
        elif method == "brier_softmax":
            return self._brier_softmax_weights(model_names)
        else:
            return {name: 1.0 / len(model_names) for name in model_names}

    def _brier_inverse_weights(self, model_names: List[str]) -> Dict[str, float]:
        """Weight = 1/Brier, normalized to sum to 1.0."""
        brier_scores = {}
        for name in model_names:
            brier = self.tracker.get_brier_score(name)
            if brier < float('inf') and brier > 0:
                brier_scores[name] = 1.0 / brier
            else:
                brier_scores[name] = 1.0  # Default for unevaluated models

        total = sum(brier_scores.values())
        if total == 0:
            return {name: 1.0 / len(model_names) for name in model_names}

        return {name: score / total for name, score in brier_scores.items()}

    def _brier_softmax_weights(self, model_names: List[str]) -> Dict[str, float]:
        """Softmax over negative Brier scores for smoother weighting."""
        brier_scores = []
        for name in model_names:
            brier = self.tracker.get_brier_score(name)
            brier_scores.append(-brier if brier < float('inf') else -1.0)

        # Temperature-scaled softmax
        brier_scores = np.array(brier_scores)
        temperature = 0.5
        exp_scores = np.exp(brier_scores / temperature)
        weights = exp_scores / np.sum(exp_scores)

        return {name: float(w) for name, w in zip(model_names, weights)}

    def dynamic_weight_update(
        self,
        model_names: List[str],
        min_weight: float = 0.05,
    ) -> Dict[str, float]:
        """
        Dynamically update weights based on performance.

        Args:
            model_names: Model source names
            min_weight: Minimum weight for any model

        Returns:
            Updated weights dict
        """
        weights = self.optimize_weights(model_names)

        # Ensure minimum weight
        total_min = min_weight * len(model_names)
        if total_min > 1.0:
            min_weight = 1.0 / len(model_names)

        for name in weights:
            if weights[name] < min_weight:
                weights[name] = min_weight

        # Renormalize
        total = sum(weights.values())
        return {name: w / total for name, w in weights.items()}


# ── Ensemble Predictor ───────────────────────────────────────────────────────

class EnsemblePredictor:
    """
    Meta-Blender Ensemble combining multiple prediction sources.

    Integrates:
    1. Monte Carlo simulation probabilities
    2. XGBoost LambdaMART rankings
    3. Plackett-Luce probabilistic rankings
    4. Composite score heuristics

    Uses dynamic weighting based on historical Brier scores.
    """

    SOURCE_NAMES = [
        "monte_carlo",
        "xgboost",
        "plackett_luce",
        "composite",
    ]

    def __init__(self):
        self.sources: Dict[str, ModelSource] = {}
        self.weight_optimizer = WeightOptimizer()
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize model sources with default weights."""
        for name in self.SOURCE_NAMES:
            self.sources[name] = ModelSource(
                name=name,
                weight=1.0 / len(self.SOURCE_NAMES),
                brier_score=self.weight_optimizer.tracker.get_brier_score(name),
                n_evaluations=len(self.weight_optimizer.tracker.history.get(name, [])),
            )

        # Load saved weights if available
        self._load_weights()

    def update_weights(self):
        """Dynamically update weights based on tracked performance."""
        active_sources = [
            name for name, source in self.sources.items()
            if source.enabled
        ]
        updated = self.weight_optimizer.dynamic_weight_update(active_sources)

        for name, weight in updated.items():
            if name in self.sources:
                self.sources[name].weight = weight

        self._save_weights()
        logger.info(f"Ensemble weights updated: {updated}")

    def set_manual_weights(self, weights: Dict[str, float]):
        """Override weights manually."""
        for name, weight in weights.items():
            if name in self.sources:
                self.sources[name].weight = weight
                self.sources[name].enabled = weight > 0
        self._save_weights()

    def predict(
        self,
        mc_predictions: List[Dict],
        xgb_rankings: Optional[List] = None,
        pl_rankings: Optional[List] = None,
        composite_scores: Optional[List[Dict]] = None,
        circuit_id: str = "",
    ) -> EnsembleResult:
        """
        Generate ensemble prediction for a race.

        Args:
            mc_predictions: Monte Carlo simulation predictions
            xgb_rankings: XGBoost rankings (optional)
            pl_rankings: Plackett-Luce rankings (optional)
            composite_scores: Composite score outputs (optional)
            circuit_id: Circuit identifier

        Returns:
            EnsembleResult with blended predictions
        """
        # Update weights from historical performance
        self.update_weights()

        # Extract per-driver probabilities from each source
        driver_data = self._extract_driver_data(mc_predictions)

        # Build source probabilities
        source_probs: Dict[str, Dict[str, Dict[str, float]]] = {}

        # 1. Monte Carlo
        source_probs["monte_carlo"] = self._mc_to_probs(mc_predictions)

        # 2. XGBoost (if available)
        if xgb_rankings:
            source_probs["xgboost"] = self._xgb_to_probs(xgb_rankings)
        else:
            self.sources["xgboost"].enabled = False

        # 3. Plackett-Luce (if available)
        if pl_rankings:
            source_probs["plackett_luce"] = self._pl_to_probs(pl_rankings)
        else:
            self.sources["plackett_luce"].enabled = False

        # 4. Composite heuristic
        source_probs["composite"] = self._composite_to_probs(composite_scores or mc_predictions)

        # Blend probabilities
        ensemble_predictions = self._blend_predictions(driver_data, source_probs)

        # Determine winning model
        winning_model = self._find_winning_model(source_probs, ensemble_predictions)

        return EnsembleResult(
            predictions=ensemble_predictions,
            model_weights={name: s.weight for name, s in self.sources.items() if s.enabled},
            ensemble_confidence=self._calculate_ensemble_confidence(ensemble_predictions),
            calibration_score=self._calculate_calibration_score(),
            num_sources=sum(1 for s in self.sources.values() if s.enabled),
            winning_model=winning_model,
        )

    def _extract_driver_data(self, mc_predictions: List[Dict]) -> Dict[str, Dict]:
        """Extract driver metadata from MC predictions."""
        data = {}
        for p in mc_predictions:
            did = p.get("driver_id", p.get("driver", ""))
            data[did] = {
                "driver_name": p.get("driver_name", p.get("driver", did)),
                "team": p.get("team", "unknown"),
            }
        return data

    def _mc_to_probs(self, predictions: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Extract probabilities from MC predictions."""
        probs = {}
        for p in predictions:
            did = p.get("driver_id", p.get("driver", ""))
            probs[did] = {
                "win": p.get("win_probability", p.get("win_pct", 0) / 100.0),
                "top3": p.get("top3_probability", p.get("top3_pct", 0) / 100.0),
                "top10": p.get("top10_probability", p.get("top10_pct", 0) / 100.0),
                "dnf": p.get("dnf_probability", p.get("dnf_pct", 0) / 100.0),
            }
        return probs

    def _xgb_to_probs(self, rankings: List) -> Dict[str, Dict[str, float]]:
        """Convert XGBoost rankings to probabilities via softmax."""
        scores = {r.driver_id: r.rank_score for r in rankings}
        return self._scores_to_probs(scores)

    def _pl_to_probs(self, rankings: List) -> Dict[str, Dict[str, float]]:
        """Extract probabilities from Plackett-Luce rankings."""
        probs = {}
        for r in rankings:
            probs[r.driver_id] = {
                "win": r.pl_win_prob,
                "top3": r.pl_top3_prob,
                "top10": r.pl_top10_prob,
                "dnf": 0.0,
            }
        return probs

    def _composite_to_probs(self, scores: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Convert composite scores to probabilities."""
        score_dict = {d["driver_id"]: d["composite_score"] for d in scores}
        return self._scores_to_probs(score_dict)

    def _scores_to_probs(self, scores: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Convert arbitrary scores to probabilities via softmax."""
        if not scores:
            return {}

        driver_ids = list(scores.keys())
        values = np.array([scores[did] for did in driver_ids])

        # Temperature-scaled softmax for win probability
        temperature = 0.28
        win_probs = self._softmax(values / temperature)

        # Top-3 and Top-10 cumulative from softmax
        sorted_indices = np.argsort(-values)
        sorted_probs = win_probs[sorted_indices]
        cum_probs = np.cumsum(sorted_probs)

        top3_probs = np.zeros_like(cum_probs)
        top3_probs[sorted_indices] = np.minimum(cum_probs / 3.0, 1.0)

        top10_probs = np.zeros_like(cum_probs)
        top10_probs[sorted_indices] = np.minimum(cum_probs, 1.0)

        result = {}
        for i, did in enumerate(driver_ids):
            result[did] = {
                "win": float(win_probs[i]),
                "top3": float(top3_probs[i]),
                "top10": float(top10_probs[i]),
                "dnf": 0.0,
            }
        return result

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Numerically stable softmax."""
        x_max = np.max(x)
        exp_x = np.exp(x - x_max)
        return exp_x / np.sum(exp_x)

    def _blend_predictions(
        self,
        driver_data: Dict[str, Dict],
        source_probs: Dict[str, Dict[str, Dict[str, float]]],
    ) -> List[EnsemblePrediction]:
        """Blend probabilities from all active sources."""
        active_sources = [
            (name, self.sources[name])
            for name in self.SOURCE_NAMES
            if name in source_probs and self.sources.get(name, ModelSource(name)).enabled
        ]

        if not active_sources:
            logger.warning("No active sources for ensemble blending")
            return self._default_predictions(driver_data)

        # Normalize weights
        total_weight = sum(s.weight for _, s in active_sources)
        if total_weight == 0:
            total_weight = 1.0

        predictions = []
        for did, meta in driver_data.items():
            blended_win = 0.0
            blended_top3 = 0.0
            blended_top10 = 0.0
            blended_dnf = 0.0
            model_breakdown = {}

            for source_name, source in active_sources:
                if did in source_probs[source_name]:
                    probs = source_probs[source_name][did]
                    weight = source.weight / total_weight

                    blended_win += weight * probs.get("win", 0.0)
                    blended_top3 += weight * probs.get("top3", 0.0)
                    blended_top10 += weight * probs.get("top10", 0.0)
                    blended_dnf += weight * probs.get("dnf", 0.0)
                    model_breakdown[source_name] = probs.get("win", 0.0)

            # Enforce hierarchy: win <= top3 <= top10
            blended_win = min(blended_win, blended_top3)
            blended_top3 = min(blended_top3, blended_top10)

            # Brier-weighted composite score for tiebreaking
            brier_weighted = blended_win * 0.5 + blended_top3 * 0.3 + blended_top10 * 0.2

            confidence = self._assign_confidence(blended_win)

            predictions.append(EnsemblePrediction(
                driver_id=did,
                driver_name=meta.get("driver_name", did),
                team=meta.get("team", "unknown"),
                ensemble_win_prob=round(blended_win, 4),
                ensemble_top3_prob=round(blended_top3, 4),
                ensemble_top10_prob=round(blended_top10, 4),
                ensemble_dnf_prob=round(blended_dnf, 4),
                ensemble_position=0,  # Will set after sorting
                model_breakdown=model_breakdown,
                confidence=confidence,
                brier_weighted_score=round(brier_weighted, 4),
            ))

        # Sort by brier-weighted score descending
        predictions.sort(key=lambda p: p.brier_weighted_score, reverse=True)
        for pos, p in enumerate(predictions, start=1):
            p.ensemble_position = pos

        return predictions

    def _assign_confidence(self, win_prob: float) -> str:
        """Assign confidence level based on blended win probability."""
        if win_prob > 0.25:
            return "high"
        elif win_prob > 0.05:
            return "medium"
        else:
            return "low"

    def _default_predictions(self, driver_data: Dict[str, Dict]) -> List[EnsemblePrediction]:
        """Return default predictions when no sources are available."""
        n = len(driver_data)
        if n == 0:
            return []
        equal_prob = 1.0 / n
        predictions = []
        for i, (did, meta) in enumerate(driver_data.items(), start=1):
            predictions.append(EnsemblePrediction(
                driver_id=did,
                driver_name=meta.get("driver_name", did),
                team=meta.get("team", "unknown"),
                ensemble_win_prob=equal_prob,
                ensemble_top3_prob=equal_prob * 3,
                ensemble_top10_prob=equal_prob * 10,
                ensemble_dnf_prob=0.15,
                ensemble_position=i,
                model_breakdown={},
                confidence="low",
                brier_weighted_score=equal_prob,
            ))
        return predictions

    def _calculate_ensemble_confidence(self, predictions: List[EnsemblePrediction]) -> float:
        """Calculate overall ensemble confidence (0-1)."""
        if not predictions:
            return 0.0

        # Confidence = weighted by top-3 separation
        top3_scores = [p.ensemble_win_prob for p in predictions[:3]]
        if not top3_scores:
            return 0.0

        # Higher separation between top 3 = more confident
        max_score = max(top3_scores)
        min_score = min(top3_scores) if len(top3_scores) > 1 else 0
        separation = max_score - min_score

        # Blend with number of active sources
        n_sources = sum(1 for s in self.sources.values() if s.enabled)
        source_factor = min(1.0, n_sources / 4.0)

        return round(0.5 + separation * 0.3 + source_factor * 0.2, 3)

    def _calculate_calibration_score(self) -> float:
        """Calculate overall calibration score across all models."""
        scores = []
        for name in self.SOURCE_NAMES:
            cal = self.weight_optimizer.tracker.get_calibration_error(name)
            if cal > 0:
                scores.append(1.0 - min(cal, 0.5) * 2)  # Map to [0, 1]

        return np.mean(scores) if scores else 0.5

    def _find_winning_model(
        self,
        source_probs: Dict[str, Dict[str, Dict[str, float]]],
        ensemble_preds: List[EnsemblePrediction],
    ) -> str:
        """Determine which model performed best (lowest Brier)."""
        if not ensemble_preds:
            return "none"

        brier_scores = {}
        for source_name in source_probs:
            if source_name not in self.sources or not self.sources[source_name].enabled:
                continue
            brier = self.weight_optimizer.tracker.get_brier_score(source_name)
            if brier < float('inf'):
                brier_scores[source_name] = brier

        if brier_scores:
            return min(brier_scores, key=brier_scores.get)

        # Fallback: model with highest weight
        active = {n: s.weight for n, s in self.sources.items() if s.enabled}
        return max(active, key=active.get) if active else "monte_carlo"

    def to_dict(self, result: EnsembleResult) -> Dict:
        """Convert EnsembleResult to serializable dict."""
        return {
            "predictions": [
                {
                    "driver_id": p.driver_id,
                    "driver_name": p.driver_name,
                    "team": p.team,
                    "ensemble_win_pct": round(p.ensemble_win_prob * 100, 1),
                    "ensemble_top3_pct": round(p.ensemble_top3_prob * 100, 1),
                    "ensemble_top10_pct": round(p.ensemble_top10_prob * 100, 1),
                    "ensemble_dnf_pct": round(p.ensemble_dnf_prob * 100, 1),
                    "ensemble_position": p.ensemble_position,
                    "model_breakdown": p.model_breakdown,
                    "confidence": p.confidence,
                }
                for p in result.predictions
            ],
            "model_weights": result.model_weights,
            "ensemble_confidence": result.ensemble_confidence,
            "calibration_score": result.calibration_score,
            "num_sources": result.num_sources,
            "winning_model": result.winning_model,
        }

    def _save_weights(self):
        """Save current weights to disk."""
        try:
            data = {
                name: {
                    "weight": source.weight,
                    "brier_score": source.brier_score,
                    "n_evaluations": source.n_evaluations,
                    "enabled": source.enabled,
                }
                for name, source in self.sources.items()
            }
            with open(ENSEMBLE_WEIGHTS_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save ensemble weights: {e}")

    def _load_weights(self):
        """Load saved weights from disk."""
        try:
            if ENSEMBLE_WEIGHTS_PATH.exists():
                with open(ENSEMBLE_WEIGHTS_PATH) as f:
                    data = json.load(f)
                for name, source_data in data.items():
                    if name in self.sources:
                        self.sources[name].weight = source_data.get("weight", 0.25)
                        self.sources[name].brier_score = source_data.get("brier_score", float('inf'))
                        self.sources[name].n_evaluations = source_data.get("n_evaluations", 0)
                        self.sources[name].enabled = source_data.get("enabled", True)
        except Exception as e:
            logger.warning(f"Failed to load ensemble weights: {e}")


# ── Convenience function ─────────────────────────────────────────────────────

def get_ensemble_predictor() -> EnsemblePredictor:
    """Get or create an EnsemblePredictor singleton."""
    return EnsemblePredictor()


__all__ = [
    "EnsemblePredictor",
    "EnsemblePrediction",
    "EnsembleResult",
    "ModelSource",
    "PerformanceTracker",
    "WeightOptimizer",
    "get_ensemble_predictor",
]

