#!/usr/bin/env python3
"""
Test authentication system.
Verifies that auth endpoints work correctly.
"""
import sys
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE_URL = "http://localhost:5000"

def test_health():
    """Test if backend is running."""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        return False

def test_register():
    """Test user registration."""
    print("\n📝 Testing user registration...")
    
    # Generate unique test user
    import time
    timestamp = int(time.time())
    test_data = {
        "email": f"test{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Registration successful")
            print(f"   User ID: {data['user']['id']}")
            print(f"   Username: {data['user']['username']}")
            print(f"   Access Token: {data['access_token'][:50]}...")
            return data
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_login(username, password):
    """Test user login."""
    print(f"\n🔐 Testing login for {username}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "email_or_username": username,
                "password": password
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful")
            print(f"   Access Token: {data['access_token'][:50]}...")
            print(f"   Token Type: {data['token_type']}")
            print(f"   Expires In: {data['expires_in']} seconds")
            return data
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_profile(access_token):
    """Test getting user profile."""
    print("\n👤 Testing profile retrieval...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/profile",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile retrieved successfully")
            print(f"   User ID: {data['id']}")
            print(f"   Email: {data['email']}")
            print(f"   Username: {data['username']}")
            print(f"   Is Admin: {data['is_admin']}")
            return data
        else:
            print(f"❌ Profile retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return None

def test_protected_route(access_token):
    """Test accessing a protected route."""
    print("\n🛡️ Testing protected route access...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/races",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Protected route accessible")
            print(f"   Retrieved {len(data)} races")
            return True
        else:
            print(f"❌ Protected route access failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Protected route error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("F1 Predictor 2026 - Authentication System Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not running. Start it first!")
        sys.exit(1)
    
    # Test 2: Registration
    reg_result = test_register()
    if not reg_result:
        print("\n❌ Registration test failed")
        sys.exit(1)
    
    # Test 3: Login with registered user
    login_result = test_login(
        reg_result['user']['username'],
        "TestPassword123!"
    )
    if not login_result:
        print("\n❌ Login test failed")
        sys.exit(1)
    
    # Test 4: Get profile
    profile_result = test_profile(login_result['access_token'])
    if not profile_result:
        print("\n❌ Profile test failed")
        sys.exit(1)
    
    # Test 5: Access protected route
    if not test_protected_route(login_result['access_token']):
        print("\n❌ Protected route test failed")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nAuthentication system is working correctly.")
    print("You can now:")
    print("  1. Register new users at /signup")
    print("  2. Login at /login")
    print("  3. Access all protected routes")
    print("  4. Manage user profiles")

if __name__ == "__main__":
    main()
