#!/usr/bin/env python3
"""
Quick test script to check registration and admin credentials.
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("F1 Predictor 2026 - Registration Test")
print("=" * 60)
print()

# Test 1: Check backend health
print("1. Checking backend health...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("   ✅ Backend is running")
    else:
        print(f"   ❌ Backend returned status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Cannot connect to backend: {e}")
    print("   Is the backend running on port 5000?")
    exit(1)

print()

# Test 2: Try to register a test user
print("2. Testing registration endpoint...")
test_user = {
    "email": f"test_{int(__import__('time').time())}@example.com",
    "username": f"testuser_{int(__import__('time').time())}",
    "password": "TestPass123!",
    "full_name": "Test User"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=test_user,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("   ✅ Registration successful!")
        print(f"   User ID: {data['user']['id']}")
        print(f"   Username: {data['user']['username']}")
        print(f"   Email: {data['user']['email']}")
    else:
        print(f"   ❌ Registration failed")
        print(f"   Response: {response.text}")
        
        # Try to get more details
        try:
            error_data = response.json()
            print(f"   Error details: {json.dumps(error_data, indent=2)}")
        except:
            pass
except Exception as e:
    print(f"   ❌ Request failed: {e}")

print()

# Test 3: Check admin credentials from .env
print("3. Admin Credentials (from .env file):")
print("=" * 60)
try:
    with open('.env', 'r') as f:
        env_content = f.read()
        for line in env_content.split('\n'):
            if line.startswith('ADMIN_'):
                key, value = line.split('=', 1)
                if 'PASSWORD' not in key:
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {'*' * len(value)}")
except FileNotFoundError:
    print("   ⚠️  .env file not found!")

print()
print("=" * 60)
print("DEFAULT ADMIN CREDENTIALS:")
print("=" * 60)
print("   Email:    admin@f1predictor.com")
print("   Username: admin")
print("   Password: F1Admin2026!Secure")
print()
print("⚠️  IMPORTANT: Change the password after first login!")
print("=" * 60)
