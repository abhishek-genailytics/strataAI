#!/usr/bin/env python3
"""
Test script to verify Supabase connection and data availability.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_supabase_connection():
    """Test Supabase connection and check for data."""
    try:
        from app.utils.supabase_client import get_supabase_client
        
        print("🔗 Testing Supabase connection...")
        supabase = get_supabase_client()
        
        # Test providers table
        print("\n📋 Checking ai_providers table...")
        providers_response = supabase.table("ai_providers").select("*").limit(5).execute()
        print(f"Found {len(providers_response.data or [])} providers")
        
        if providers_response.data:
            for provider in providers_response.data[:3]:
                print(f"  - {provider.get('display_name', 'Unknown')} ({provider.get('name', 'unknown')})")
        
        # Test models table
        print("\n🤖 Checking ai_models table...")
        models_response = supabase.table("ai_models").select("*").limit(5).execute()
        print(f"Found {len(models_response.data or [])} models")
        
        if models_response.data:
            for model in models_response.data[:3]:
                print(f"  - {model.get('display_name', 'Unknown')} ({model.get('model_name', 'unknown')})")
        
        # Test model pricing table
        print("\n💰 Checking model_pricing table...")
        pricing_response = supabase.table("model_pricing").select("*").limit(5).execute()
        print(f"Found {len(pricing_response.data or [])} pricing entries")
        
        # Test API keys table
        print("\n🔑 Checking api_keys table...")
        api_keys_response = supabase.table("api_keys").select("*").limit(5).execute()
        print(f"Found {len(api_keys_response.data or [])} API keys")
        
        print("\n✅ Supabase connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Supabase connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
