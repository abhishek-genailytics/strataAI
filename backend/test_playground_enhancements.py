#!/usr/bin/env python3
"""
Test script for the optional playground enhancements:
- GET /v1/playground/sessions (list sessions with pagination)
- GET /v1/playground/sessions/by-client-id/{client_session_id} (lookup by client ID)
- Enhanced session responses with provider_id and model_id fields
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
PAT_TOKEN = "your-pat-token-here"  # Replace with actual PAT token

def test_playground_enhancements():
    """Test the new playground enhancement endpoints."""
    
    headers = {
        "Authorization": f"Bearer {PAT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Playground Enhancement Endpoints")
    print("=" * 50)
    
    # Test 1: List sessions endpoint
    print("\n1️⃣ Testing GET /v1/playground/sessions")
    try:
        response = requests.get(f"{BASE_URL}/v1/playground/sessions", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sessions found: {len(data.get('sessions', []))}")
            print(f"✅ Next cursor: {data.get('next_cursor')}")
            if data.get('sessions'):
                session = data['sessions'][0]
                print(f"✅ Sample session has provider_id: {session.get('provider_id')}")
                print(f"✅ Sample session has model_id: {session.get('model_id')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: List sessions with pagination
    print("\n2️⃣ Testing GET /v1/playground/sessions with pagination")
    try:
        response = requests.get(f"{BASE_URL}/v1/playground/sessions?limit=5", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Limited sessions: {len(data.get('sessions', []))}")
            if data.get('next_cursor'):
                # Test cursor pagination
                cursor_response = requests.get(
                    f"{BASE_URL}/v1/playground/sessions?cursor={data['next_cursor']}", 
                    headers=headers
                )
                print(f"✅ Cursor pagination status: {cursor_response.status_code}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Get session by client ID (requires existing session with client_session_id)
    print("\n3️⃣ Testing GET /v1/playground/sessions/by-client-id/{client_session_id}")
    try:
        # First, try to get sessions to find one with client_session_id
        sessions_response = requests.get(f"{BASE_URL}/v1/playground/sessions", headers=headers)
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            client_session_id = None
            
            for session in sessions_data.get('sessions', []):
                metadata = session.get('metadata', {})
                if metadata.get('client_session_id'):
                    client_session_id = metadata['client_session_id']
                    break
            
            if client_session_id:
                response = requests.get(
                    f"{BASE_URL}/v1/playground/sessions/by-client-id/{client_session_id}", 
                    headers=headers
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Found session by client ID: {data.get('id')}")
                    print(f"✅ Provider ID: {data.get('provider_id')}")
                    print(f"✅ Model ID: {data.get('model_id')}")
                else:
                    print(f"❌ Error: {response.text}")
            else:
                print("⚠️  No sessions with client_session_id found to test")
        else:
            print(f"❌ Could not fetch sessions: {sessions_response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Enhanced individual session endpoint
    print("\n4️⃣ Testing enhanced GET /v1/playground/sessions/{session_id}")
    try:
        sessions_response = requests.get(f"{BASE_URL}/v1/playground/sessions", headers=headers)
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            if sessions_data.get('sessions'):
                session_id = sessions_data['sessions'][0]['id']
                response = requests.get(f"{BASE_URL}/v1/playground/sessions/{session_id}", headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Session ID: {data.get('id')}")
                    print(f"✅ Provider ID: {data.get('provider_id')}")
                    print(f"✅ Model ID: {data.get('model_id')}")
                    print(f"✅ Message count: {data.get('message_count')}")
                else:
                    print(f"❌ Error: {response.text}")
            else:
                print("⚠️  No sessions found to test individual endpoint")
        else:
            print(f"❌ Could not fetch sessions: {sessions_response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Playground enhancement testing complete!")
    print("\nNote: Replace PAT_TOKEN with a valid token and ensure the server is running.")

if __name__ == "__main__":
    test_playground_enhancements()
