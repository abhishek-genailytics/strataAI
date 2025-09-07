#!/usr/bin/env python3
"""
PG-7 Acceptance Tests - Message create + optimistic UI (idempotent, reconcilable)

Tests all acceptance criteria:
1. Happy path: optimistic UI with proper reconciliation
2. Retry path: same idempotency key returns cached results
3. Double click: same client_msg_id prevents duplicates
4. Out-of-order sends: concurrent requests with different keys
5. No headers: fallback behavior works correctly
"""

import asyncio
import httpx
import json
import uuid
from typing import Dict, Any, Optional
import time

# Test configuration
BASE_URL = "http://localhost:8000"
PLAYGROUND_ENDPOINT = f"{BASE_URL}/playground/chat/completions"

# Mock session ID for testing (replace with actual session)
TEST_SESSION_ID = "123e4567-e89b-12d3-a456-426614174000"

# Mock authentication headers (replace with actual auth)
AUTH_HEADERS = {
    "Authorization": "Bearer test-token",  # Replace with actual auth
    "Content-Type": "application/json"
}

class TestResults:
    def __init__(self):
        self.results = []
        
    def add_result(self, test_name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append(f"{status} {test_name}: {details}")
        
    def print_summary(self):
        print("\n" + "="*60)
        print("PG-7 ACCEPTANCE TEST RESULTS")
        print("="*60)
        for result in self.results:
            print(result)
        
        passed = sum(1 for r in self.results if "✅ PASS" in r)
        total = len(self.results)
        print(f"\nSUMMARY: {passed}/{total} tests passed")
        print("="*60)

def create_test_request(message: str = "Hello, test message") -> Dict[str, Any]:
    """Create a standard test request payload."""
    return {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }

async def send_request(
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    session_id: str = TEST_SESSION_ID
) -> httpx.Response:
    """Send a request to the playground endpoint."""
    all_headers = {**AUTH_HEADERS}
    if headers:
        all_headers.update(headers)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PLAYGROUND_ENDPOINT}?session_id={session_id}",
            json=payload,
            headers=all_headers,
            timeout=30.0
        )
        return response

