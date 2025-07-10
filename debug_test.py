#!/usr/bin/env python3
"""
Quick Backend API Test to debug issues
"""

import requests
import json

BASE_URL = "https://c10ec94f-3259-4138-9605-b8f20b4e5059.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

def test_auth_flow():
    print("Testing authentication flow...")
    
    # Test registration
    user_data = {
        "username": "test_user_debug",
        "email": "test@debug.com",
        "password": "TestPass123!"
    }
    
    print("1. Testing registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data, headers=HEADERS, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Registration successful")
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    # Test login
    print("2. Testing login...")
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=HEADERS, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        token_info = response.json()
        token = token_info["access_token"]
        print("   ✅ Login successful")
        
        # Test protected route
        print("3. Testing protected route...")
        auth_headers = HEADERS.copy()
        auth_headers["Authorization"] = f"Bearer {token}"
        response = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Protected route access successful")
        else:
            print(f"   ❌ Protected route failed: {response.text}")
            
        # Test protected route without auth
        print("4. Testing protected route without auth...")
        response = requests.get(f"{BASE_URL}/auth/me", headers=HEADERS, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 401 or response.status_code == 403:
            print("   ✅ Unauthorized access properly blocked")
        else:
            print(f"   ❌ Unauthorized access not blocked: {response.text}")
            
    else:
        print(f"   ❌ Login failed: {response.text}")

if __name__ == "__main__":
    test_auth_flow()