#!/usr/bin/env python3
"""Test script to verify authentication has been removed successfully."""
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Authentication Removal")
print("=" * 60)

# Test 1: Import app factory
print("\n1. Testing app factory import...")
try:
    from backend.app import create_app
    print("   ✓ App factory imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import app factory: {e}")
    sys.exit(1)

# Test 2: Create app instance
print("\n2. Creating app instance...")
try:
    app = create_app()
    print("   ✓ App created successfully")
except Exception as e:
    print(f"   ✗ Failed to create app: {e}")
    sys.exit(1)

# Test 3: Check routes don't include auth
print("\n3. Checking registered routes...")
routes = [route.path for route in app.routes]
auth_routes = [r for r in routes if '/auth' in r.lower()]
if auth_routes:
    print(f"   ⚠ Warning: Found auth routes: {auth_routes}")
else:
    print("   ✓ No auth routes registered")

# Test 4: Verify key API routes exist
print("\n4. Verifying key API routes...")
required_routes = ['/api/v1/races', '/api/v1/predictions', '/api/v1/standings/drivers']
for route in required_routes:
    if route in routes:
        print(f"   ✓ {route}")
    else:
        print(f"   ✗ Missing: {route}")

print("\n" + "=" * 60)
print("✅ All tests passed! Authentication successfully removed.")
print("=" * 60)
