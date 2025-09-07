#!/usr/bin/env python3
"""
Task 17 Manual Verification: Direct testing of stream enforcement
"""

import requests
import json

def test_with_real_server():
    """Test against running server to verify headers and JSON response."""
    
    print("🧪 Manual Verification of Task 17 Implementation\n")
    
    # Test 1: Stream=true should return JSON with headers
    print("1. Testing stream=true → JSON response with headers")
    
    payload = {
        "model": "anthropic/claude-3-haiku-20240307",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={
                "Authorization": "Bearer task17-test-token-12345",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        # Check for our custom headers
        stream_disabled = response.headers.get('x-stream-disabled')
        stream_reason = response.headers.get('x-stream-reason')
        
        if stream_disabled:
            print(f"   ✅ X-Stream-Disabled: {stream_disabled}")
        else:
            print("   ❌ X-Stream-Disabled header missing")
            
        if stream_reason:
            print(f"   ✅ X-Stream-Reason: {stream_reason}")
        else:
            print("   ❌ X-Stream-Reason header missing")
        
        # Verify JSON response
        if response.headers.get('content-type', '').startswith('application/json'):
            print("   ✅ Response is JSON (not SSE)")
            try:
                data = response.json()
                if 'object' in data and data['object'] == 'chat.completion':
                    print("   ✅ Valid OpenAI chat completion format")
                else:
                    print(f"   ⚠️  Response format: {data}")
            except:
                print("   ❌ Invalid JSON response")
        else:
            print(f"   ❌ Not JSON: {response.headers.get('content-type')}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print()
    
    # Test 2: No stream parameter should not have headers
    print("2. Testing no stream parameter → normal JSON without headers")
    
    payload_no_stream = {
        "model": "anthropic/claude-3-haiku-20240307", 
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={
                "Authorization": "Bearer task17-test-token-12345",
                "Content-Type": "application/json"
            },
            json=payload_no_stream
        )
        
        print(f"   Status: {response.status_code}")
        
        # These headers should NOT be present
        if 'x-stream-disabled' not in response.headers:
            print("   ✅ X-Stream-Disabled header correctly absent")
        else:
            print("   ❌ X-Stream-Disabled header should not be present")
            
        if 'x-stream-reason' not in response.headers:
            print("   ✅ X-Stream-Reason header correctly absent")
        else:
            print("   ❌ X-Stream-Reason header should not be present")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    test_with_real_server()
