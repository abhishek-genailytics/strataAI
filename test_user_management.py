#!/usr/bin/env python3
"""
Test script for user management system
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your backend runs on a different port
API_BASE = f"{BASE_URL}/api"

def test_organization_creation():
    """Test creating an organization"""
    print("Testing organization creation...")
    
    # First, we need to authenticate (this would normally be done via Supabase Auth)
    # For testing, we'll assume the user is already authenticated
    
    org_data = {
        "name": "test-org",
        "display_name": "Test Organization",
        "domain": "test.com"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/organizations/",
            json=org_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            org = response.json()
            print(f"✅ Organization created: {org['name']} (ID: {org['id']})")
            return org['id']
        else:
            print(f"❌ Failed to create organization: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
        return None

def test_user_invitation(org_id):
    """Test inviting a user to the organization"""
    print(f"\nTesting user invitation for organization {org_id}...")
    
    invitation_data = {
        "email": "test@example.com",
        "role": "member"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/user-management/invite",
            json=invitation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            invitation = response.json()
            print(f"✅ User invitation created: {invitation['email']} (Role: {invitation['role']})")
            return invitation['id']
        else:
            print(f"❌ Failed to create invitation: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error creating invitation: {e}")
        return None

def test_get_organization_users(org_id):
    """Test getting organization users"""
    print(f"\nTesting get organization users for {org_id}...")
    
    try:
        response = requests.get(
            f"{API_BASE}/user-management/users",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} users in organization")
            for user in users:
                print(f"  - {user['email']} ({user['role']})")
            return users
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return []

def test_create_personal_access_token():
    """Test creating a personal access token"""
    print("\nTesting personal access token creation...")
    
    token_data = {
        "name": "test-token",
        "scopes": ["api:read", "api:write"],
        "expires_at": (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/user-management/tokens",
            json=token_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token = response.json()
            print(f"✅ Token created: {token['name']}")
            print(f"  Token: {token['token'][:20]}...")
            print(f"  Prefix: {token['token_prefix']}")
            return token['id']
        else:
            print(f"❌ Failed to create token: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        return None

def test_get_personal_access_tokens():
    """Test getting personal access tokens"""
    print("\nTesting get personal access tokens...")
    
    try:
        response = requests.get(
            f"{API_BASE}/user-management/tokens",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            print(f"✅ Found {len(tokens)} tokens")
            for token in tokens:
                print(f"  - {token['name']} ({token['token_prefix']})")
            return tokens
        else:
            print(f"❌ Failed to get tokens: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        print(f"❌ Error getting tokens: {e}")
        return []

def main():
    """Run all tests"""
    print("🧪 Testing User Management System")
    print("=" * 50)
    
    # Note: These tests require authentication
    # In a real scenario, you would need to:
    # 1. Authenticate with Supabase Auth
    # 2. Get a valid JWT token
    # 3. Include the token in the Authorization header
    
    print("⚠️  Note: These tests require authentication.")
    print("   Make sure you're logged in and have a valid JWT token.")
    print("   You may need to manually add the Authorization header to the requests.")
    print()
    
    # Test organization creation
    org_id = test_organization_creation()
    
    if org_id:
        # Test user invitation
        invitation_id = test_user_invitation(org_id)
        
        # Test getting users
        users = test_get_organization_users(org_id)
        
        # Test token creation
        token_id = test_create_personal_access_token()
        
        # Test getting tokens
        tokens = test_get_personal_access_tokens()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nNext steps:")
    print("1. Start your backend server: uvicorn app.main:app --reload")
    print("2. Start your frontend: npm start")
    print("3. Log in to the application")
    print("4. Navigate to the Access Management page")
    print("5. Test the user invitation and token creation features")

if __name__ == "__main__":
    main()
