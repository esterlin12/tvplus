#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Live Streaming Platform
Tests all authentication, channel management, super user, and admin features
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://c10ec94f-3259-4138-9605-b8f20b4e5059.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data
TEST_USERS = {
    "regular_user": {
        "username": "sarah_johnson",
        "email": "sarah.johnson@streamtv.com",
        "password": "SecurePass123!"
    },
    "content_creator": {
        "username": "mike_streams",
        "email": "mike.streams@livecast.com", 
        "password": "Creator2024#"
    },
    "admin_user": {
        "username": "admin_alex",
        "email": "alex.admin@platform.com",
        "password": "AdminSecure456$"
    }
}

TEST_CHANNELS = [
    {
        "name": "Tech News Live",
        "description": "Latest technology news and updates from around the world",
        "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "urls": [
            "https://stream.example.com/tech-news.m3u8",
            "https://backup.example.com/tech-news.m3u8",
            "https://cdn.example.com/tech-live"
        ],
        "category": "Technology"
    },
    {
        "name": "Sports Central",
        "description": "Live sports coverage and highlights",
        "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "urls": [
            "https://sports.example.com/live.m3u8",
            "https://sports-backup.example.com/stream"
        ],
        "category": "Sports"
    },
    {
        "name": "Music 24/7",
        "description": "Non-stop music streaming channel",
        "urls": [
            "https://music.example.com/live.m3u8",
            "https://music-stream.example.com/24-7.m3u8"
        ],
        "category": "Music"
    }
]

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.tokens = {}
        self.user_ids = {}
        self.channel_ids = []
        
    def log_success(self, test_name):
        self.passed += 1
        print(f"✅ {test_name}")
        
    def log_failure(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        
        if self.errors:
            print(f"\n{'='*60}")
            print("FAILED TESTS:")
            print(f"{'='*60}")
            for error in self.errors:
                print(f"• {error}")

def make_request(method, endpoint, data=None, headers=None, auth_token=None):
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    request_headers = HEADERS.copy()
    
    if headers:
        request_headers.update(headers)
        
    if auth_token:
        request_headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=request_headers, params=data, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=request_headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=request_headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=request_headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        print(f"DEBUG: {method} {endpoint} -> {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_user_authentication(results):
    """Test user authentication system"""
    print(f"\n{'='*60}")
    print("TESTING USER AUTHENTICATION SYSTEM")
    print(f"{'='*60}")
    
    # Test 1: User Registration
    for user_type, user_data in TEST_USERS.items():
        response = make_request("POST", "/auth/register", user_data)
        if response and response.status_code == 200:
            user_info = response.json()
            results.user_ids[user_type] = user_info["id"]
            results.log_success(f"User registration - {user_type}")
        else:
            error_msg = response.text if response else "No response"
            results.log_failure(f"User registration - {user_type}", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: User Login
    for user_type, user_data in TEST_USERS.items():
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        response = make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            token_info = response.json()
            results.tokens[user_type] = token_info["access_token"]
            results.log_success(f"User login - {user_type}")
        else:
            error_msg = response.text if response else "No response"
            results.log_failure(f"User login - {user_type}", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 3: Get current user info (authenticated)
    for user_type in TEST_USERS.keys():
        if user_type in results.tokens:
            response = make_request("GET", "/auth/me", auth_token=results.tokens[user_type])
            if response and response.status_code == 200:
                results.log_success(f"Get current user info - {user_type}")
            else:
                error_msg = response.text if response else "No response"
                results.log_failure(f"Get current user info - {user_type}", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 4: Test protected route without authentication
    response = make_request("GET", "/auth/me")
    if response and response.status_code == 401:
        results.log_success("Protected route without auth (should fail)")
    else:
        results.log_failure("Protected route without auth", f"Expected 401, got {response.status_code if response else 'None'}")

def test_channel_management(results):
    """Test channel management CRUD operations"""
    print(f"\n{'='*60}")
    print("TESTING CHANNEL MANAGEMENT CRUD")
    print(f"{'='*60}")
    
    if "regular_user" not in results.tokens:
        results.log_failure("Channel CRUD tests", "No authentication token available")
        return
    
    # Test 1: Create channels
    for i, channel_data in enumerate(TEST_CHANNELS):
        response = make_request("POST", "/channels", channel_data, auth_token=results.tokens["regular_user"])
        if response and response.status_code == 200:
            channel_info = response.json()
            results.channel_ids.append(channel_info["id"])
            results.log_success(f"Create channel - {channel_data['name']}")
        else:
            error_msg = response.text if response else "No response"
            results.log_failure(f"Create channel - {channel_data['name']}", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Get all channels (public endpoint)
    response = make_request("GET", "/channels")
    if response and response.status_code == 200:
        channels = response.json()
        results.log_success(f"Get all channels (found {len(channels)} channels)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Get all channels", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 3: Get single channel
    if results.channel_ids:
        channel_id = results.channel_ids[0]
        response = make_request("GET", f"/channels/{channel_id}")
        if response and response.status_code == 200:
            results.log_success("Get single channel")
        else:
            error_msg = response.text if response else "No response"
            results.log_failure("Get single channel", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 4: Update channel (owner)
    if results.channel_ids:
        channel_id = results.channel_ids[0]
        update_data = {
            "name": "Tech News Live - Updated",
            "description": "Updated description for tech news channel",
            "urls": ["https://updated.example.com/tech.m3u8"],
            "category": "Technology"
        }
        response = make_request("PUT", f"/channels/{channel_id}", update_data, auth_token=results.tokens["regular_user"])
        if response and response.status_code == 200:
            results.log_success("Update channel (owner)")
        else:
            error_msg = response.text if response else "No response"
            results.log_failure("Update channel (owner)", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 5: Get user's own channels
    response = make_request("GET", "/my-channels", auth_token=results.tokens["regular_user"])
    if response and response.status_code == 200:
        my_channels = response.json()
        results.log_success(f"Get my channels (found {len(my_channels)} channels)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Get my channels", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 6: Test invalid URL validation
    invalid_channel = {
        "name": "Invalid Channel",
        "description": "Channel with invalid URLs",
        "urls": ["not-a-valid-url", "also-invalid"],
        "category": "Test"
    }
    response = make_request("POST", "/channels", invalid_channel, auth_token=results.tokens["regular_user"])
    if response and response.status_code == 400:
        results.log_success("URL validation (should reject invalid URLs)")
    else:
        results.log_failure("URL validation", f"Expected 400, got {response.status_code if response else 'None'}")

def test_super_user_features(results):
    """Test super user M3U8 downloads and admin features"""
    print(f"\n{'='*60}")
    print("TESTING SUPER USER FEATURES")
    print(f"{'='*60}")
    
    if "admin_user" not in results.tokens or "regular_user" not in results.user_ids:
        results.log_failure("Super user tests", "Missing required tokens or user IDs")
        return
    
    # Test 1: Promote user to super user (using admin_user as existing super user)
    # First, we need to make admin_user a super user manually for testing
    regular_user_id = results.user_ids["regular_user"]
    response = make_request("POST", f"/admin/users/{regular_user_id}/make-super", auth_token=results.tokens["admin_user"])
    if response and response.status_code == 200:
        results.log_success("Promote user to super user")
    else:
        # This might fail if admin_user is not already a super user, which is expected
        results.log_failure("Promote user to super user", f"Status: {response.status_code if response else 'None'} - Admin user may not be super user yet")
    
    # Test 2: Test M3U8 download with regular user (should fail)
    if results.channel_ids:
        channel_id = results.channel_ids[0]
        response = make_request("GET", f"/channels/{channel_id}/m3u8", auth_token=results.tokens["regular_user"])
        if response and response.status_code == 403:
            results.log_success("M3U8 download with regular user (should fail)")
        else:
            results.log_failure("M3U8 download access control", f"Expected 403, got {response.status_code if response else 'None'}")
    
    # Test 3: Test M3U8 download without authentication
    if results.channel_ids:
        channel_id = results.channel_ids[0]
        response = make_request("GET", f"/channels/{channel_id}/m3u8")
        if response and response.status_code == 401:
            results.log_success("M3U8 download without auth (should fail)")
        else:
            results.log_failure("M3U8 download without auth", f"Expected 401, got {response.status_code if response else 'None'}")

def test_channel_search_filtering(results):
    """Test channel search and filtering functionality"""
    print(f"\n{'='*60}")
    print("TESTING CHANNEL SEARCH AND FILTERING")
    print(f"{'='*60}")
    
    # Test 1: Search channels by name
    response = make_request("GET", "/channels", {"search": "Tech"})
    if response and response.status_code == 200:
        channels = response.json()
        results.log_success(f"Search channels by name (found {len(channels)} channels)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Search channels by name", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Filter channels by category
    response = make_request("GET", "/channels", {"category": "Technology"})
    if response and response.status_code == 200:
        channels = response.json()
        results.log_success(f"Filter channels by category (found {len(channels)} channels)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Filter channels by category", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 3: Get categories
    response = make_request("GET", "/categories")
    if response and response.status_code == 200:
        categories_data = response.json()
        categories = categories_data.get("categories", [])
        results.log_success(f"Get categories (found {len(categories)} categories)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Get categories", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 4: Combined search and filter
    response = make_request("GET", "/channels", {"search": "Live", "category": "Sports"})
    if response and response.status_code == 200:
        channels = response.json()
        results.log_success(f"Combined search and filter (found {len(channels)} channels)")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Combined search and filter", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")

def test_admin_panel_features(results):
    """Test admin panel features"""
    print(f"\n{'='*60}")
    print("TESTING ADMIN PANEL FEATURES")
    print(f"{'='*60}")
    
    if "admin_user" not in results.tokens:
        results.log_failure("Admin panel tests", "No admin token available")
        return
    
    # Test 1: Get all channels (admin)
    response = make_request("GET", "/admin/channels", auth_token=results.tokens["admin_user"])
    if response and response.status_code == 200:
        channels = response.json()
        results.log_success(f"Admin get all channels (found {len(channels)} channels)")
    elif response and response.status_code == 403:
        results.log_failure("Admin get all channels", "Access denied - admin user may not be super user")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Admin get all channels", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Get all users (admin)
    response = make_request("GET", "/admin/users", auth_token=results.tokens["admin_user"])
    if response and response.status_code == 200:
        users = response.json()
        results.log_success(f"Admin get all users (found {len(users)} users)")
    elif response and response.status_code == 403:
        results.log_failure("Admin get all users", "Access denied - admin user may not be super user")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Admin get all users", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 3: Test admin access with regular user (should fail)
    if "regular_user" in results.tokens:
        response = make_request("GET", "/admin/channels", auth_token=results.tokens["regular_user"])
        if response and response.status_code == 403:
            results.log_success("Admin access with regular user (should fail)")
        else:
            results.log_failure("Admin access control", f"Expected 403, got {response.status_code if response else 'None'}")

def test_error_handling(results):
    """Test various error handling scenarios"""
    print(f"\n{'='*60}")
    print("TESTING ERROR HANDLING")
    print(f"{'='*60}")
    
    # Test 1: Invalid credentials
    invalid_login = {"username": "nonexistent", "password": "wrongpass"}
    response = make_request("POST", "/auth/login", invalid_login)
    if response and response.status_code == 401:
        results.log_success("Invalid credentials (should fail)")
    else:
        results.log_failure("Invalid credentials handling", f"Expected 401, got {response.status_code if response else 'None'}")
    
    # Test 2: Duplicate user registration
    if TEST_USERS:
        first_user = list(TEST_USERS.values())[0]
        response = make_request("POST", "/auth/register", first_user)
        if response and response.status_code == 400:
            results.log_success("Duplicate user registration (should fail)")
        else:
            results.log_failure("Duplicate user handling", f"Expected 400, got {response.status_code if response else 'None'}")
    
    # Test 3: Invalid channel ID
    response = make_request("GET", "/channels/invalid-channel-id")
    if response and response.status_code == 404:
        results.log_success("Invalid channel ID (should fail)")
    else:
        results.log_failure("Invalid channel ID handling", f"Expected 404, got {response.status_code if response else 'None'}")
    
    # Test 4: Update channel without ownership
    if results.channel_ids and "content_creator" in results.tokens:
        channel_id = results.channel_ids[0]  # Created by regular_user
        update_data = {"name": "Unauthorized Update", "description": "Should fail", "urls": ["https://test.com"]}
        response = make_request("PUT", f"/channels/{channel_id}", update_data, auth_token=results.tokens["content_creator"])
        if response and response.status_code == 403:
            results.log_success("Update channel without ownership (should fail)")
        else:
            results.log_failure("Channel ownership validation", f"Expected 403, got {response.status_code if response else 'None'}")

def test_basic_endpoints(results):
    """Test basic API endpoints"""
    print(f"\n{'='*60}")
    print("TESTING BASIC ENDPOINTS")
    print(f"{'='*60}")
    
    # Test 1: Root endpoint
    response = make_request("GET", "/")
    if response and response.status_code == 200:
        results.log_success("Root endpoint")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Root endpoint", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Health check
    response = make_request("GET", "/health")
    if response and response.status_code == 200:
        results.log_success("Health check endpoint")
    else:
        error_msg = response.text if response else "No response"
        results.log_failure("Health check endpoint", f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")

def cleanup_test_data(results):
    """Clean up test data"""
    print(f"\n{'='*60}")
    print("CLEANING UP TEST DATA")
    print(f"{'='*60}")
    
    # Delete created channels
    if "regular_user" in results.tokens:
        for channel_id in results.channel_ids:
            response = make_request("DELETE", f"/channels/{channel_id}", auth_token=results.tokens["regular_user"])
            if response and response.status_code == 200:
                print(f"✅ Deleted channel {channel_id}")
            else:
                print(f"❌ Failed to delete channel {channel_id}")

def main():
    """Main test execution"""
    print("🚀 Starting Live Streaming Platform Backend API Tests")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = TestResults()
    
    try:
        # Run all test suites
        test_basic_endpoints(results)
        test_user_authentication(results)
        test_channel_management(results)
        test_channel_search_filtering(results)
        test_super_user_features(results)
        test_admin_panel_features(results)
        test_error_handling(results)
        
        # Cleanup
        cleanup_test_data(results)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        results.log_failure("Test execution", str(e))
    
    finally:
        results.print_summary()
        
        # Return appropriate exit code
        if results.failed > 0:
            print(f"\n⚠️  {results.failed} tests failed. Check the errors above.")
            sys.exit(1)
        else:
            print(f"\n🎉 All {results.passed} tests passed!")
            sys.exit(0)

if __name__ == "__main__":
    main()