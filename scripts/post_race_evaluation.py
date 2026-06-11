"""Post-race evaluation helper for F1 Predictor."""

import json
import sys

from engine.prediction_tracker import run_post_race_evaluation


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/post_race_evaluation.py <race_id> <results.json>")
        sys.exit(1)

    race_id = sys.argv[1]
    results_path = sys.argv[2]

    with open(results_path, "r", encoding="utf-8") as f:
        actual_results = json.load(f)

    result = run_post_race_evaluation(race_id, actual_results)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