async def test_happy_path(results: TestResults):
    """Test 1: Happy path - optimistic UI with proper reconciliation."""
    print("Running Test 1: Happy path...")
    
    client_msg_id = str(uuid.uuid4())
    idempotency_key = str(uuid.uuid4())
    
    headers = {
        "X-Session-ID": TEST_SESSION_ID,
        "X-Client-Message-ID": client_msg_id,
        "X-Idempotency-Key": idempotency_key
    }
    
    try:
        response = await send_request(
            create_test_request("Test happy path message"),
            headers=headers
        )
        
        # Check response status
        if response.status_code != 200:
            results.add_result("Happy Path", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        # Check response headers
        required_headers = ["X-User-Message-ID", "X-Assistant-Message-ID", "X-Message-Index-Start"]
        missing_headers = [h for h in required_headers if h not in response.headers]
        
        if missing_headers:
            results.add_result("Happy Path", False, f"Missing headers: {missing_headers}")
            return
        
        # Check response body
        data = response.json()
        if not data.get("choices") or not data["choices"][0].get("message", {}).get("content"):
            results.add_result("Happy Path", False, "No assistant content in response")
            return
        
        # Check usage data exists
        if not data.get("usage") or data["usage"].get("total_tokens", 0) == 0:
            results.add_result("Happy Path", False, "No usage data in response")
            return
        
        results.add_result("Happy Path", True, 
            f"User ID: {response.headers.get('X-User-Message-ID')[:8]}..., "
            f"Assistant ID: {response.headers.get('X-Assistant-Message-ID')[:8]}...")
        
    except Exception as e:
        results.add_result("Happy Path", False, f"Exception: {str(e)}")

async def test_retry_path(results: TestResults):
    """Test 2: Retry path - same idempotency key returns cached results."""
    print("Running Test 2: Retry path...")
    
    client_msg_id = str(uuid.uuid4())
    idempotency_key = str(uuid.uuid4())
    
    headers = {
        "X-Session-ID": TEST_SESSION_ID,
        "X-Client-Message-ID": client_msg_id,
        "X-Idempotency-Key": idempotency_key
    }
    
    try:
        # First request
        response1 = await send_request(
            create_test_request("Test retry message"),
            headers=headers
        )
        
        if response1.status_code != 200:
            results.add_result("Retry Path", False, f"First request failed: HTTP {response1.status_code}")
            return
        
        # Wait a moment
        await asyncio.sleep(0.1)
        
        # Second request with same idempotency key
        response2 = await send_request(
            create_test_request("Test retry message"),
            headers=headers
        )
        
        if response2.status_code != 200:
            results.add_result("Retry Path", False, f"Second request failed: HTTP {response2.status_code}")
            return
        
        # Compare responses
        data1 = response1.json()
        data2 = response2.json()
        
        # Should have same assistant message IDs
        assistant_id1 = response1.headers.get("X-Assistant-Message-ID")
        assistant_id2 = response2.headers.get("X-Assistant-Message-ID")
        
        if assistant_id1 != assistant_id2:
            results.add_result("Retry Path", False, "Different assistant IDs returned")
            return
        
        # Should have same content
        content1 = data1.get("choices", [{}])[0].get("message", {}).get("content", "")
        content2 = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if content1 != content2:
            results.add_result("Retry Path", False, "Different content returned")
            return
        
        results.add_result("Retry Path", True, f"Same assistant ID returned: {assistant_id1[:8]}...")
        
    except Exception as e:
        results.add_result("Retry Path", False, f"Exception: {str(e)}")

async def test_double_click(results: TestResults):
    """Test 3: Double click - same client_msg_id prevents duplicates."""
    print("Running Test 3: Double click protection...")
    
    client_msg_id = str(uuid.uuid4())
    idempotency_key1 = str(uuid.uuid4())
    idempotency_key2 = str(uuid.uuid4())
    
    headers1 = {
        "X-Session-ID": TEST_SESSION_ID,
        "X-Client-Message-ID": client_msg_id,
        "X-Idempotency-Key": idempotency_key1
    }
    
    headers2 = {
        "X-Session-ID": TEST_SESSION_ID,
        "X-Client-Message-ID": client_msg_id,  # Same client message ID
        "X-Idempotency-Key": idempotency_key2  # Different idempotency key
    }
    
    try:
        # Send two requests quickly with same client_msg_id
        tasks = [
            send_request(create_test_request("Double click test"), headers1),
            send_request(create_test_request("Double click test"), headers2)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Both should succeed
        success_count = 0
        user_ids = set()
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                continue
            if response.status_code == 200:
                success_count += 1
                user_id = response.headers.get("X-User-Message-ID")
                if user_id:
                    user_ids.add(user_id)
        
        if success_count < 2:
            results.add_result("Double Click", False, f"Only {success_count} requests succeeded")
            return
        
        # Should reuse the same user message (same client_msg_id)
        if len(user_ids) == 1:
            results.add_result("Double Click", True, f"Reused user message ID: {list(user_ids)[0][:8]}...")
        else:
            results.add_result("Double Click", False, f"Created {len(user_ids)} different user messages")
        
    except Exception as e:
        results.add_result("Double Click", False, f"Exception: {str(e)}")

async def test_out_of_order(results: TestResults):
    """Test 4: Out-of-order sends - concurrent requests with different keys."""
    print("Running Test 4: Out-of-order sends...")
    
    # Create multiple concurrent requests
    requests = []
    for i in range(3):
        headers = {
            "X-Session-ID": TEST_SESSION_ID,
            "X-Client-Message-ID": str(uuid.uuid4()),
            "X-Idempotency-Key": str(uuid.uuid4())
        }
        requests.append((
            create_test_request(f"Concurrent message {i}"),
            headers
        ))
    
    try:
        # Send all requests concurrently
        tasks = [send_request(payload, headers) for payload, headers in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check all succeeded
        success_count = 0
        indices = []
        
        for response in responses:
            if isinstance(response, Exception):
                continue
            if response.status_code == 200:
                success_count += 1
                index = response.headers.get("X-Message-Index-Start")
                if index:
                    indices.append(int(index))
        
        if success_count < 3:
            results.add_result("Out-of-Order", False, f"Only {success_count}/3 requests succeeded")
            return
        
        # Indices should be sequential (server assigns them in order)
        indices.sort()
        is_sequential = all(indices[i] == indices[0] + i for i in range(len(indices)))
        
        if is_sequential:
            results.add_result("Out-of-Order", True, f"Sequential indices: {indices}")
        else:
            results.add_result("Out-of-Order", False, f"Non-sequential indices: {indices}")
        
    except Exception as e:
        results.add_result("Out-of-Order", False, f"Exception: {str(e)}")

async def test_no_headers(results: TestResults):
    """Test 5: No headers - fallback behavior works correctly."""
    print("Running Test 5: No headers fallback...")
    
    try:
        # Send request without PG-7 headers
        response = await send_request(
            create_test_request("No headers test message")
        )
        
        if response.status_code != 200:
            results.add_result("No Headers", False, f"HTTP {response.status_code}: {response.text}")
            return
        
        # Should still return response headers (server generates them)
        required_headers = ["X-User-Message-ID", "X-Assistant-Message-ID", "X-Message-Index-Start"]
        missing_headers = [h for h in required_headers if h not in response.headers]
        
        if missing_headers:
            results.add_result("No Headers", False, f"Missing headers: {missing_headers}")
            return
        
        # Should have valid response body
        data = response.json()
        if not data.get("choices") or not data["choices"][0].get("message", {}).get("content"):
            results.add_result("No Headers", False, "No assistant content in response")
            return
        
        results.add_result("No Headers", True, "Server generated all IDs and indices")
        
    except Exception as e:
        results.add_result("No Headers", False, f"Exception: {str(e)}")

async def main():
    """Run all acceptance tests."""
    print("Starting PG-7 Acceptance Tests...")
    print(f"Testing endpoint: {PLAYGROUND_ENDPOINT}")
    print(f"Session ID: {TEST_SESSION_ID}")
    print("-" * 60)
    
    results = TestResults()
    
    # Run all tests
    await test_happy_path(results)
    await test_retry_path(results)
    await test_double_click(results)
    await test_out_of_order(results)
    await test_no_headers(results)
    
    # Print results
    results.print_summary()
    
    print("\nNOTES:")
    print("- Idempotency features are currently disabled due to schema limitations")
    print("- Double-click protection is disabled (no metadata columns)")
    print("- All tests verify the infrastructure is in place")
    print("- Enable features by adding metadata columns to chat_messages table")

if __name__ == "__main__":
    asyncio.run(main())
