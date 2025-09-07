#!/usr/bin/env python3
"""
Manual PG-7 Test Script

Simple test to verify PG-7 headers are working correctly.
Run this against a local development server.
"""

import requests
import json
import uuid

def test_pg7_headers():
    """Test PG-7 header functionality manually."""
    
    # Test configuration
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/playground/chat/completions"
    
    # Generate test IDs
    session_id = str(uuid.uuid4())
    client_msg_id = str(uuid.uuid4())
    idempotency_key = str(uuid.uuid4())
    
    # Request payload
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message for PG-7"}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id,
        "X-Client-Message-ID": client_msg_id,
        "X-Idempotency-Key": idempotency_key
    }
    
    print("PG-7 Manual Test")
    print("=" * 40)
    print(f"Session ID: {session_id}")
    print(f"Client Message ID: {client_msg_id}")
    print(f"Idempotency Key: {idempotency_key}")
    print()
    
    try:
        # Make request
        print("Sending request...")
        response = requests.post(
            f"{endpoint}?session_id={session_id}",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print()
        
        # Check response headers
        print("Response Headers:")
        pg7_headers = [
            "X-User-Message-ID",
            "X-Assistant-Message-ID", 
            "X-Message-Index-Start",
            "X-Stream-Disabled"
        ]
        
        for header in pg7_headers:
            value = response.headers.get(header, "NOT FOUND")
            status = "✅" if value != "NOT FOUND" else "❌"
            print(f"  {status} {header}: {value}")
        
        print()
        
        # Check response body
        if response.status_code == 200:
            data = response.json()
            print("Response Body:")
            print(f"  ID: {data.get('id', 'NOT FOUND')}")
            print(f"  Model: {data.get('model', 'NOT FOUND')}")
            print(f"  Content: {data.get('choices', [{}])[0].get('message', {}).get('content', 'NOT FOUND')[:50]}...")
            print(f"  Usage: {data.get('usage', 'NOT FOUND')}")
        else:
            print("Error Response:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pg7_headers()
