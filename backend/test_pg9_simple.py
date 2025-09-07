#!/usr/bin/env python3
"""
Simple PG-9 Send Pipeline Test
Tests the playground chat completions endpoint to verify basic functionality.
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime

async def test_playground_endpoint():
    """Test the playground chat completions endpoint."""
    
    print("🧪 Testing PG-9 Send Pipeline")
    print("=" * 50)
    
    # Test configuration
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        
        # Test 1: Basic endpoint availability
        print("\n1. Testing endpoint availability...")
        try:
            response = await client.get("/api/v1/playground/health")
            print(f"   Health check: {response.status_code}")
        except Exception as e:
            print(f"   Health check failed: {e}")
        
        # Test 2: Chat completions endpoint structure
        print("\n2. Testing chat completions endpoint...")
        
        headers = {
            "Content-Type": "application/json",
            "X-Session-ID": str(uuid.uuid4()),
            "X-Client-Message-ID": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }
        
        request_data = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "Hello! This is a test message."}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        try:
            response = await client.post(
                "/api/v1/playground/chat/completions",
                json=request_data,
                headers=headers
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response structure: {list(data.keys())}")
                
                # Check OpenAI compatibility
                if "object" in data and data["object"] == "chat.completion":
                    print("   ✅ OpenAI-compatible response structure")
                else:
                    print("   ❌ Missing OpenAI compatibility")
                
                if "choices" in data and len(data["choices"]) > 0:
                    print("   ✅ Has choices array")
                else:
                    print("   ❌ Missing choices")
                
                if "usage" in data:
                    print("   ✅ Has usage data")
                    print(f"   Usage: {data['usage']}")
                else:
                    print("   ❌ Missing usage data")
                
            else:
                print(f"   Response body: {response.text}")
                
        except Exception as e:
            print(f"   Request failed: {e}")
        
        # Test 3: Error handling (invalid model)
        print("\n3. Testing error handling...")
        
        error_request = {
            "model": "invalid/model",
            "messages": [
                {"role": "user", "content": "This should fail"}
            ]
        }
        
        try:
            response = await client.post(
                "/api/v1/playground/chat/completions",
                json=error_request,
                headers=headers
            )
            
            print(f"   Error status: {response.status_code}")
            
            if response.status_code >= 400:
                error_data = response.json()
                if "error" in error_data:
                    print("   ✅ OpenAI-style error format")
                    print(f"   Error: {error_data['error']}")
                else:
                    print("   ❌ Non-OpenAI error format")
                    print(f"   Response: {error_data}")
            
        except Exception as e:
            print(f"   Error test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_playground_endpoint())
