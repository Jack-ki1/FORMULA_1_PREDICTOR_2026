"""
Hugging Face NLP/Sentiment Integration for F1 News Analysis.

Provides:
  1. Zero-shot classification for F1 technical upgrades, penalty analysis
  2. Sentiment analysis for driver/team news sentiment
  3. Driver confidence adjustment based on parsed news
  4. Hugging Face Hub export for prediction benchmarks and datasets

Graceful fallback when transformers are not installed or GPU unavailable.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional Dependencies ────────────────────────────────────────────────────
_TRANSFORMERS_AVAILABLE = False
_TORCH_AVAILABLE = False

try:
    import transformers
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers not installed. Install with: pip install transformers")

try:
    import torch
    _TORCH_AVAILABLE = torch.cuda.is_available() or True  # CPU always available
except ImportError:
    _TORCH_AVAILABLE = False

_HF_HUB_AVAILABLE = False
try:
    from huggingface_hub import HfApi, create_repo, upload_file
    _HF_HUB_AVAILABLE = True
except ImportError:
    logger.warning("huggingface_hub not installed. Install with: pip install huggingface_hub")


# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class F1NewsItem:
    """Represents a single parsed F1 news item."""
    source: str                      # "technical_upgrade", "penalty", "weather", "general"
    driver_ids: List[str]           # Affected driver(s)
    team: Optional[str]             # Affected team (if applicable)
    sentiment: float                # -1.0 (negative) to 1.0 (positive)
    confidence: float               # 0.0 to 1.0
    category: str                   # e.g., "engine_penalty", "aero_upgrade", "weather_alert"
    headline: str                   # Original text
    impact_score: float             # 0.0 to 1.0 (how much this affects performance)


@dataclass
class SentimentOverride:
    """Sentiment-based confidence adjustment for a driver."""
    driver_id: str
    base_sentiment: float           # Overall news sentiment for this driver
    confidence_adjustment: float    # How much to adjust win probability (-0.5 to +0.5)
    news_items: List[F1NewsItem]    # Supporting news items
    last_updated: str               # ISO timestamp


# ── Fallback Patterns ────────────────────────────────────────────────────────

# Keyword-based fallback when transformers are not available
SENTIMENT_KEYWORDS = {
    "positive": [
        "win", "victory", "champion", "fastest", "podium", "upgrade", "new floor",
        "new front wing", "new rear wing", "improved", "breakthrough", "dominant",
        "pole position", "optimized", "innovation", "confidence",
    ],
    "negative": [
        "penalty", "grid drop", "dnf", "crash", "retirement", "engine failure",
        "gearbox", "hydraulic", "issue", "problem", "struggle", "slow",
        "investigation", "stewards", "disqualification", "damage",
    ],
    "upgrade": [
        "upgrade", "update", "new package", "aero", "floor", "diffuser",
        "front wing", "rear wing", "suspension", "engine mode", "power unit",
    ],
    "penalty": [
        "penalty", "grid penalty", "engine penalty", "gearbox change",
        "power unit change", "reprimand", "time penalty", "qualifying penalty",
    ],
}

# Categories for zero-shot classification
F1_CATEGORIES = [
    "engine upgrade", "aero upgrade", "suspension upgrade",
    "engine penalty", "gearbox penalty", "driver transfer",
    "weather alert", "safety car", "team strategy",
    "driver performance", "reliability improvement",
    "pit stop improvement", "tire degradation improvement",
]


# ── NLP Pipeline ─────────────────────────────────────────────────────────────

class F1NLPipeline:
    """
    Hugging Face NLP pipeline for F1 news analysis.

    Supports:
    - Zero-shot classification (Facebook BART-large-MNLI)
    - Sentiment analysis (Twitter RoBERTa)
    - Keyword-based fallback when models unavailable
    """

    def __init__(
        self,
        zero_shot_model: str = "facebook/bart-large-mnli",
        sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
        device: int = -1,  # -1 for CPU, 0 for GPU
    ):
        self.zero_shot_model_name = zero_shot_model
        self.sentiment_model_name = sentiment_model
        self.device = device

        self.zero_shot_pipeline = None
        self.sentiment_pipeline = None
        self._initialized = False

        # Driver ID mapping for entity recognition
        self._driver_aliases = self._build_driver_aliases()

    def _build_driver_aliases(self) -> Dict[str, str]:
        """Build mapping of name variants to driver IDs."""
        try:
            from data.driver_data import get_all_drivers
            aliases = {}
            for d in get_all_drivers():
                name = d.get("name", d["id"])
                # Full name lowercase
                aliases[name.lower()] = d["id"]
                # First name
                aliases[name.split()[0].lower()] = d["id"]
                # Last name
                if len(name.split()) > 1:
                    aliases[name.split()[-1].lower()] = d["id"]
                # Short code
                aliases[d.get("short", d["id"]).lower()] = d["id"]
            return aliases
        except Exception:
            return {}

    def initialize(self) -> bool:
        """
        Load Hugging Face models into memory.

        Returns:
            True if models loaded, False if fallback must be used
        """
        if self._initialized:
            return True

        if not _TRANSFORMERS_AVAILABLE:
            logger.warning("transformers not available. Using keyword-based fallback.")
            return False

        try:
            import transformers

            # Determine device
            device_id = self.device
            if device_id < 0 and _TORCH_AVAILABLE:
                device_id = -1  # CPU

            logger.info(f"Loading zero-shot model: {self.zero_shot_model_name}")
            self.zero_shot_pipeline = transformers.pipeline(
                "zero-shot-classification",
                model=self.zero_shot_model_name,
                device=device_id,
            )

            logger.info(f"Loading sentiment model: {self.sentiment_model_name}")
            self.sentiment_pipeline = transformers.pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                device=device_id,
            )

            self._initialized = True
            logger.info("NLP models loaded successfully")
            return True

        except Exception as e:
            logger.warning(f"Failed to load NLP models: {e}. Using keyword-based fallback.")
            return False

    def classify_news(
        self,
        text: str,
        candidate_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Classify F1 news text using zero-shot or keyword fallback.

        Args:
            text: News text to classify
            candidate_labels: Optional list of labels (uses F1_CATEGORIES if None)

        Returns:
            Dict with labels, scores, and confidence
        """
        if candidate_labels is None:
            candidate_labels = F1_CATEGORIES

        if self.zero_shot_pipeline is not None:
            try:
                result = self.zero_shot_pipeline(text, candidate_labels)
                return {
                    "labels": result["labels"],
                    "scores": result["scores"],
                    "confidence": max(result["scores"]),
                    "method": "zero_shot",
                }
            except Exception as e:
                logger.debug(f"Zero-shot classification failed: {e}")

        # Fallback: keyword matching
        text_lower = text.lower()
        label_scores = []
        for label in candidate_labels:
            score = 0.0
            keywords = label.lower().split()
            for kw in keywords:
                if kw in text_lower:
                    score += 1.0 / len(keywords)
            label_scores.append(score)

        if max(label_scores) > 0:
            import numpy as np
            scores = np.array(label_scores, dtype=float)
            scores = scores / (scores.sum() + 1e-9)
            return {
                "labels": candidate_labels,
                "scores": scores.tolist(),
                "confidence": float(max(scores)),
                "method": "keyword_fallback",
            }

        return {
            "labels": candidate_labels,
            "scores": [1.0 / len(candidate_labels)] * len(candidate_labels),
            "confidence": 0.3,
            "method": "uniform_fallback",
        }

    def analyze_sentiment(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of F1 news text.

        Returns:
            Dict with sentiment (-1 to 1), confidence, and label
        """
        if self.sentiment_pipeline is not None:
            try:
                result = self.sentiment_pipeline(text)[0]
                label = result["label"]
                score = result["score"]
                if label.upper() == "POSITIVE":
                    sentiment = float(score)
                elif label.upper() == "NEGATIVE":
                    sentiment = -float(score)
                else:
                    sentiment = float(score) * 2 - 1  # Map [0,1] to [-1,1]

                return {
                    "sentiment": sentiment,
                    "confidence": float(score),
                    "label": label,
                    "method": "transformer",
                }
            except Exception as e:
                logger.debug(f"Sentiment analysis failed: {e}")

        # Fallback: keyword-based sentiment
        text_lower = text.lower()
        positive_count = sum(1 for kw in SENTIMENT_KEYWORDS["positive"] if kw in text_lower)
        negative_count = sum(1 for kw in SENTIMENT_KEYWORDS["negative"] if kw in text_lower)

        total = positive_count + negative_count
        if total > 0:
            net = (positive_count - negative_count) / total
        else:
            net = 0.0

        confidence = min(1.0, total / 5.0)  # More keywords = more confident

        return {
            "sentiment": net,
            "confidence": confidence,
            "label": "POSITIVE" if net > 0.1 else "NEGATIVE" if net < -0.1 else "NEUTRAL",
            "method": "keyword_fallback",
        }

    def extract_drivers(self, text: str) -> List[str]:
        """Extract mentioned driver IDs from text."""
        text_lower = text.lower()
        mentioned = []
        for alias, driver_id in self._driver_aliases.items():
            if alias in text_lower and driver_id not in mentioned:
                mentioned.append(driver_id)
        return mentioned

    def extract_team(self, text: str) -> Optional[str]:
        """Extract mentioned team from text."""
        teams = [
            "mercedes", "red bull", "ferrari", "mclaren", "williams",
            "alpine", "haas", "aston martin", "audi", "rb", "cadillac",
            "racing bulls",
        ]
        text_lower = text.lower()
        for team in teams:
            if team in text_lower:
                # Map to internal ID
                team_map = {
                    "mercedes": "mercedes",
                    "red bull": "red_bull",
                    "ferrari": "ferrari",
                    "mclaren": "mclaren",
                    "williams": "williams",
                    "alpine": "alpine",
                    "haas": "haas",
                    "aston martin": "aston_martin",
                    "audi": "audi",
                    "rb": "rb",
                    "cadillac": "cadillac",
                    "racing bulls": "rb",
                }
                return team_map.get(team)
        return None


# ── News Parser ──────────────────────────────────────────────────────────────

class F1NewsParser:
    """
    Parses F1 news/updates and produces driver sentiment overrides.

    Handles:
    - Technical upgrade announcements (aero, engine, suspension)
    - Engine/grid penalties
    - Weather alerts
    - Driver performance analysis
    - Team strategy announcements
    """

    def __init__(self, nlp_pipeline: Optional[F1NLPipeline] = None):
        self.nlp = nlp_pipeline or F1NLPipeline()
        self.news_history: List[F1NewsItem] = []
        self.driver_overrides: Dict[str, SentimentOverride] = {}

        # Initialize NLP
        self.nlp.initialize()

    def parse_news_item(
        self,
        text: str,
        source: str = "general",
    ) -> Optional[F1NewsItem]:
        """
        Parse a single F1 news item and return structured data.

        Args:
            text: News text
            source: Source category

        Returns:
            F1NewsItem or None if parsing fails
        """
        # Classify the news
        classification = self.nlp.classify_news(text)
        sentiment_result = self.nlp.analyze_sentiment(text)

        # Extract entities
        driver_ids = self.nlp.extract_drivers(text)
        team = self.nlp.extract_team(text)

        # Determine category from classification
        category = classification["labels"][0] if classification["scores"] else "general"
        confidence = classification["confidence"]

        # Calculate impact score based on category and sentiment
        impact_score = self._calculate_impact(category, sentiment_result["sentiment"])

        news_item = F1NewsItem(
            source=source,
            driver_ids=driver_ids if driver_ids else [],
            team=team,
            sentiment=sentiment_result["sentiment"],
            confidence=confidence,
            category=category,
            headline=text,
            impact_score=impact_score,
        )

        self.news_history.append(news_item)
        return news_item

    def _calculate_impact(self, category: str, sentiment: float) -> float:
        """Calculate how much this news affects performance (0-1)."""
        high_impact_categories = [
            "engine penalty", "aero upgrade", "driver transfer",
        ]
        medium_impact_categories = [
            "engine upgrade", "suspension upgrade", "team strategy",
            "reliability improvement", "weather alert",
        ]

        abs_sentiment = abs(sentiment)

        if any(c in category for c in high_impact_categories):
            base_impact = 0.7
        elif any(c in category for c in medium_impact_categories):
            base_impact = 0.4
        else:
            base_impact = 0.2

        return min(1.0, base_impact * (0.5 + 0.5 * abs_sentiment))

    def process_news_batch(
        self,
        news_items: List[str],
        source: str = "general",
    ) -> List[F1NewsItem]:
        """
        Process a batch of news items.

        Args:
            news_items: List of news text strings
            source: Source category

        Returns:
            List of parsed F1NewsItem
        """
        parsed = []
        for text in news_items:
            item = self.parse_news_item(text, source)
            if item:
                parsed.append(item)
        return parsed

    def compute_driver_overrides(self) -> Dict[str, SentimentOverride]:
        """
        Compute sentiment overrides for all drivers based on recent news.

        Returns:
            Dict of driver_id -> SentimentOverride
        """
        # Aggregate news by driver
        driver_news: Dict[str, List[F1NewsItem]] = {}
        for item in self.news_history:
            for did in item.driver_ids:
                if did not in driver_news:
                    driver_news[did] = []
                driver_news[did].append(item)

        overrides = {}
        for did, items in driver_news.items():
            if not items:
                continue

            # Calculate average sentiment weighted by impact
            total_weight = sum(i.impact_score for i in items)
            if total_weight == 0:
                continue

            weighted_sentiment = sum(
                i.sentiment * i.impact_score for i in items
            ) / total_weight

            # Confidence adjustment: map sentiment [-1, 1] to adjustment [-0.5, 0.5]
            confidence_adjustment = weighted_sentiment * 0.3

            overrides[did] = SentimentOverride(
                driver_id=did,
                base_sentiment=round(weighted_sentiment, 3),
                confidence_adjustment=round(confidence_adjustment, 3),
                news_items=items[-5:],  # Last 5 items
                last_updated=datetime.now().isoformat(),
            )

        self.driver_overrides = overrides
        return overrides

    def apply_overrides_to_predictions(
        self,
        predictions: List[Dict],
        max_adjustment: float = 0.15,
    ) -> List[Dict]:
        """
        Apply sentiment overrides to prediction probabilities.

        Adjusts win_probability based on driver news sentiment.

        Args:
            predictions: List of prediction dicts with 'driver_id' and 'win_probability'
            max_adjustment: Maximum probability adjustment

        Returns:
            Adjusted predictions list
        """
        if not self.driver_overrides:
            self.compute_driver_overrides()

        adjusted = []
        for pred in predictions:
            did = pred.get("driver_id", pred.get("driver", ""))
            override = self.driver_overrides.get(did)

            if override:
                adjustment = override.confidence_adjustment * max_adjustment
                pred["win_probability"] = np.clip(
                    pred.get("win_probability", 0.0) + adjustment,
                    0.0, 1.0,
                )
                pred["sentiment_adjustment"] = round(adjustment, 4)
                pred["news_sentiment"] = override.base_sentiment

            adjusted.append(pred)

        return adjusted

    def clear_news(self):
        """Clear all parsed news (for fresh analysis)."""
        self.news_history.clear()
        self.driver_overrides.clear()


# ── Hugging Face Hub Export ──────────────────────────────────────────────────

class HFHubExporter:
    """
    Exports prediction benchmarks, datasets, and model metrics to Hugging Face Hub.

    Allows sharing prediction results and comparing models publicly.
    """

    def __init__(self, repo_name: str = "f1-predictor-2026-benchmarks"):
        self.repo_name = repo_name
        self.api = None
        self._available = _HF_HUB_AVAILABLE

    def ensure_repo(self) -> bool:
        """Create or verify the HF Hub repository exists."""
        if not self._available:
            return False

        try:
            self.api = HfApi()
            try:
                create_repo(self.repo_name, exist_ok=True, repo_type="dataset")
            except Exception:
                pass  # Repo may already exist
            return True
        except Exception as e:
            logger.error(f"Failed to create HF Hub repo: {e}")
            return False

    def export_benchmark(
        self,
        benchmark_data: Dict,
        filename: str = "benchmark_results.json",
    ) -> bool:
        """
        Export benchmark results to Hugging Face Hub.

        Args:
            benchmark_data: Benchmark results dict
            filename: Output filename in repo

        Returns:
            True if successful
        """
        if not self.ensure_repo():
            logger.warning("HF Hub not available. Saving locally.")
            self._save_local(benchmark_data, filename)
            return False

        try:
            import tempfile
            import json as json_module

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json_module.dump(benchmark_data, f, indent=2)
                temp_path = f.name

            upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=f"benchmarks/{filename}",
                repo_id=self.repo_name,
                repo_type="dataset",
            )

            Path(temp_path).unlink(missing_ok=True)
            logger.info(f"Benchmark exported to HF Hub: {self.repo_name}/benchmarks/{filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to HF Hub: {e}")
            self._save_local(benchmark_data, filename)
            return False

    def export_predictions(
        self,
        predictions: List[Dict],
        race_id: str,
        format: str = "json",
    ) -> bool:
        """
        Export race predictions to Hugging Face Hub.

        Args:
            predictions: List of prediction dicts
            race_id: Circuit/race identifier
            format: File format (json or csv)

        Returns:
            True if successful
        """
        if not self.ensure_repo():
            return False

        try:
            import tempfile
            import json as json_module

            filename = f"predictions_{race_id}.{format}"

            with tempfile.NamedTemporaryFile(mode="w", suffix=f".{format}", delete=False) as f:
                if format == "json":
                    json_module.dump(predictions, f, indent=2)
                else:
                    import csv
                    if predictions:
                        writer = csv.DictWriter(f, fieldnames=predictions[0].keys())
                        writer.writeheader()
                        writer.writerows(predictions)
                temp_path = f.name

            upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=f"predictions/{filename}",
                repo_id=self.repo_name,
                repo_type="dataset",
            )

            Path(temp_path).unlink(missing_ok=True)
            logger.info(f"Predictions exported to HF Hub: {self.repo_name}/predictions/{filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export predictions: {e}")
            return False

    def export_model_metrics(
        self,
        metrics: Dict,
        model_name: str = "xgboost_lambdarank",
    ) -> bool:
        """
        Export model training metrics to Hugging Face Hub.

        Args:
            metrics: Training/evaluation metrics dict
            model_name: Model identifier

        Returns:
            True if successful
        """
        if not self.ensure_repo():
            return False

        try:
            import tempfile
            import json as json_module

            filename = f"metrics_{model_name}.json"

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json_module.dump({
                    "model": model_name,
                    "metrics": metrics,
                    "timestamp": datetime.now().isoformat(),
                }, f, indent=2)
                temp_path = f.name

            upload_file(
                path_or_fileobj=temp_path,
                path_in_repo=f"metrics/{filename}",
                repo_id=self.repo_name,
                repo_type="dataset",
            )

            Path(temp_path).unlink(missing_ok=True)
            logger.info(f"Model metrics exported to HF Hub: {self.repo_name}/metrics/{filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False

    def _save_local(self, data: Dict, filename: str):
        """Save data locally when HF Hub is unavailable."""
        export_dir = Path(__file__).resolve().parents[1] / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Exported locally to {path}")


# ── Convenience Functions ────────────────────────────────────────────────────

# Default parser singleton
_default_parser: Optional[F1NewsParser] = None


def get_news_parser() -> F1NewsParser:
    """Get or create the default news parser singleton."""
    global _default_parser
    if _default_parser is None:
        _default_parser = F1NewsParser()
    return _default_parser


def get_hf_exporter() -> HFHubExporter:
    """Get a Hugging Face Hub exporter instance."""
    return HFHubExporter()


def adjust_predictions_with_sentiment(
    predictions: List[Dict],
    news_texts: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Convenience function: parse news and adjust predictions in one call.

    Args:
        predictions: List of prediction dicts
        news_texts: Optional list of news texts to process

    Returns:
        Adjusted predictions
    """
    parser = get_news_parser()

    if news_texts:
        parser.process_news_batch(news_texts)

    overrides = parser.compute_driver_overrides()
    return parser.apply_overrides_to_predictions(predictions)


__all__ = [
    "F1NLPipeline",
    "F1NewsParser",
    "HFHubExporter",
    "F1NewsItem",
    "SentimentOverride",
    "get_news_parser",
    "get_hf_exporter",
    "adjust_predictions_with_sentiment",
    "_TRANSFORMERS_AVAILABLE",
]

