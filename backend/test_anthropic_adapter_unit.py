"""
Unit tests for Anthropic adapter implementation.
Tests adapter logic without making real API calls.
"""

import sys
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, '/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI/backend')

from app.services.llm_adapters.anthropic import AnthropicAdapter, _collect_system, _anthropic_messages
from app.models.openai_chat import ChatCompletionRequest, ChatMessage
from app.core.exceptions import AuthenticationError


def test_system_message_collection():
    """Test system message collection and joining."""
    print("🧪 Testing system message collection...")
    
    request = ChatCompletionRequest(
        model="anthropic/claude-3-sonnet-20240229",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="system", content="Be concise."),
            ChatMessage(role="assistant", content="Hi!"),
        ]
    )
    
    system_text = _collect_system(request)
    expected = "You are a helpful assistant.\n\nBe concise."
    
    assert system_text == expected, f"Expected '{expected}', got '{system_text}'"
    print(f"✅ System message collection passed: '{system_text}'")
    return True


def test_anthropic_message_filtering():
    """Test message filtering for Anthropic format."""
    print("🧪 Testing message filtering...")
    
    request = ChatCompletionRequest(
        model="anthropic/claude-3-sonnet-20240229",
        messages=[
            ChatMessage(role="system", content="You are helpful."),
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi!"),
            ChatMessage(role="user", content="How are you?"),
        ]
    )
    
    anthropic_msgs = _anthropic_messages(request)
    expected = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "How are you?"},
    ]
    
    assert anthropic_msgs == expected, f"Expected {expected}, got {anthropic_msgs}"
    print(f"✅ Message filtering passed: {len(anthropic_msgs)} messages")
    return True


def test_adapter_configuration():
    """Test adapter configuration and headers."""
    print("🧪 Testing adapter configuration...")
    
    adapter = AnthropicAdapter()
    
    # Test provider name
    assert adapter.provider_name == "anthropic"
    
    # Test endpoint
    endpoint = adapter._endpoint()
    assert endpoint == "https://api.anthropic.com/v1/messages"
    
    # Test headers
    headers = adapter._headers("test-key")
    expected_headers = {
        "x-api-key": "test-key",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    assert headers == expected_headers
    
    print(f"✅ Adapter configuration passed")
    print(f"   Provider: {adapter.provider_name}")
    print(f"   Endpoint: {endpoint}")
    print(f"   Headers: {headers}")
    return True


async def test_missing_api_key_error():
    """Test missing API key raises AuthenticationError."""
    print("🧪 Testing missing API key error...")
    
    adapter = AnthropicAdapter()
    request = ChatCompletionRequest(
        model="anthropic/claude-3-sonnet-20240229",
        messages=[ChatMessage(role="user", content="Hello")]
    )
    
    try:
        await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-sonnet-20240229",
            api_key=None
        )
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError as e:
        assert e.code == "provider_key_missing"
        print(f"✅ Missing API key error passed: {e}")
        return True


@patch('httpx.AsyncClient.post')
async def test_successful_response_mapping(mock_post):
    """Test successful response mapping from Anthropic to OpenAI format."""
    print("🧪 Testing response mapping...")
    
    # Mock Anthropic API response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={
        "id": "msg_123",
        "model": "claude-3-sonnet-20240229",
        "content": [
            {"type": "text", "text": "Hello! How can I help you today?"}
        ],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 15
        }
    })
    mock_post.return_value = mock_response
    
    adapter = AnthropicAdapter()
    request = ChatCompletionRequest(
        model="anthropic/claude-3-sonnet-20240229",
        messages=[ChatMessage(role="user", content="Hello")],
        max_tokens=100
    )
    
    response = await adapter.chat_completion(
        organization_id=uuid4(),
        request=request,
        model_name="claude-3-sonnet-20240229",
        api_key="test-key"
    )
    
    # Validate response mapping
    assert response.model == "anthropic/claude-3-sonnet-20240229"
    assert response.choices[0].message.content == "Hello! How can I help you today?"
    assert response.choices[0].finish_reason == "stop"
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 15
    assert response.usage.total_tokens == 25
    
    print(f"✅ Response mapping passed")
    print(f"   Content: {response.choices[0].message.content}")
    print(f"   Usage: {response.usage.prompt_tokens}+{response.usage.completion_tokens}={response.usage.total_tokens}")
    return True


@patch('httpx.AsyncClient.post')
async def test_stop_reason_mapping(mock_post):
    """Test stop reason mapping."""
    print("🧪 Testing stop reason mapping...")
    
    # Test max_tokens stop reason
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={
        "id": "msg_123",
        "model": "claude-3-sonnet-20240229",
        "content": [{"type": "text", "text": "Response"}],
        "stop_reason": "max_tokens",
        "usage": {"input_tokens": 5, "output_tokens": 10}
    })
    mock_post.return_value = mock_response
    
    adapter = AnthropicAdapter()
    request = ChatCompletionRequest(
        model="anthropic/claude-3-sonnet-20240229",
        messages=[ChatMessage(role="user", content="Hello")],
        max_tokens=10
    )
    
    response = await adapter.chat_completion(
        organization_id=uuid4(),
        request=request,
        model_name="claude-3-sonnet-20240229",
        api_key="test-key"
    )
    
    assert response.choices[0].finish_reason == "length"
    print(f"✅ Stop reason mapping passed: max_tokens -> length")
    return True


def main():
    """Run all unit tests."""
    print("🚀 Starting Anthropic Adapter Unit Tests")
    print("=" * 50)
    
    # Synchronous tests
    sync_tests = [
        ("System Message Collection", test_system_message_collection),
        ("Message Filtering", test_anthropic_message_filtering),
        ("Adapter Configuration", test_adapter_configuration),
    ]
    
    # Async tests
    async_tests = [
        ("Missing API Key Error", test_missing_api_key_error),
        ("Response Mapping", test_successful_response_mapping),
        ("Stop Reason Mapping", test_stop_reason_mapping),
    ]
    
    results = []
    
    # Run sync tests
    for test_name, test_func in sync_tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Run async tests
    async def run_async_tests():
        for test_name, test_func in async_tests:
            print(f"\n--- {test_name} ---")
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                results.append((test_name, False))
    
    asyncio.run(run_async_tests())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All unit tests passed!")
    else:
        print("⚠️  Some tests failed.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
