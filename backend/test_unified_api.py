#!/usr/bin/env python3
"""
Test script for the unified API gateway.
Tests PAT authentication and unified chat completions.
"""
import asyncio
import json
import sys
from typing import Dict, Any

import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_PAT = None  # Will be set from environment or user input

async def test_unified_api():
    """Test the unified API gateway functionality."""
    
    print("🚀 Testing StrataAI Unified API Gateway")
    print("=" * 50)
    
    # Get PAT token
    global TEST_PAT
    TEST_PAT = os.getenv("STRATA_PAT") or input("Enter your Strata PAT token: ").strip()
    
    if not TEST_PAT:
        print("❌ No PAT token provided. Exiting.")
        return
    
    headers = {
        "Authorization": f"Bearer {TEST_PAT}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: List supported providers
        print("\n📋 Test 1: List supported providers")
        try:
            response = await client.get(f"{BASE_URL}/providers")
            if response.status_code == 200:
                data = response.json()
                print("✅ Supported providers:", data["supported_providers"])
                print("📝 Example models:", json.dumps(data["example_models"], indent=2))
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: List available models (requires auth)
        print("\n📋 Test 2: List available models")
        try:
            response = await client.get(f"{BASE_URL}/models", headers=headers)
            if response.status_code == 200:
                data = response.json()
                models = [model["id"] for model in data["data"]]
                print(f"✅ Available models ({len(models)}):", models[:5])  # Show first 5
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: OpenAI chat completion
        print("\n💬 Test 3: OpenAI chat completion")
        openai_request = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Say 'Hello from OpenAI via StrataAI!' in exactly those words."}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions", 
                headers=headers, 
                json=openai_request
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ OpenAI Response: {content}")
                print(f"📊 Usage: {data.get('usage', 'N/A')}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Anthropic chat completion
        print("\n💬 Test 4: Anthropic chat completion")
        anthropic_request = {
            "model": "anthropic/claude-3-haiku-20240307",
            "messages": [
                {"role": "user", "content": "Say 'Hello from Anthropic via StrataAI!' in exactly those words."}
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions", 
                headers=headers, 
                json=anthropic_request
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ Anthropic Response: {content}")
                print(f"📊 Usage: {data.get('usage', 'N/A')}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Streaming chat completion
        print("\n🌊 Test 5: Streaming chat completion")
        stream_request = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            "stream": True,
            "max_tokens": 50
        }
        
        try:
            async with client.stream(
                "POST", 
                f"{BASE_URL}/chat/completions/stream", 
                headers=headers, 
                json=stream_request
            ) as response:
                if response.status_code == 200:
                    print("✅ Streaming response:")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_part = line[6:]
                            if data_part.strip() == "[DONE]":
                                print("🏁 Stream completed")
                                break
                            try:
                                chunk_data = json.loads(data_part)
                                if "choices" in chunk_data and chunk_data["choices"]:
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        print(f"📝 {delta['content']}", end="", flush=True)
                            except json.JSONDecodeError:
                                continue
                    print()  # New line after streaming
                else:
                    print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 6: Error handling - invalid model
        print("\n❌ Test 6: Error handling (invalid model)")
        error_request = {
            "model": "invalid/model-name",
            "messages": [
                {"role": "user", "content": "This should fail"}
            ]
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions", 
                headers=headers, 
                json=error_request
            )
            if response.status_code != 200:
                print(f"✅ Correctly handled error: {response.status_code}")
                error_data = response.json()
                print(f"📝 Error message: {error_data.get('detail', 'N/A')}")
            else:
                print("❌ Should have failed but didn't")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 7: Authentication error
        print("\n🔐 Test 7: Authentication error (invalid PAT)")
        invalid_headers = {
            "Authorization": "Bearer invalid_pat_token",
            "Content-Type": "application/json"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/chat/completions", 
                headers=invalid_headers, 
                json=openai_request
            )
            if response.status_code == 401:
                print("✅ Correctly rejected invalid PAT")
            else:
                print(f"❌ Expected 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Unified API Gateway testing completed!")
    print("\n💡 Usage example for your users:")
    print(f"""
import requests

headers = {{"Authorization": "Bearer {{STRATA_PAT}}"}}
data = {{
    "model": "openai/gpt-3.5-turbo",  # or "anthropic/claude-3-haiku"
    "messages": [{{"role": "user", "content": "Hello!"}}]
}}

response = requests.post(
    "{BASE_URL}/chat/completions", 
    headers=headers, 
    json=data
)
print(response.json())
""")

if __name__ == "__main__":
    asyncio.run(test_unified_api())
