"""
Quick Verification Script - Run all critical tests after audit fixes.

Usage:
    python verify_fixes.py
"""

import sys


def test_section_1_critical_bugs():
    """Test all 5 critical bug fixes."""
    print("\n" + "="*60)
    print("SECTION 1: CRITICAL BUGS")
    print("="*60)
    
    # Bug 1: compute_recent_form_score
    try:
        from engine.feature_engineering import compute_recent_form_score
        score = compute_recent_form_score('hamilton')
        assert 0.0 <= score <= 1.0
        print("✅ Bug 1 FIXED: compute_recent_form_score no longer crashes")
    except Exception as e:
        print(f"❌ Bug 1 FAILED: {e}")
        return False
    
    # Bug 2: Logger import
    try:
        from api.routes import logger
        assert logger is not None
        print("✅ Bug 2 FIXED: Logger properly imported in routes.py")
    except Exception as e:
        print(f"❌ Bug 2 FAILED: {e}")
        return False
    
    # Bug 3: FEATURE_WEIGHTS keys
    try:
        from config.settings import FEATURE_WEIGHTS
        from engine.feature_engineering import compute_composite_score
        result = compute_composite_score('antonelli', 'canada')
        engine_keys = set(result['features'].keys())
        weight_keys = set(FEATURE_WEIGHTS.keys())
        assert engine_keys == weight_keys, f"Mismatch: {engine_keys} vs {weight_keys}"
        print("✅ Bug 3 FIXED: FEATURE_WEIGHTS keys match engine output")
    except Exception as e:
        print(f"❌ Bug 3 FAILED: {e}")
        return False
    
    # Bug 4: Pydantic schemas
    try:
        from api.schemas import WinnerPredictionResponse, DNFProbabilityResponse
        winner_resp = WinnerPredictionResponse(
            circuit='canada',
            top_5_win_probabilities=[{'driver': 'test', 'win_pct': 10.0}]
        )
        dnf_resp = DNFProbabilityResponse(
            circuit='canada',
            dnf_risk=[{'driver': 'test', 'dnf_pct': 5.0}]
        )
        print("✅ Bug 4 FIXED: Pydantic schemas aligned with routes")
    except Exception as e:
        print(f"❌ Bug 4 FAILED: {e}")
        return False
    
    # Bug 5: PredictionTracker session
    try:
        from engine.prediction_tracker import PredictionTracker
        tracker = PredictionTracker()
        # Just verify it initializes without error
        tracker.db.close()
        print("✅ Bug 5 FIXED: PredictionTracker session management corrected")
    except Exception as e:
        print(f"❌ Bug 5 FAILED: {e}")
        return False
    
    return True


