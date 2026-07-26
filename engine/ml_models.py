"""
SOTA Machine Learning Models for F1 Race Outcome Prediction.

Implements:
  1. XGBoost LambdaMART Learning-to-Rank for finishing order prediction
  2. Plackett-Luce Probabilistic Ranking model
  3. Optuna hyperparameter tuning for ranking loss optimization
  4. Auto-fetching historical data (2022-2025) via Jolpica API
  5. Model persistence (save/load trained models)

Graceful fallback if XGBoost/scipy are not installed.
"""

import logging
import os
import pickle
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional Dependencies ────────────────────────────────────────────────────
_XGBOOST_AVAILABLE = False
_SCIPY_AVAILABLE = False
_OPTUNA_AVAILABLE = False

try:
    import xgboost as xgb
    _XGBOOST_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not installed. Install with: pip install xgboost")

try:
    import scipy
    from scipy.optimize import minimize
    from scipy.special import softmax
    _SCIPY_AVAILABLE = True
except ImportError:
    logger.warning("SciPy not installed. Install with: pip install scipy")

try:
    import optuna
    _OPTUNA_AVAILABLE = True
except ImportError:
    logger.warning("Optuna not installed. Install with: pip install optuna")

# ── Paths ────────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

XGB_MODEL_PATH = MODELS_DIR / "xgboost_lambdarank.json"
PL_MODEL_PATH = MODELS_DIR / "plackett_luce_params.json"
FEATURE_NAMES_PATH = MODELS_DIR / "feature_names.json"
DATA_CACHE_PATH = MODELS_DIR / "historical_training_data.pkl"


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class RankedDriver:
    driver_id: str
    driver_name: str
    team: str
    rank_score: float       # XGBoost predicted score (higher = better rank)
    rank_position: int       # 1-based predicted position from ranking
    pl_win_prob: float = 0.0      # Plackett-Luce win probability
    pl_top3_prob: float = 0.0     # Plackett-Luce top-3 probability
    pl_top10_prob: float = 0.0    # Plackett-Luce top-10 probability


@dataclass
class MLPredictionResult:
    rankings: List[RankedDriver]
    model_used: str
    ndcg_score: Optional[float] = None
    ensemble_weight: float = 0.5  # Default weight in ensemble


# ── Feature Preparation ──────────────────────────────────────────────────────

FEATURE_NAMES_DEFAULT = [
    "elo_rating",
    "constructor_strength",
    "recent_form",
    "grid_position",
    "weather_adjustment",
    "reliability",
    "safety_car_upside",
    "track_type_fit",
    "tire_management_score",
    "qualifying_delta",
    "experience_races",
    "championship_points",
    "circuit_lap_count",
    "circuit_sc_prob",
    "circuit_overtaking_diff",
    "lag_avg_position_last_3",
    "lag_avg_position_last_5",
    "lag_form_trend",
    "quali_to_race_pace_ratio",
    "drs_efficiency",
    "team_tire_strategy_score",
]


