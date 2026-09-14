"""
Generate golden prediction fixtures — deterministic inputs, AI disabled.
Stores to tests/fixtures/golden/*.json for parity harness.
"""
import json, os, hashlib
from pathlib import Path

FIXTURE_DIR = Path("tests/fixtures/golden")
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    {"race_id":"au","session_type":"race","sub_session":"race","weather":"dry","simulation_count":1000,"feature_weights":{"chaos_level":50}},
    {"race_id":"au","session_type":"qualifying","sub_session":"q3","weather":"dry","simulation_count":1000,"feature_weights":{"chaos_level":50}},
    {"race_id":"au","session_type":"practice","sub_session":"fp1","weather":"dry","simulation_count":1000,"feature_weights":{"chaos_level":50}},
    {"race_id":"mc","session_type":"race","weather":"wet","simulation_count":1000,"feature_weights":{"chaos_level":70}},
    {"race_id":"it","session_type":"race","weather":"dry","simulation_count":500,"grid_positions":{"VER":1,"LEC":2,"NOR":3},"feature_weights":{"chaos_level":30}},
]

def main():
    from backend.app.engine.predictor import generate_prediction
    for case in CASES:
        result = generate_prediction(**{**case, "ai_config":{"ai_mode":"normal"}})
        # minimal deterministic projection for fixture
        # hash inputs for filename
        h = hashlib.md5(json.dumps(case, sort_keys=True).encode()).hexdigest()[:8]
        fname = f"{case['race_id']}_{case['session_type']}_{case.get('sub_session','race')}_{h}.json"
        payload = {"input": case, "output": {
            "race_id": result["race_id"],
            "session_type": result["session_type"],
            "sub_session": result.get("sub_session"),
            "grid_positions": result["grid_positions"],
            "predictions": result["predictions"],
            "winner_probabilities": result["winner_probabilities"],
            "confidence_intervals": result["confidence_intervals"],
        }}
        (FIXTURE_DIR/fname).write_text(json.dumps(payload, indent=2))
        print(f"Wrote {fname} winner_sum={sum(result['winner_probabilities'].values()):.4f}")

if __name__ == "__main__":
    main()