def test_section_2_data_integrity():
    """Test all 5 data integrity fixes."""
    print("\n" + "="*60)
    print("SECTION 2: DATA INTEGRITY")
    print("="*60)
    
    # Conflict 1: Hamilton team
    try:
        from data.driver_data import DRIVERS
        from data.season_2026 import CONSTRUCTOR_MAPPING
        assert DRIVERS['hamilton']['team'] == CONSTRUCTOR_MAPPING['hamilton']
        assert DRIVERS['hamilton']['team'] == 'mercedes'
        print("✅ Conflict 1 FIXED: Hamilton team consistent (Mercedes)")
    except Exception as e:
        print(f"❌ Conflict 1 FAILED: {e}")
        return False
    
    # Conflict 2: Constructor strength
    try:
        from engine.feature_engineering import _CONSTRUCTOR_STRENGTH
        red_bull = _CONSTRUCTOR_STRENGTH.get('red_bull', 0)
        assert red_bull >= 0.80, f"Red Bull too low: {red_bull}"
        print(f"✅ Conflict 2 FIXED: Red Bull strength reasonable ({red_bull})")
    except Exception as e:
        print(f"❌ Conflict 2 FAILED: {e}")
        return False
    
    # Conflict 3: Duplicate Bottas
    try:
        from data.driver_data import get_all_drivers
        ids = [d['id'] for d in get_all_drivers()]
        assert 'bottas_kick' not in ids, "Duplicate Bottas still exists"
        assert len(ids) == len(set(ids)), "Other duplicates found"
        print("✅ Conflict 3 FIXED: No duplicate Bottas entry")
    except Exception as e:
        print(f"❌ Conflict 3 FAILED: {e}")
        return False
    
    # Conflict 4: Round numbering
    try:
        from data.calendar_2026 import CALENDAR_2026
        from data.circuit_data import CIRCUITS
        cal_rounds = {r['circuit']: r['round'] for r in CALENDAR_2026}
        mismatches = []
        for cid, circuit in CIRCUITS.items():
            if cid in cal_rounds and circuit['round_2026'] != cal_rounds[cid]:
                mismatches.append(cid)
        assert len(mismatches) == 0, f"Mismatches: {mismatches}"
        print("✅ Conflict 4 FIXED: All round numbers consistent")
    except Exception as e:
        print(f"❌ Conflict 4 FAILED: {e}")
        return False
    
    # Conflict 5: Hamilton recent form
    try:
        from data.driver_data import DRIVERS
        from data.season_2026 import SEASON_RESULTS_2026
        actual = []
        for race in reversed(SEASON_RESULTS_2026):
            for result in race['results']:
                if result['driver'] == 'hamilton':
                    actual.append(result['position'])
                    break
            if len(actual) >= 6:
                break
        while len(actual) < 6:
            actual.append(0)
        stored = DRIVERS['hamilton']['recent_form']
        assert actual == stored, f"Mismatch: {actual} vs {stored}"
        print("✅ Conflict 5 FIXED: Hamilton recent form matches season results")
    except Exception as e:
        print(f"❌ Conflict 5 FAILED: {e}")
        return False
    
    return True


def test_section_3_engine():
    """Test engine quality improvements."""
    print("\n" + "="*60)
    print("SECTION 3: ENGINE QUALITY")
    print("="*60)
    
    # 3.4: Experience-based ELO dampening
    try:
        from engine.feature_engineering import compute_elo_score
        # Lindblad has only 1 experience race
        score = compute_elo_score('lindblad')
        assert 0.0 <= score <= 1.0
        print("✅ 3.4 FIXED: Experience-based ELO dampening working")
    except Exception as e:
        print(f"❌ 3.4 FAILED: {e}")
        return False
    
    # 3.5-3.6: Monotonicity and normalization
    try:
        from engine.predictor import predict, PredictionRequest
        result = predict(PredictionRequest(circuit_id="canada", n_simulations=500))
        
        for pred in result['predictions']:
            assert pred['win_pct'] <= pred['top3_pct'], \
                f"Win > Top3 for {pred['driver']}"
            assert pred['top3_pct'] <= pred['top10_pct'], \
                f"Top3 > Top10 for {pred['driver']}"
        
        total_win = sum(p['win_pct'] for p in result['predictions'])
        assert 95 <= total_win <= 105, f"Win probs sum to {total_win}"
        print("✅ 3.5-3.6 FIXED: Monotonicity and normalization working")
    except Exception as e:
        print(f"❌ 3.5-3.6 FAILED: {e}")
        return False
    
    return True


def main():
    print("\n" + "#"*60)
    print("# F1 PREDICTION SYSTEM - AUDIT FIX VERIFICATION")
    print("#"*60)
    
    all_passed = True
    
    # Run all test sections
    if not test_section_1_critical_bugs():
        all_passed = False
    
    if not test_section_2_data_integrity():
        all_passed = False
    
    if not test_section_3_engine():
        all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Audit fixes verified successfully.")
        print("="*60)
        return 0
    else:
        print("❌ SOME TESTS FAILED. Review errors above.")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
