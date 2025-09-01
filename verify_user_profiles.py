#!/usr/bin/env python3
"""
Script to verify the current state of user profiles
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000/api"

def check_user_profiles():
    """Check the current state of user profiles"""
    print("🔍 Verifying User Profiles")
    print("=" * 50)
    
    # SQL queries to check the state
    queries = [
        {
            "name": "Total users in auth.users",
            "sql": "SELECT COUNT(*) as count FROM auth.users WHERE email_confirmed_at IS NOT NULL"
        },
        {
            "name": "Total user profiles",
            "sql": "SELECT COUNT(*) as count FROM user_profiles"
        },
        {
            "name": "Users without profiles",
            "sql": """
                SELECT COUNT(*) as count 
                FROM auth.users au
                LEFT JOIN user_profiles up ON au.id = up.id
                WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL
            """
        },
        {
            "name": "Sample users without profiles",
            "sql": """
                SELECT au.id, au.email, au.created_at
                FROM auth.users au
                LEFT JOIN user_profiles up ON au.id = up.id
                WHERE up.id IS NULL AND au.email_confirmed_at IS NOT NULL
                LIMIT 5
            """
        },
        {
            "name": "Sample user profiles",
            "sql": """
                SELECT up.id, up.full_name, up.created_at, au.email
                FROM user_profiles up
                JOIN auth.users au ON up.id = au.id
                LIMIT 5
            """
        }
    ]
    
    print("📊 Database State Analysis:")
    print("-" * 30)
    
    for query in queries:
        print(f"\n🔍 {query['name']}:")
        print(f"SQL: {query['sql'].strip()}")
        print("Result: [Run this in your Supabase SQL Editor]")
    
    print("\n📝 Manual Verification Steps:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run each query above to check the state")
    print("4. Verify that all confirmed users have profiles")
    
    print("\n🎯 Expected Results:")
    print("- Total users in auth.users should match total user profiles")
    print("- Users without profiles should be 0")
    print("- All confirmed users should have corresponding profiles")
    
    print("\n🔧 If profiles are missing:")
    print("1. Run the fix_user_profiles.py script")
    print("2. Or manually run the migration SQL")
    print("3. Re-run these verification queries")

def test_user_profile_api():
    """Test the user profile API endpoints"""
    print("\n🌐 Testing User Profile API")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        {
            "name": "Get current user profile",
            "method": "GET",
            "url": f"{API_BASE}/auth/me",
            "requires_auth": True
        },
        {
            "name": "Update user profile",
            "method": "PUT", 
            "url": f"{API_BASE}/auth/profile",
            "requires_auth": True,
            "data": {
                "full_name": "Test User",
                "bio": "Test bio"
            }
        }
    ]
    
    print("📋 API Endpoints to test:")
    for endpoint in endpoints:
        print(f"\n🔗 {endpoint['name']}:")
        print(f"   Method: {endpoint['method']}")
        print(f"   URL: {endpoint['url']}")
        if endpoint.get('requires_auth'):
            print("   Auth: Required (Bearer token)")
        if endpoint.get('data'):
            print(f"   Data: {json.dumps(endpoint['data'], indent=2)}")
    
    print("\n⚠️  Note: These endpoints require authentication.")
    print("   Test them after logging in through the frontend.")

def main():
    """Main function"""
    print("🔍 User Profile Verification Tool")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/status", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("⚠️  Backend responded with unexpected status")
    except requests.exceptions.RequestException:
        print("❌ Backend is not running")
        print("   Start the backend with: cd backend && uvicorn app.main:app --reload")
    
    # Run verification
    check_user_profiles()
    test_user_profile_api()
    
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    print("1. ✅ Checked database queries for verification")
    print("2. ✅ Listed API endpoints for testing")
    print("3. 🔧 Use fix_user_profiles.py to fix missing profiles")
    print("4. 🔍 Run the SQL queries in Supabase to verify results")

if __name__ == "__main__":
    main()
