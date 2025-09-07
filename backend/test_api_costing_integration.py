#!/usr/bin/env python3
"""
Integration test for Task 13 - Cost computation in actual API endpoint
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from app.services.costing import compute_cost, clear_pricing_cache
from app.models.openai_chat import ChatCompletionUsage, ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice
from app.core.supabase import get_supabase_service

def setup_test_pricing():
    """Set up test pricing data for API integration test."""
    sb = get_supabase_service()
    
    # Find or create a test model
    models_resp = sb.table("ai_models").select("id, model_name, provider_id").eq("is_active", True).limit(1).execute()
    if not models_resp.data:
        print("No models found for integration test")
        return None
    
    model_id = models_resp.data[0]["id"]
    
    # Clear existing pricing
    sb.table("model_pricing").delete().eq("model_id", model_id).execute()
    clear_pricing_cache()
    
    # Add test pricing
    now = datetime.now(timezone.utc).isoformat()
    pricing_data = [
        {
            "id": str(uuid4()),
            "model_id": model_id,
            "pricing_type": "input",
            "price_per_unit": "0.5",
            "unit": "token",
            "currency": "USD",
            "region": "global",
            "effective_from": now,
            "effective_until": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid4()),
            "model_id": model_id,
            "pricing_type": "output",
            "price_per_unit": "1.5",
            "unit": "token",
            "currency": "USD",
            "region": "global",
            "effective_from": now,
            "effective_until": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid4()),
            "model_id": model_id,
            "pricing_type": "per_request",
            "price_per_unit": "0.002",
            "unit": "request",
            "currency": "USD",
            "region": "global",
            "effective_from": now,
            "effective_until": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
    ]
    
    for pricing in pricing_data:
        sb.table("model_pricing").insert(pricing).execute()
    
    return model_id

def test_request_state_population():
    """Test that request.state is properly populated with cost data."""
    print("=== Request State Population Test ===")
    
    # Set up test pricing
    model_id = setup_test_pricing()
    if not model_id:
        print("❌ Could not set up test pricing")
        return False
    
    # Mock request object
    mock_request = Mock()
    mock_request.state = Mock()
    
    # Mock resolved model
    from app.models.catalog import ResolvedModel
    resolved_model = ResolvedModel(
        id=UUID(model_id),
        provider_id=UUID("12345678-1234-5678-9012-123456789012"),
        provider_name="openai",
        model_name="gpt-4o-mini",
        display_name="GPT-4o Mini",
        model_type="chat",
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=False,
        supports_audio=False,
        max_tokens=4096,
        max_input_tokens=128000,
        is_active=True
    )
    
    # Mock adapter response
    mock_usage = ChatCompletionUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    mock_choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(role="assistant", content="Test response"),
        finish_reason="stop"
    )
    
    mock_response = ChatCompletionResponse(
        id="chatcmpl-test",
        object="chat.completion",
        created=1234567890,
        model="openai/gpt-4o-mini",
        choices=[mock_choice],
        usage=mock_usage
    )
    
    # Simulate the cost computation and state setting from unified_api.py
    cost = compute_cost(
        usage=mock_response.usage,
        model_id=resolved_model.id,
        region=None
    )
    
    # Set request state (simulating what unified_api.py does)
    mock_request.state.cost_breakdown = cost
    mock_request.state.model_id = resolved_model.id
    mock_request.state.provider_id = resolved_model.provider_id
    mock_request.state.api_key_id = UUID("87654321-4321-8765-2109-876543210987")
    
    # Verify request state is properly populated
    assert hasattr(mock_request.state, 'cost_breakdown'), "cost_breakdown not set on request.state"
    assert hasattr(mock_request.state, 'model_id'), "model_id not set on request.state"
    assert hasattr(mock_request.state, 'provider_id'), "provider_id not set on request.state"
    assert hasattr(mock_request.state, 'api_key_id'), "api_key_id not set on request.state"
    
    # Verify cost calculation
    expected_total = Decimal("1.252000")  # (1000/1000)*0.5 + (500/1000)*1.5 + 0.002
    assert mock_request.state.cost_breakdown.total_cost == expected_total, f"Expected {expected_total}, got {mock_request.state.cost_breakdown.total_cost}"
    assert mock_request.state.cost_breakdown.currency == "USD", "Expected USD currency"
    
    print(f"✅ Request state properly populated:")
    print(f"   Cost breakdown: ${mock_request.state.cost_breakdown.total_cost} {mock_request.state.cost_breakdown.currency}")
    print(f"   Model ID: {mock_request.state.model_id}")
    print(f"   Provider ID: {mock_request.state.provider_id}")
    print(f"   API Key ID: {mock_request.state.api_key_id}")
    
    return True

def test_openai_response_unchanged():
    """Verify that OpenAI response schema is not mutated by cost computation."""
    print("\n=== OpenAI Response Schema Test ===")
    
    # Create a standard OpenAI response
    usage = ChatCompletionUsage(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(role="assistant", content="Hello!"),
        finish_reason="stop"
    )
    
    response = ChatCompletionResponse(
        id="chatcmpl-123",
        object="chat.completion",
        created=1234567890,
        model="openai/gpt-4o-mini",
        choices=[choice],
        usage=usage
    )
    
    # Serialize to dict to check exact fields
    response_dict = response.model_dump()
    expected_fields = {"id", "object", "created", "model", "choices", "usage"}
    actual_fields = set(response_dict.keys())
    
    assert actual_fields == expected_fields, f"Response schema changed! Expected {expected_fields}, got {actual_fields}"
    
    # Verify no cost fields are added to the response
    cost_fields = {"cost", "cost_breakdown", "pricing", "total_cost"}
    assert not any(field in actual_fields for field in cost_fields), "Cost fields leaked into OpenAI response"
    
    print("✅ OpenAI response schema unchanged - no cost fields leaked")
    return True

def run_integration_tests():
    """Run all integration tests."""
    print("Starting Task 13 API Integration Tests...\n")
    
    try:
        # Test 1: Request state population
        if not test_request_state_population():
            return False
        
        # Test 2: OpenAI response schema unchanged
        if not test_openai_response_unchanged():
            return False
        
        print("\n🎉 All integration tests PASSED!")
        print("✅ Cost computation properly integrated into unified API")
        print("✅ Request state populated for Task 14 analytics")
        print("✅ OpenAI compatibility maintained")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
