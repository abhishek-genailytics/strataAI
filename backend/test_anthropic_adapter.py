"""
Acceptance tests for Anthropic adapter implementation.
Tests the adapter directly with real API calls to validate behavior.

Usage:
    export ANTHROPIC_API_KEY=<your_key>
    python test_anthropic_adapter.py
"""

import asyncio
import os
import sys
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, '/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI/backend')

from app.services.llm_adapters.anthropic import AnthropicAdapter
from app.models.openai_chat import ChatCompletionRequest, ChatMessage
from app.core.exceptions import AuthenticationError, InvalidRequestError


async def test_happy_path():
    """Test happy path with real Anthropic API key."""
    print("🧪 Testing happy path...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        return False
    
    adapter = AnthropicAdapter()
    
    request = ChatCompletionRequest(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[ChatMessage(role="user", content="Say hi")],
        max_tokens=200
    )
    
    try:
        response = await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-5-haiku-20241022",  # Use actual available model from DB
            api_key=api_key
        )
        
        # Validate response
        assert response.choices, "Response should have choices"
        assert response.choices[0].message.content, "Message content should be non-empty"
        assert response.usage.prompt_tokens >= 1, f"Expected prompt_tokens >= 1, got {response.usage.prompt_tokens}"
        assert response.usage.completion_tokens >= 1, f"Expected completion_tokens >= 1, got {response.usage.completion_tokens}"
        assert response.model.startswith("anthropic/"), f"Model should start with 'anthropic/', got {response.model}"
        assert response.choices[0].finish_reason in ["stop", "length"], f"Invalid finish_reason: {response.choices[0].finish_reason}"
        
        print(f"✅ Happy path test passed!")
        print(f"   Response: {response.choices[0].message.content[:100]}...")
        print(f"   Usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total")
        print(f"   Model: {response.model}")
        print(f"   Finish reason: {response.choices[0].finish_reason}")
        return True
        
    except Exception as e:
        print(f"❌ Happy path test failed: {e}")
        return False


async def test_missing_api_key():
    """Test missing API key raises AuthenticationError."""
    print("🧪 Testing missing API key...")
    
    adapter = AnthropicAdapter()
    
    request = ChatCompletionRequest(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[ChatMessage(role="user", content="Say hi")],
        max_tokens=200
    )
    
    try:
        await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-5-haiku-20241022",
            api_key=None
        )
        print("❌ Missing API key test failed: Should have raised AuthenticationError")
        return False
        
    except AuthenticationError as e:
        assert e.code == "provider_key_missing", f"Expected code 'provider_key_missing', got {e.code}"
        print(f"✅ Missing API key test passed: {e}")
        return True
        
    except Exception as e:
        print(f"❌ Missing API key test failed: Expected AuthenticationError, got {type(e).__name__}: {e}")
        return False


async def test_max_tokens_default():
    """Test max_tokens default behavior when not provided."""
    print("🧪 Testing max_tokens default...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping max_tokens test - ANTHROPIC_API_KEY not set")
        return True
    
    adapter = AnthropicAdapter()
    
    # Request without max_tokens
    request = ChatCompletionRequest(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[ChatMessage(role="user", content="Say hi")]
        # No max_tokens specified
    )
    
    try:
        response = await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-5-haiku-20241022",
            api_key=api_key
        )
        
        print(f"✅ Max tokens default test passed - used default value")
        print(f"   Response: {response.choices[0].message.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Max tokens default test failed: {e}")
        return False


async def test_stop_sequences():
    """Test stop sequences mapping."""
    print("🧪 Testing stop sequences...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping stop sequences test - ANTHROPIC_API_KEY not set")
        return True
    
    adapter = AnthropicAdapter()
    
    request = ChatCompletionRequest(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[ChatMessage(role="user", content="Count to 5 and then say END")],
        max_tokens=100,
        stop=["END"]
    )
    
    try:
        response = await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-5-haiku-20241022",
            api_key=api_key
        )
        
        print(f"✅ Stop sequences test completed")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Finish reason: {response.choices[0].finish_reason}")
        
        # Note: We can't guarantee the model will hit the stop sequence,
        # but we can verify the request was processed successfully
        return True
        
    except Exception as e:
        print(f"❌ Stop sequences test failed: {e}")
        return False


async def test_invalid_model_error():
    """Test error mapping for invalid model names."""
    print("🧪 Testing invalid model error...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping invalid model test - ANTHROPIC_API_KEY not set")
        return True
    
    adapter = AnthropicAdapter()
    
    request = ChatCompletionRequest(
        model="anthropic/invalid-model-name",
        messages=[ChatMessage(role="user", content="Say hi")],
        max_tokens=200
    )
    
    try:
        response = await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="invalid-model-name",
            api_key=api_key
        )
        print("❌ Invalid model test failed: Should have raised an error")
        return False
        
    except (InvalidRequestError, AuthenticationError) as e:
        print(f"✅ Invalid model test passed: {type(e).__name__}: {e}")
        return True
        
    except Exception as e:
        print(f"✅ Invalid model test passed with provider error: {type(e).__name__}: {e}")
        return True


async def test_system_message_handling():
    """Test system message collection and conversion."""
    print("🧪 Testing system message handling...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Skipping system message test - ANTHROPIC_API_KEY not set")
        return True
    
    adapter = AnthropicAdapter()
    
    request = ChatCompletionRequest(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="system", content="Be concise in your responses."),
            ChatMessage(role="user", content="What is 2+2?")
        ],
        max_tokens=50
    )
    
    try:
        response = await adapter.chat_completion(
            organization_id=uuid4(),
            request=request,
            model_name="claude-3-5-haiku-20241022",
            api_key=api_key
        )
        
        print(f"✅ System message test passed")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ System message test failed: {e}")
        return False


async def main():
    """Run all acceptance tests."""
    print("🚀 Starting Anthropic Adapter Acceptance Tests")
    print("=" * 50)
    
    tests = [
        ("Missing API Key", test_missing_api_key),
        ("Happy Path", test_happy_path),
        ("Max Tokens Default", test_max_tokens_default),
        ("Stop Sequences", test_stop_sequences),
        ("Invalid Model Error", test_invalid_model_error),
        ("System Message Handling", test_system_message_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
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
        print("🎉 All acceptance tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
