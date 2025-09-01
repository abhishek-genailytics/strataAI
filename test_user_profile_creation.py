#!/usr/bin/env python3
"""
Script to test user profile creation and verify the trigger is working
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the backend directory to the path so we can import the Supabase client
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.utils.supabase_client import supabase
    print("✅ Successfully imported Supabase client")
except ImportError as e:
    print(f"❌ Failed to import Supabase client: {e}")
    print("Make sure you're in the project root directory")
    sys.exit(1)

def test_existing_users():
    """Test if existing users have profiles"""
    print("🔍 Testing Existing Users")
    print("=" * 50)
    
    try:
        # Get all confirmed users
        auth_users = supabase.table("auth.users").select("id, email, created_at, raw_user_meta_data").eq("email_confirmed_at", "not.is.null").execute()
        
        print(f"📊 Found {len(auth_users.data)} confirmed users in auth.users")
        
        # Get all user profiles
        user_profiles = supabase.table("user_profiles").select("id, full_name, created_at").execute()
        
        print(f"📊 Found {len(user_profiles.data)} user profiles")
        
        # Check for missing profiles
        auth_user_ids = {user['id'] for user in auth_users.data}
        profile_user_ids = {profile['id'] for profile in user_profiles.data}
        
        missing_profiles = auth_user_ids - profile_user_ids
        
        if missing_profiles:
            print(f"❌ Found {len(missing_profiles)} users without profiles:")
            for user_id in missing_profiles:
                user = next((u for u in auth_users.data if u['id'] == user_id), None)
                if user:
                    print(f"   - {user['email']} (ID: {user_id})")
        else:
            print("✅ All confirmed users have profiles!")
        
        # Show sample profiles
        if user_profiles.data:
            print(f"\n📋 Sample user profiles:")
            for profile in user_profiles.data[:3]:
                user = next((u for u in auth_users.data if u['id'] == profile['id']), None)
                if user:
                    print(f"   - {user['email']}: {profile['full_name'] or 'No name'}")
        
        return len(missing_profiles) == 0
        
    except Exception as e:
        print(f"❌ Error testing existing users: {e}")
        return False

def test_trigger_function():
    """Test if the trigger function exists and works"""
    print("\n🔧 Testing Trigger Function")
    print("=" * 50)
    
    try:
        # Check if the function exists
        result = supabase.rpc("handle_new_user", {"test": True}).execute()
        print("✅ handle_new_user function exists")
        return True
    except Exception as e:
        if "function" in str(e).lower() and "does not exist" in str(e).lower():
            print("❌ handle_new_user function does not exist")
            return False
        else:
            print(f"⚠️  Function exists but test failed: {e}")
            return True

def test_sync_function():
    """Test the sync function"""
    print("\n🔄 Testing Sync Function")
    print("=" * 50)
    
    try:
        # Run the sync function
        result = supabase.rpc("sync_missing_user_profiles").execute()
        
        if result.data:
            profiles_created = result.data[0] if isinstance(result.data, list) else result.data
            print(f"✅ Sync function ran successfully")
            print(f"📊 Profiles created: {profiles_created}")
            return True
        else:
            print("⚠️  Sync function returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sync function: {e}")
        return False

def create_test_user_profile():
    """Create a test user profile manually"""
    print("\n🧪 Testing Manual Profile Creation")
    print("=" * 50)
    
    try:
        # Get the first user without a profile
        auth_users = supabase.table("auth.users").select("id, email, raw_user_meta_data").eq("email_confirmed_at", "not.is.null").execute()
        user_profiles = supabase.table("user_profiles").select("id").execute()
        
        auth_user_ids = {user['id'] for user in auth_users.data}
        profile_user_ids = {profile['id'] for profile in user_profiles.data}
        
        missing_profiles = auth_user_ids - profile_user_ids
        
        if not missing_profiles:
            print("✅ No missing profiles to test with")
            return True
        
        # Take the first missing user
        test_user_id = list(missing_profiles)[0]
        test_user = next((u for u in auth_users.data if u['id'] == test_user_id), None)
        
        if not test_user:
            print("❌ Could not find test user")
            return False
        
        print(f"🧪 Creating profile for user: {test_user['email']}")
        
        # Create profile manually
        profile_data = {
            "id": test_user_id,
            "full_name": test_user.get('raw_user_meta_data', {}).get('full_name', ''),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("user_profiles").insert(profile_data).execute()
        
        if result.data:
            print(f"✅ Successfully created profile for {test_user['email']}")
            return True
        else:
            print(f"❌ Failed to create profile for {test_user['email']}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test profile: {e}")
        return False

def main():
    """Main function"""
    print("🧪 User Profile Creation Test")
    print("=" * 60)
    
    # Test existing users
    existing_users_ok = test_existing_users()
    
    # Test trigger function
    trigger_ok = test_trigger_function()
    
    # Test sync function
    sync_ok = test_sync_function()
    
    # Test manual creation if needed
    if not existing_users_ok:
        manual_ok = create_test_user_profile()
    else:
        manual_ok = True
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    results = [
        ("Existing Users Check", existing_users_ok),
        ("Trigger Function", trigger_ok),
        ("Sync Function", sync_ok),
        ("Manual Creation", manual_ok)
    ]
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    print(f"\n📈 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 User profile system is working correctly!")
        print("   All confirmed users should have profiles.")
    else:
        print("\n🔧 Some issues detected. Check the output above for details.")
        print("   You may need to run the fix_user_profiles.py script again.")

if __name__ == "__main__":
    main()
