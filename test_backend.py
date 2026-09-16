#!/usr/bin/env python3
"""Quick test to verify backend API endpoints work correctly."""
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing F1 Predictor 2026 Backend")
print("=" * 60)

# Test 1: Import and create app
print("\n1. Creating FastAPI app...")
try:
    from backend.app import create_app
    app = create_app()
    print(f"   ✓ App created successfully with {len(app.routes)} routes")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check critical routes exist
print("\n2. Checking critical routes...")
routes = [route.path for route in app.routes]
critical_routes = [
    '/api/v1/races',
    '/api/v1/drivers', 
    '/api/v1/standings/drivers',
    '/api/v1/standings/constructors',
    '/health'
]

for route in critical_routes:
    if route in routes:
        print(f"   ✓ {route}")
    else:
        print(f"   ✗ MISSING: {route}")

# Test 3: Verify no auth routes
print("\n3. Verifying auth is disabled...")
auth_routes = [r for r in routes if '/auth' in r.lower()]
if auth_routes:
    print(f"   ⚠ Warning: Found auth routes: {auth_routes}")
else:
    print("   ✓ No auth routes (authentication disabled)")

# Test 4: Test race service directly
print("\n4. Testing race service...")
try:
    from backend.app.services.race_service import race_service
    races = race_service.list_races()
    print(f"   ✓ Race service returned {len(races)} races")
    if len(races) > 0:
        print(f"      First race: {races[0].get('name', 'Unknown')}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 5: Test driver data
print("\n5. Testing driver data...")
try:
    from backend.app.data.driver_data import get_all_enhanced_drivers
    drivers = get_all_enhanced_drivers()
    print(f"   ✓ Driver data returned {len(drivers)} drivers")
    if len(drivers) > 0:
        print(f"      First driver: {drivers[0].get('name', 'Unknown')}")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 6: Test standings service
print("\n6. Testing standings service...")
try:
    from backend.app.services.standings_service import standings_service
    driver_standings = standings_service.get_driver_standings()
    print(f"   ✓ Driver standings retrieved")
    constructor_standings = standings_service.get_constructor_standings()
    print(f"   ✓ Constructor standings retrieved")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
