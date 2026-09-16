import logging
from backend.app.engine.benchmark_suite import BenchmarkSuite
logger = logging.getLogger(__name__)
from backend.app.config.feature_weights import feature_weights
from backend.app.config.constants import TARGETS
class AnalyticsService:
    def get_accuracy(self):
        """Measured accuracy, or an explicit 'not measured' result.

        NOTE: this used to have an `except` branch returning hardcoded
        accuracies (winner 0.58, podium 0.89, points 0.81, q3 0.74) — a second
        copy of the same fabrication that lived in BenchmarkSuite, and a worse
        one because it fired exactly when measurement was unavailable. It is
        removed: on failure we report the failure, never a plausible number.
        """
        try:
            return BenchmarkSuite().generate_accuracy_report()
        except Exception as e:
            logger.warning("accuracy measurement failed: %s", e)
            return {
                "status": "error",
                "target_accuracies": {},
                "measured_on": None,
                "races_evaluated": 0,
                "note": f"accuracy could not be measured: {e}",
            }
    def get_weights(self):
        try: return feature_weights.get_all_weights()
        except Exception: return {"chaos_level":50,"wet_influence":50,"reliability_influence":50,"strategy_aggressiveness":50,"grid_weight":55}
    def update_weights(self, data: dict):
        for k,v in data.items():
            feature_weights.validate_weight(k,v)
        return {"status":"success","weights": data}
    def get_targets(self):
        return list(TARGETS.values())
analytics_service = AnalyticsService()