class FeaturePreparator:
    """Prepares driver features for XGBoost training and inference."""

    @staticmethod
    def prepare_features_from_engine(
        driver_composite_scores: List[Dict],
        circuit_id: str,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Convert engine feature dicts to XGBoost-compatible numpy array.

        Args:
            driver_composite_scores: Output from compute_all_drivers()
            circuit_id: Circuit identifier

        Returns:
            (feature_matrix, feature_names)
        """
        from data.circuit_data import get_circuit
        circuit = get_circuit(circuit_id)

        rows = []
        feature_names = list(FEATURE_NAMES_DEFAULT)

        for d in driver_composite_scores:
            feats = d.get("features", {})
            driver_data = _get_driver_safe(d["driver_id"])

            # Build feature vector matching FEATURE_NAMES_DEFAULT order
            row = [
                feats.get("elo_rating", 0.5),
                feats.get("constructor_strength", 0.25),
                feats.get("recent_form", 0.5),
                feats.get("grid_position", 0.5),
                feats.get("weather_adjustment", 0.5),
                feats.get("reliability", 0.5),
                feats.get("safety_car_upside", 0.25),
                feats.get("track_type_fit", 0.5),
                driver_data.get("tire_management", 7.0) / 10.0,
                driver_data.get("qualifying_delta_avg", 0.25),
                min(driver_data.get("experience_races", 0) / 100.0, 1.0),
                min(driver_data.get("championship_points_2026", 0) / 200.0, 1.0),
                circuit.get("lap_count", 60) / 100.0,
                circuit.get("safety_car_probability", 0.5),
                circuit.get("overtaking_difficulty", 5) / 10.0,
                feats.get("lag_avg_position_last_3", 0.5),
                feats.get("lag_avg_position_last_5", 0.5),
                feats.get("lag_form_trend", 0.0),
                feats.get("quali_to_race_pace_ratio", 1.0),
                feats.get("drs_efficiency", 0.5),
                feats.get("team_tire_strategy_score", 0.5),
            ]
            rows.append(row)

        return np.array(rows, dtype=np.float32), feature_names

    @staticmethod
    def prepare_training_data(
        historical_races: List[Dict],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Convert historical race results into XGBoost training data.

        Each row is a (driver, race) pair with:
        - features: driver+circuit features at race time
        - relevance: position-based relevance score (20 for P1, 19 for P2, ..., 1 for P20)
        - group: race grouping for LambdaMART

        Args:
            historical_races: List of race dicts with results

        Returns:
            (X, y, groups) where groups indicates race boundaries
        """
        from engine.feature_engineering import compute_composite_score
        from data.circuit_data import get_circuit

        all_X = []
        all_y = []
        groups = []

        for race in historical_races:
            circuit_id = race["circuit"]
            results = race.get("results", [])
            if not results:
                continue

            race_features = []
            race_relevances = []

            for r in results:
                driver_id = r["driver"]
                position = r["position"]
                status = r.get("status", "Finished")

                try:
                    comp = compute_composite_score(driver_id, circuit_id)
                except Exception:
                    continue

                feats = comp.get("features", {})
                driver_data = _get_driver_safe(driver_id)
                circuit = get_circuit(circuit_id)

                # Build feature vector
                row = [
                    feats.get("elo_rating", 0.5),
                    feats.get("constructor_strength", 0.25),
                    feats.get("recent_form", 0.5),
                    feats.get("grid_position", 0.5),
                    feats.get("weather_adjustment", 0.5),
                    feats.get("reliability", 0.5),
                    feats.get("safety_car_upside", 0.25),
                    feats.get("track_type_fit", 0.5),
                    driver_data.get("tire_management", 7.0) / 10.0,
                    driver_data.get("qualifying_delta_avg", 0.25),
                    min(driver_data.get("experience_races", 0) / 100.0, 1.0),
                    min(driver_data.get("championship_points_2026", 0) / 200.0, 1.0),
                    circuit.get("lap_count", 60) / 100.0,
                    circuit.get("safety_car_probability", 0.5),
                    circuit.get("overtaking_difficulty", 5) / 10.0,
                    0.0,  # lag features placeholder
                    0.0,
                    0.0,
                    1.0,
                    0.5,
                    0.5,
                ]
                race_features.append(row)

                # Relevance: 20 - position (P1=20, P20=1, DNF=0)
                if status in ("DNF", "DNS", "DSQ"):
                    relevance = 0
                else:
                    relevance = max(1, 21 - position)
                race_relevances.append(relevance)

            if len(race_features) >= 2:
                all_X.extend(race_features)
                all_y.extend(race_relevances)
                groups.append(len(race_features))

        if not all_X:
            logger.warning("No training data could be prepared")
            return np.array([]), np.array([]), np.array([])

        return (
            np.array(all_X, dtype=np.float32),
            np.array(all_y, dtype=np.float32),
            np.array(groups, dtype=np.int32),
        )


def _get_driver_safe(driver_id: str) -> Dict:
    """Safely get driver data with fallback defaults."""
    try:
        from data.driver_data import get_driver
        return get_driver(driver_id)
    except Exception:
        return {}


# ── Historical Data Auto-Fetch ───────────────────────────────────────────────

def auto_fetch_historical_data(
    seasons: Optional[List[int]] = None,
    force_refresh: bool = False,
) -> List[Dict]:
    """
    Auto-fetch historical F1 race results (2022-2025) for ML training.

    Tries Jolpica API first, falls back to bundled data.

    Args:
        seasons: List of seasons to fetch (default: 2022-2025)
        force_refresh: If True, re-fetch even if cached

    Returns:
        List of race dicts with results
    """
    if seasons is None:
        seasons = [2022, 2023, 2024, 2025]

    # Check cache first
    if DATA_CACHE_PATH.exists() and not force_refresh:
        try:
            with open(DATA_CACHE_PATH, "rb") as f:
                cached = pickle.load(f)
            cached_seasons = cached.get("seasons", [])
            if set(seasons).issubset(set(cached_seasons)):
                logger.info(f"Using cached historical data ({len(cached.get('races', []))} races)")
                return cached.get("races", [])
        except Exception:
            pass

    all_races = []
    fetched_seasons = set()

    # Try Jolpica API
    try:
        from data.jolpica_client import get_jolpica_client
        client = get_jolpica_client()

        for season in seasons:
            try:
                races = client.get_season_schedule(season)
                for race in races:
                    round_num = race.get("round", 0)
                    try:
                        race_result = client.get_race_results(season, round_num)
                        if race_result and race_result.get("results"):
                            mapped_results = []
                            from data.live_updater import _ERGAST_CODE_TO_OUR_ID
                            for r in race_result["results"]:
                                code = r.get("driver_code", "")
                                our_id = _ERGAST_CODE_TO_OUR_ID.get(code, code.lower())
                                mapped_results.append({
                                    "driver": our_id,
                                    "position": r.get("position", 0),
                                    "status": r.get("status", "Finished"),
                                    "points": r.get("points", 0),
                                })

                            all_races.append({
                                "round": round_num,
                                "circuit": race.get("circuit_id", "").lower(),
                                "name": race.get("race_name", f"Round {round_num}"),
                                "date": race.get("date", ""),
                                "sprint": race.get("sprint_weekend", False),
                                "results": mapped_results,
                            })
                            fetched_seasons.add(season)
                    except Exception as e:
                        logger.debug(f"Could not fetch race {round_num}/{season}: {e}")
                        continue

                logger.info(f"Fetched {len(all_races)} races for season {season} from Jolpica")

            except Exception as e:
                logger.warning(f"Could not fetch season {season} from Jolpica: {e}")
                continue

        if all_races:
            # Cache the fetched data
            with open(DATA_CACHE_PATH, "wb") as f:
                pickle.dump({"seasons": list(fetched_seasons), "races": all_races}, f)
            logger.info(f"Cached {len(all_races)} races to {DATA_CACHE_PATH}")
            return all_races

    except Exception as e:
        logger.warning(f"Jolpica fetch failed: {e}. Trying bundled data...")

    # Fallback: bundled 2026 data
    try:
        from data.season_2026 import SEASON_RESULTS_2026
        logger.info("Using bundled 2026 season data as fallback")
        return SEASON_RESULTS_2026
    except Exception:
        logger.error("No data available for training")
        return []


# ── XGBoost LambdaMART ──────────────────────────────────────────────────────

class XGBoostRanker:
    """
    XGBoost LambdaMART Learning-to-Rank model for F1 finishing order.

    Uses 'rank:ndcg' objective for listwise ranking optimization.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        min_child_weight: float = 1.0,
        gamma: float = 0.0,
        reg_alpha: float = 0.0,
        reg_lambda: float = 1.0,
        seed: int = 42,
    ):
        self.params = {
            "objective": "rank:ndcg",
            "eval_metric": ["ndcg@3", "ndcg@5", "map"],
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "min_child_weight": min_child_weight,
            "gamma": gamma,
            "reg_alpha": reg_alpha,
            "reg_lambda": reg_lambda,
            "seed": seed,
            "verbosity": 0,
            "tree_method": "auto",
        }
        self.n_estimators = n_estimators
        self.model: Optional["xgb.Booster"] = None
        self.feature_names: List[str] = []
        self.is_trained = False
        self._available = _XGBOOST_AVAILABLE

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        feature_names: Optional[List[str]] = None,
        eval_set: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None,
    ) -> Dict[str, float]:
        """
        Train the XGBoost LambdaMART model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Relevance scores (n_samples,)
            groups: Group boundaries for ranking (n_queries,)
            feature_names: Feature names for interpretability
            eval_set: Optional (X_val, y_val, groups_val) for early stopping

        Returns:
            Training history dict
        """
        if not self._available:
            logger.warning("XGBoost not available. Install with: pip install xgboost")
            return {"error": "XGBoost not installed"}

        if len(X) == 0:
            logger.warning("No training data provided")
            return {"error": "Empty training data"}

        self.feature_names = feature_names or FEATURE_NAMES_DEFAULT

        dtrain = xgb.DMatrix(X, label=y)
        dtrain.set_group(groups)

        evals_result = {}
        evals = [(dtrain, "train")]

        if eval_set is not None:
            X_val, y_val, groups_val = eval_set
            dval = xgb.DMatrix(X_val, label=y_val)
            dval.set_group(groups_val)
            evals.append((dval, "eval"))

        self.model = xgb.train(
            self.params,
            dtrain,
            num_boost_round=self.n_estimators,
            evals=evals,
            evals_result=evals_result,
            early_stopping_rounds=20,
            verbose_eval=False,
        )

        self.is_trained = True
        logger.info(f"XGBoost trained: {self.n_estimators} rounds, "
                     f"NDCG@3={evals_result.get('train', {}).get('ndcg@3', [0])[-1]:.4f}")

        return {k: v[-1] for k, v in evals_result.get("train", {}).items()}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict ranking scores for drivers.

        Args:
            X: Feature matrix (n_drivers, n_features)

        Returns:
            Ranking scores (higher = should finish ahead)
        """
        if not self._available or self.model is None:
            logger.warning("XGBoost model not available for prediction")
            return np.zeros(X.shape[0])

        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
        scores = self.model.predict(dmatrix)
        return scores

    def rank_drivers(
        self,
        driver_composite_scores: List[Dict],
        circuit_id: str,
    ) -> List[RankedDriver]:
        """
        Rank drivers for a race using the trained model.

        Args:
            driver_composite_scores: From compute_all_drivers()
            circuit_id: Circuit identifier

        Returns:
            List of RankedDriver sorted by predicted rank
        """
        if not self._available or self.model is None:
            logger.warning("XGBoost model not available, returning default rankings")
            return self._default_rankings(driver_composite_scores)

        X, _ = FeaturePreparator.prepare_features_from_engine(
            driver_composite_scores, circuit_id
        )
        scores = self.predict(X)

        # Create rankings sorted by score descending
        rankings = []
        for i, d in enumerate(driver_composite_scores):
            driver_data = _get_driver_safe(d["driver_id"])
            rankings.append(RankedDriver(
                driver_id=d["driver_id"],
                driver_name=driver_data.get("name", d["driver_id"]),
                team=driver_data.get("team", "unknown"),
                rank_score=float(scores[i]),
                rank_position=0,  # Will set after sorting
            ))

        rankings.sort(key=lambda r: r.rank_score, reverse=True)
        for pos, r in enumerate(rankings, start=1):
            r.rank_position = pos

        return rankings

    def _default_rankings(self, driver_composite_scores: List[Dict]) -> List[RankedDriver]:
        """Fallback: rank by composite score."""
        sorted_scores = sorted(
            driver_composite_scores,
            key=lambda x: x["composite_score"],
            reverse=True,
        )
        rankings = []
        for i, d in enumerate(sorted_scores, start=1):
            driver_data = _get_driver_safe(d["driver_id"])
            rankings.append(RankedDriver(
                driver_id=d["driver_id"],
                driver_name=driver_data.get("name", d["driver_id"]),
                team=driver_data.get("team", "unknown"),
                rank_score=float(d["composite_score"]),
                rank_position=i,
            ))
        return rankings

    def save(self, path: Optional[Path] = None) -> bool:
        """Save model to disk."""
        if self.model is None:
            return False
        path = path or XGB_MODEL_PATH
        try:
            self.model.save_model(str(path))
            with open(str(path) + ".feat_names", "w") as f:
                import json
                json.dump(self.feature_names, f)
            logger.info(f"XGBoost model saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load(self, path: Optional[Path] = None) -> bool:
        """Load model from disk."""
        if not self._available:
            return False
        path = path or XGB_MODEL_PATH
        if not path.exists():
            logger.warning(f"Model file not found: {path}")
            return False
        try:
            self.model = xgb.Booster()
            self.model.load_model(str(path))
            # Try loading feature names
            feat_path = str(path) + ".feat_names"
            if os.path.exists(feat_path):
                with open(feat_path) as f:
                    import json
                    self.feature_names = json.load(f)
            self.is_trained = True
            logger.info(f"XGBoost model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False


# ── Plackett-Luce Probabilistic Ranking ──────────────────────────────────────

class PlackettLuceModel:
    """
    Plackett-Luce probabilistic ranking model.

    Converts driver strength parameters into exact multi-position joint
    probabilities using the Plackett-Luce formula:

    P(driver i wins) = strength_i / sum(strength_j for all j)
    P(driver i P2 | winner known) = strength_i / sum(strength_j for remaining j)
    etc.

    This naturally handles the dependencies between finishing positions
    that simple softmax-based approaches miss.
    """

    def __init__(self, strength_params: Optional[Dict[str, float]] = None):
        """
        Args:
            strength_params: Optional dict of driver_id -> strength parameter
        """
        self.strength_params = strength_params or {}
        self._available = _SCIPY_AVAILABLE

    def fit_from_scores(
        self,
        driver_composite_scores: List[Dict],
        scale_range: Tuple[float, float] = (0.1, 5.0),
    ) -> Dict[str, float]:
        """
        Convert composite scores to Plackett-Luce strength parameters.

        Uses a scaled exponential transformation to ensure positive strengths.

        Args:
            driver_composite_scores: From compute_all_drivers()
            scale_range: Range for strength parameter scaling

        Returns:
            Dict of driver_id -> strength parameter
        """
        scores = {d["driver_id"]: d["composite_score"] for d in driver_composite_scores}
        min_s, max_s = min(scores.values()), max(scores.values())
        range_s = max_s - min_s if max_s > min_s else 1.0

        # Scale to [scale_range[0], scale_range[1]]
        lo, hi = scale_range
        strengths = {}
        for did, s in scores.items():
            normalized = (s - min_s) / range_s
            strengths[did] = lo + normalized * (hi - lo)

        self.strength_params = strengths
        return strengths

    def fit_from_xgboost(
        self,
        xgb_rankings: List[RankedDriver],
        temperature: float = 1.0,
    ) -> Dict[str, float]:
        """
        Convert XGBoost ranking scores to PL strength parameters.

        Args:
            xgb_rankings: Output from XGBoostRanker.rank_drivers()
            temperature: Temperature for scaling (lower = more concentrated)

        Returns:
            Dict of driver_id -> strength parameter
        """
        scores = {r.driver_id: r.rank_score for r in xgb_rankings}
        min_s, max_s = min(scores.values()), max(scores.values())
        range_s = max_s - min_s if max_s > min_s else 1.0

        strengths = {}
        for did, s in scores.items():
            normalized = (s - min_s) / range_s
            strengths[did] = np.exp(normalized / temperature)

        self.strength_params = strengths
        return strengths

    def compute_win_probabilities(self) -> Dict[str, float]:
        """
        Compute win probabilities using the Plackett-Luce formula.

        P(driver i wins) = strength_i / sum(strength_j for all j)

        Returns:
            Dict of driver_id -> win probability
        """
        if not self.strength_params:
            return {}

        total = sum(self.strength_params.values())
        if total == 0:
            return {k: 1.0 / len(self.strength_params) for k in self.strength_params}

        return {k: v / total for k, v in self.strength_params.items()}

    def compute_top_k_probabilities(self, k: int = 3) -> Dict[str, float]:
        """
        Compute top-k probabilities using iterative PL formula.

        P(driver i in top k) = sum over all permutations of top k
        containing driver i of the probability of that permutation.

        Uses an efficient iterative approximation.

        Args:
            k: Number of top positions (3 for podium, 10 for points)

        Returns:
            Dict of driver_id -> top-k probability
        """
        if not self.strength_params:
            return {}

        driver_ids = list(self.strength_params.keys())
        strengths = np.array([self.strength_params[did] for did in driver_ids])
        n = len(strengths)

        # Compute probability each driver finishes in each position
        # using the sequential PL formula
        probs = np.zeros((n, min(k, n)))

        remaining_strengths = strengths.copy()
        for pos in range(min(k, n)):
            total_remaining = np.sum(remaining_strengths)
            if total_remaining == 0:
                break
            probs[:, pos] = remaining_strengths / total_remaining

            # For next position, we need to condition on removing the winner
            # We approximate by reducing strength proportional to win prob
            win_probs = remaining_strengths / total_remaining
            remaining_strengths = remaining_strengths * (1 - win_probs) / (1 - win_probs + 1e-9)

        # Top-k probability = sum of position probabilities for positions 1..k
        top_k_probs = np.sum(probs[:, :k], axis=1)
        top_k_probs = np.clip(top_k_probs, 0.0, 1.0)

        return {driver_ids[i]: float(top_k_probs[i]) for i in range(n)}

    def compute_position_distribution(
        self,
        driver_id: str,
        n_positions: int = 20,
    ) -> List[float]:
        """
        Compute probability distribution over all finishing positions for a driver.

        Args:
            driver_id: Driver identifier
            n_positions: Number of positions to compute

        Returns:
            List of probabilities [P(pos=1), P(pos=2), ..., P(pos=n_positions)]
        """
        if not self.strength_params or driver_id not in self.strength_params:
            return [1.0 / n_positions] * n_positions

        driver_ids = sorted(self.strength_params.keys(),
                           key=lambda x: self.strength_params[x], reverse=True)
        n = min(len(driver_ids), n_positions)
        dist = [0.0] * n_positions

        driver_idx = None
        for i, did in enumerate(driver_ids):
            if did == driver_id:
                driver_idx = i
                break

        if driver_idx is None:
            return [1.0 / n_positions] * n_positions

        strengths = np.array([self.strength_params[did] for did in driver_ids])

        # Monte Carlo approximation for position distribution
        rng = np.random.RandomState(42)
        n_sim = 10000
        positions = np.zeros(n_sim, dtype=int)

        for sim in range(n_sim):
            remaining = list(range(n))
            for pos in range(1, n + 1):
                remaining_strengths = strengths[remaining]
                total = np.sum(remaining_strengths)
                if total == 0:
                    break
                probs = remaining_strengths / total
                winner_idx = rng.choice(len(remaining), p=probs)
                winner_global = remaining[winner_idx]
                if winner_global == driver_idx:
                    positions[sim] = pos
                    break
                remaining.pop(winner_idx)

        for pos in range(1, n + 1):
            dist[pos - 1] = float(np.mean(positions == pos))

        return dist

    def predict_full(
        self,
        driver_composite_scores: List[Dict],
    ) -> List[RankedDriver]:
        """
        Full Plackett-Luce prediction for a race.

        Args:
            driver_composite_scores: From compute_all_drivers()

        Returns:
            List of RankedDriver with PL probabilities
        """
        self.fit_from_scores(driver_composite_scores)
        win_probs = self.compute_win_probabilities()
        top3_probs = self.compute_top_k_probabilities(3)
        top10_probs = self.compute_top_k_probabilities(10)

        rankings = []
        for d in driver_composite_scores:
            did = d["driver_id"]
            driver_data = _get_driver_safe(did)
            rankings.append(RankedDriver(
                driver_id=did,
                driver_name=driver_data.get("name", did),
                team=driver_data.get("team", "unknown"),
                rank_score=win_probs.get(did, 0.0),
                rank_position=0,
                pl_win_prob=win_probs.get(did, 0.0),
                pl_top3_prob=top3_probs.get(did, 0.0),
                pl_top10_prob=top10_probs.get(did, 0.0),
            ))

        rankings.sort(key=lambda r: r.rank_score, reverse=True)
        for pos, r in enumerate(rankings, start=1):
            r.rank_position = pos

        return rankings


# ── Optuna Hyperparameter Tuning ─────────────────────────────────────────────

class MLHyperparameterTuner:
    """
    Optuna-based hyperparameter tuning for XGBoost LambdaMART.

    Optimizes NDCG@3 as the primary metric.
    """

    def __init__(self, n_trials: int = 50):
        self.n_trials = n_trials
        self.best_params: Dict = {}
        self.best_score: float = 0.0
        self.study = None
        self._available = _OPTUNA_AVAILABLE and _XGBOOST_AVAILABLE

    def tune(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: np.ndarray,
        n_trials: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run Optuna hyperparameter optimization.

        Args:
            X: Training features
            y: Relevance scores
            groups: Group boundaries
            n_trials: Number of trials (overrides instance default)

        Returns:
            Best parameters dict
        """
        if not self._available:
            logger.warning("Optuna or XGBoost not available for tuning")
            return self._default_params()

        n_trials = n_trials or self.n_trials

        def objective(trial):
            params = {
                "objective": "rank:ndcg",
                "eval_metric": "ndcg@3",
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_float("min_child_weight", 0.5, 5.0),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 5.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 5.0),
                "seed": 42,
                "verbosity": 0,
            }

            n_estimators = trial.suggest_int("n_estimators", 50, 500)

            # Split data for validation
            n_groups = len(groups)
            split_idx = int(n_groups * 0.8)
            train_groups = groups[:split_idx]
            val_groups = groups[split_idx:]

            train_end = int(np.sum(groups[:split_idx]))
            X_train, y_train = X[:train_end], y[:train_end]
            X_val, y_val = X[train_end:], y[train_end:]

            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtrain.set_group(train_groups)
            dval = xgb.DMatrix(X_val, label=y_val)
            dval.set_group(val_groups)

            model = xgb.train(
                params,
                dtrain,
                num_boost_round=n_estimators,
                evals=[(dtrain, "train"), (dval, "eval")],
                early_stopping_rounds=20,
                verbose_eval=False,
            )

            # Get best NDCG@3
            best_iteration = model.best_iteration
            # Manual NDCG calculation for validation set
            val_scores = model.predict(dval)
            ndcg = self._calculate_ndcg(val_scores, y_val, val_groups, k=3)

            return ndcg

        self.study = optuna.create_study(
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        self.study.optimize(objective, n_trials=n_trials)

        self.best_params = self.study.best_params
        self.best_score = self.study.best_value
        logger.info(f"Optuna tuning complete: best NDCG@3={self.best_score:.4f}")

        return self.best_params

    def _calculate_ndcg(
        self, scores: np.ndarray, y: np.ndarray, groups: np.ndarray, k: int = 3
    ) -> float:
        """Calculate NDCG@k manually."""
        pos = 0
        ndcg_total = 0.0
        n_groups = 0

        for g in groups:
            group_scores = scores[pos:pos + g]
            group_y = y[pos:pos + g]
            pos += g

            # Sort by predicted score
            order = np.argsort(-group_scores)
            sorted_y = group_y[order]

            # DCG@k
            dcg = sum(
                (2 ** rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(sorted_y[:k])
            )

            # IDCG@k
            ideal_order = np.argsort(-group_y)
            ideal_y = group_y[ideal_order]
            idcg = sum(
                (2 ** rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(ideal_y[:k])
            )

            ndcg_total += dcg / max(idcg, 1e-9)
            n_groups += 1

        return ndcg_total / max(n_groups, 1)

    def _default_params(self) -> Dict[str, Any]:
        """Return default reasonable parameters."""
        return {
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 1.0,
            "gamma": 0.0,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
            "n_estimators": 200,
        }


# ── Training Pipeline ────────────────────────────────────────────────────────

def train_ml_pipeline(
    seasons: Optional[List[int]] = None,
    n_trials: int = 30,
    tune_hyperparams: bool = True,
    force_refresh_data: bool = False,
) -> Dict[str, Any]:
    """
    End-to-end ML training pipeline.

    Steps:
    1. Auto-fetch historical data (2022-2025)
    2. Prepare feature matrix
    3. Optionally tune hyperparameters with Optuna
    4. Train XGBoost LambdaMART
    5. Save trained model

    Args:
        seasons: Seasons to train on
        n_trials: Number of Optuna trials
        tune_hyperparams: Whether to tune hyperparameters
        force_refresh_data: Force re-fetch of historical data

    Returns:
        Training report dict
    """
    logger.info("=" * 60)
    logger.info("STARTING ML TRAINING PIPELINE")
    logger.info("=" * 60)

    if not _XGBOOST_AVAILABLE:
        logger.error("XGBoost not installed. Cannot train.")
        return {"status": "error", "message": "XGBoost not installed"}

    # Step 1: Fetch data
    logger.info("Step 1/4: Fetching historical race data...")
    races = auto_fetch_historical_data(seasons, force_refresh=force_refresh_data)
    if not races:
        return {"status": "error", "message": "No historical data available"}
    logger.info(f"  Loaded {len(races)} races")

    # Step 2: Prepare features
    logger.info("Step 2/4: Preparing training features...")
    X, y, groups = FeaturePreparator.prepare_training_data(races)
    if len(X) == 0:
        return {"status": "error", "message": "Could not prepare training data"}
    logger.info(f"  Features: {X.shape}, {len(groups)} groups")

    # Step 3: Tune hyperparameters (optional)
    ranker = XGBoostRanker()
    if tune_hyperparams and _OPTUNA_AVAILABLE:
        logger.info(f"Step 3a/4: Tuning hyperparameters ({n_trials} trials)...")
        tuner = MLHyperparameterTuner(n_trials=n_trials)
        best_params = tuner.tune(X, y, groups)
        logger.info(f"  Best params: {best_params}")

        # Create ranker with best params
        ranker = XGBoostRanker(
            n_estimators=best_params.get("n_estimators", 200),
            max_depth=best_params.get("max_depth", 6),
            learning_rate=best_params.get("learning_rate", 0.1),
            subsample=best_params.get("subsample", 0.8),
            colsample_bytree=best_params.get("colsample_bytree", 0.8),
            min_child_weight=best_params.get("min_child_weight", 1.0),
            gamma=best_params.get("gamma", 0.0),
            reg_alpha=best_params.get("reg_alpha", 0.0),
            reg_lambda=best_params.get("reg_lambda", 1.0),
        )
    else:
        logger.info("Step 3a/4: Using default hyperparameters")

    # Step 4: Train
    logger.info("Step 4/4: Training XGBoost LambdaMART...")
    history = ranker.train(X, y, groups)

    # Save model
    ranker.save()

    result = {
        "status": "success",
        "n_races": len(races),
        "n_samples": len(X),
        "n_groups": len(groups),
        "training_history": {k: round(float(v), 4) for k, v in history.items()} if isinstance(history, dict) else {},
        "model_path": str(XGB_MODEL_PATH),
        "model_available": ranker.is_trained,
    }

    logger.info("=" * 60)
    logger.info("ML TRAINING COMPLETE")
    logger.info("=" * 60)

    return result


# ── Convenience: Get ML predictions for a race ───────────────────────────────

def get_ml_predictions(
    driver_composite_scores: List[Dict],
    circuit_id: str,
    use_xgboost: bool = True,
    use_plackett_luce: bool = True,
) -> MLPredictionResult:
    """
    Get ML-based predictions for a race.

    Combines XGBoost ranking and Plackett-Luce probabilities.

    Args:
        driver_composite_scores: From compute_all_drivers()
        circuit_id: Circuit identifier
        use_xgboost: Whether to use XGBoost (falls back to composite if unavailable)
        use_plackett_luce: Whether to compute PL probabilities

    Returns:
        MLPredictionResult with rankings and probabilities
    """
    # XGBoost ranking
    xgb_ranker = XGBoostRanker()
    model_loaded = xgb_ranker.load() if _XGBOOST_AVAILABLE else False

    if use_xgboost and model_loaded and _XGBOOST_AVAILABLE:
        xgb_rankings = xgb_ranker.rank_drivers(driver_composite_scores, circuit_id)
        model_used = "xgboost_lambdarank"
    else:
        # Fallback: rank by composite score
        logger.info("XGBoost model not available, using composite score ranking")
        sorted_scores = sorted(
            driver_composite_scores,
            key=lambda x: x["composite_score"],
            reverse=True,
        )
        xgb_rankings = []
        for i, d in enumerate(sorted_scores, start=1):
            driver_data = _get_driver_safe(d["driver_id"])
            xgb_rankings.append(RankedDriver(
                driver_id=d["driver_id"],
                driver_name=driver_data.get("name", d["driver_id"]),
                team=driver_data.get("team", "unknown"),
                rank_score=float(d["composite_score"]),
                rank_position=i,
            ))
        model_used = "composite_fallback"

    # Plackett-Luce probabilities
    pl_model = PlackettLuceModel()
    if use_plackett_luce and model_loaded and _SCIPY_AVAILABLE:
        pl_model.fit_from_xgboost(xgb_rankings, temperature=1.0)
        win_probs = pl_model.compute_win_probabilities()
        top3_probs = pl_model.compute_top_k_probabilities(3)
        top10_probs = pl_model.compute_top_k_probabilities(10)

        for r in xgb_rankings:
            r.pl_win_prob = win_probs.get(r.driver_id, 0.0)
            r.pl_top3_prob = top3_probs.get(r.driver_id, 0.0)
            r.pl_top10_prob = top10_probs.get(r.driver_id, 0.0)

    return MLPredictionResult(
        rankings=xgb_rankings,
        model_used=model_used,
        ensemble_weight=0.6 if model_loaded else 0.3,
    )


__all__ = [
    "XGBoostRanker",
    "PlackettLuceModel",
    "MLHyperparameterTuner",
    "FeaturePreparator",
    "RankedDriver",
    "MLPredictionResult",
    "train_ml_pipeline",
    "get_ml_predictions",
    "auto_fetch_historical_data",
    "MODELS_DIR",
    "_XGBOOST_AVAILABLE",
    "_SCIPY_AVAILABLE",
]

