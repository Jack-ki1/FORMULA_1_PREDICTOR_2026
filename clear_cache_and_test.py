"""
Cache Clearer & Diagnostic Script for F1 Predictor v3.0.

Clears all Python bytecode caches and runs diagnostic tests to find None comparison errors.

Run: py clear_cache_and_test.py
"""

import os
import sys
import shutil
from pathlib import Path

print("=" * 70)
print("F1 Predictor v3.0 - Cache Cleaner & Diagnostic")
print("=" * 70)

# ── Step 1: Clear all __pycache__ directories ──────────────────────────────────

print("\n[Step 1] Clearing Python bytecode cache...")

project_root = Path(__file__).parent
cache_dirs = list(project_root.rglob("__pycache__"))

if cache_dirs:
    print(f"  Found {len(cache_dirs)} __pycache__ directories")
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✅ Deleted: {cache_dir}")
        except Exception as e:
            print(f"  ❌ Failed to delete {cache_dir}: {e}")
else:
    print("  No __pycache__ directories found")

# Also delete .pyc files
pyc_files = list(project_root.rglob("*.pyc"))
if pyc_files:
    print(f"  Found {len(pyc_files)} .pyc files")
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
        except Exception as e:
            print(f"  ❌ Failed to delete {pyc_file}: {e}")

print("  ✅ Cache cleared!")

# ── Step 2: Diagnostic Test ────────────────────────────────────────────────────

print("\n[Step 2] Running diagnostic tests...")

try:
    print("\n  2.1: Testing data.season_2026 import...")
    from data.season_2026 import DRIVER_STANDINGS_AFTER_R5, CONSTRUCTOR_STANDINGS
    print(f"    ✅ DRIVER_STANDINGS_AFTER_R5 loaded: {len(DRIVER_STANDINGS_AFTER_R5)} drivers")
    
    # Check for None values
    print("\n  2.2: Checking for None values in standings...")
    none_found = False
    for idx, driver in enumerate(DRIVER_STANDINGS_AFTER_R5[:5]):
        position = driver.get("position")
        points = driver.get("points")
        print(f"    Driver {idx+1}: position={position} (type={type(position).__name__}), points={points}")
        if position is None:
            none_found = True
            print(f"    ❌ FOUND NONE at index {idx}!")
    
    if none_found:
        print("  ❌ ERROR: None values found in standings!")
        sys.exit(1)
    else:
        print("  ✅ No None values in first 5 drivers")
    
    # Test full comparison
    print("\n  2.3: Testing position comparison...")
    for driver in DRIVER_STANDINGS_AFTER_R5:
        pos = driver.get("position")
        if pos is not None:
            if pos <= 3:  # This is the comparison that was failing
                pass
        else:
            print(f"  ❌ Found None position for driver: {driver.get('driver')}")
            sys.exit(1)
    
    print("  ✅ All position comparisons successful!")
    
    # Test feature engineering import
    print("\n  2.4: Testing engine.feature_engineering import...")
    from engine.feature_engineering import compute_grid_position_score
    print("  ✅ Feature engineering loaded successfully")
    
    # Test vectorized simulation
    print("\n  2.5: Testing engine.vectorized_simulation import...")
    from engine.vectorized_simulation import simulate_race_vectorized
    print("  ✅ Vectorized simulation loaded successfully")
    
    # Test prediction tracker
    print("\n  2.6: Testing engine.prediction_tracker import...")
    from engine.prediction_tracker import PredictionTracker
    print("  ✅ Prediction tracker loaded successfully")
    
    # Test API schemas
    print("\n  2.7: Testing api.schemas import...")
    from api.schemas import PredictionRequest, PredictionResponse
    print("  ✅ API schemas loaded successfully")
    
    # Test core prediction
    print("\n  2.8: Testing core prediction engine...")
    from engine.predictor import predict, PredictionRequest as PR
    result = predict(PR(
        circuit_id="canada",
        rain_probability=0.2,
        n_simulations=500,
    ))
    print(f"  ✅ Prediction successful: {len(result['predictions'])} drivers")
    print(f"  ✅ Podium: {result['podium_predictions'][:3]}")
    
    print("\n" + "=" * 70)
    print("✅ ALL DIAGNOSTIC TESTS PASSED!")
    print("=" * 70)
    print("\nYou can now run: py test_v3_complete.py")
    
except Exception as e:
    print(f"\n❌ DIAGNOSTIC FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




