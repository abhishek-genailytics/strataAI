#!/usr/bin/env python3
"""
Acceptance tests for Task 13 - Cost computation service
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from app.services.costing import compute_cost, load_pricing_for_model, clear_pricing_cache
from app.models.openai_chat import ChatCompletionUsage
from app.core.supabase import get_supabase_service

def seed_model_pricing():
    """Seed model_pricing table with test data for acceptance tests."""
    sb = get_supabase_service()
    
    # First, let's find existing models to use for testing
    models_resp = sb.table("ai_models").select("id, model_name, provider_id").eq("is_active", True).limit(10).execute()
    models = models_resp.data or []
    
    if not models:
        print("No active models found in database. Creating test model entries...")
        # Create test provider if needed
        providers_resp = sb.table("ai_providers").select("id, name").eq("name", "openai").execute()
        if not providers_resp.data:
            provider_data = {
                "id": str(uuid4()),
                "name": "openai",
                "display_name": "OpenAI",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            sb.table("ai_providers").insert(provider_data).execute()
            openai_provider_id = provider_data["id"]
        else:
            openai_provider_id = providers_resp.data[0]["id"]
        
        # Create test model
        model_data = {
            "id": str(uuid4()),
            "provider_id": openai_provider_id,
            "model_name": "gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "model_type": "chat",
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": False,
            "supports_audio": False,
            "max_tokens": 4096,
            "max_input_tokens": 128000,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        sb.table("ai_models").insert(model_data).execute()
        test_model_id = model_data["id"]
        print(f"Created test model: {test_model_id}")
    else:
        # Use first available model for testing
        test_model_id = models[0]["id"]
        print(f"Using existing model for testing: {test_model_id} ({models[0]['model_name']})")
    
    # Clear existing pricing for test model
    sb.table("model_pricing").delete().eq("model_id", test_model_id).execute()
    
    # Seed OpenAI pricing data
    now = datetime.now(timezone.utc).isoformat()
    pricing_data = [
        {
            "id": str(uuid4()),
            "model_id": test_model_id,
            "pricing_type": "input",
            "price_per_unit": "0.5",  # $0.5 per 1K tokens
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
            "model_id": test_model_id,
            "pricing_type": "output",
            "price_per_unit": "1.5",  # $1.5 per 1K tokens
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
            "model_id": test_model_id,
            "pricing_type": "per_request",
            "price_per_unit": "0.002",  # $0.002 per request
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
    
    # Insert pricing data
    for pricing in pricing_data:
        sb.table("model_pricing").insert(pricing).execute()
    
    print(f"Seeded pricing data for model {test_model_id}")
    return test_model_id

def test_openai_happy_path():
    """Test OpenAI cost computation with seeded pricing data."""
    print("\n=== OpenAI Happy Path Test ===")
    
    # Seed pricing data
    model_id = seed_model_pricing()
    
    # Create test usage data
    usage = ChatCompletionUsage(
        prompt_tokens=1000,    # 1K input tokens
        completion_tokens=500, # 0.5K output tokens  
        total_tokens=1500
    )
    
    # Compute cost
    cost = compute_cost(
        usage=usage,
        model_id=UUID(model_id),
        region=None
    )
    
    # Expected calculation:
    # Input: (1000/1000) * 0.5 = $0.5
    # Output: (500/1000) * 1.5 = $0.75
    # Request: 1 * 0.002 = $0.002
    # Total: $1.252
    expected_input = Decimal("0.500000")
    expected_output = Decimal("0.750000") 
    expected_request = Decimal("0.002000")
    expected_total = Decimal("1.252000")
    
    print(f"Usage: {usage.prompt_tokens} input, {usage.completion_tokens} output tokens")
    print(f"Cost breakdown:")
    print(f"  Currency: {cost.currency}")
    print(f"  Input cost: ${cost.input_cost} (expected: ${expected_input})")
    print(f"  Output cost: ${cost.output_cost} (expected: ${expected_output})")
    print(f"  Request cost: ${cost.request_cost} (expected: ${expected_request})")
    print(f"  Total cost: ${cost.total_cost} (expected: ${expected_total})")
    
    # Verify results
    assert cost.currency == "USD", f"Expected USD, got {cost.currency}"
    assert cost.input_cost == expected_input, f"Input cost mismatch: {cost.input_cost} != {expected_input}"
    assert cost.output_cost == expected_output, f"Output cost mismatch: {cost.output_cost} != {expected_output}"
    assert cost.request_cost == expected_request, f"Request cost mismatch: {cost.request_cost} != {expected_request}"
    assert cost.total_cost == expected_total, f"Total cost mismatch: {cost.total_cost} != {expected_total}"
    
    print("✅ OpenAI happy path test PASSED")
    return model_id

def test_no_pricing_configured(model_id):
    """Test behavior when no pricing is configured."""
    print("\n=== No Pricing Configured Test ===")
    
    sb = get_supabase_service()
    
    # Remove all pricing for the model
    sb.table("model_pricing").delete().eq("model_id", model_id).execute()
    
    # Clear the pricing cache to ensure fresh lookup
    clear_pricing_cache()
    
    # Create test usage
    usage = ChatCompletionUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    # Compute cost (should return zero)
    cost = compute_cost(
        usage=usage,
        model_id=UUID(model_id),
        region=None
    )
    
    print(f"Cost with no pricing configured:")
    print(f"  Currency: {cost.currency}")
    print(f"  Input cost: ${cost.input_cost}")
    print(f"  Output cost: ${cost.output_cost}")
    print(f"  Request cost: ${cost.request_cost}")
    print(f"  Total cost: ${cost.total_cost}")
    
    # Verify all costs are zero
    expected_zero = Decimal("0.000000")
    assert cost.input_cost == expected_zero, f"Expected zero input cost, got {cost.input_cost}"
    assert cost.output_cost == expected_zero, f"Expected zero output cost, got {cost.output_cost}"
    assert cost.request_cost == expected_zero, f"Expected zero request cost, got {cost.request_cost}"
    assert cost.total_cost == expected_zero, f"Expected zero total cost, got {cost.total_cost}"
    
    print("✅ No pricing configured test PASSED")

def test_region_override(model_id):
    """Test region-specific pricing override."""
    print("\n=== Region Override Test ===")
    
    sb = get_supabase_service()
    now = datetime.now(timezone.utc).isoformat()
    
    # Add EU-specific pricing (higher rates)
    eu_pricing_data = [
        {
            "id": str(uuid4()),
            "model_id": model_id,
            "pricing_type": "input",
            "price_per_unit": "0.6",  # Higher EU rate
            "unit": "token",
            "currency": "USD",
            "region": "eu",
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
            "price_per_unit": "1.8",  # Higher EU rate
            "unit": "token",
            "currency": "USD",
            "region": "eu",
            "effective_from": now,
            "effective_until": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
    ]
    
    # Also add global pricing back
    global_pricing_data = [
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
        }
    ]
    
    # Insert both pricing sets
    for pricing in eu_pricing_data + global_pricing_data:
        sb.table("model_pricing").insert(pricing).execute()
    
    # Test usage
    usage = ChatCompletionUsage(
        prompt_tokens=1000,
        completion_tokens=500,
        total_tokens=1500
    )
    
    # Test EU region
    eu_cost = compute_cost(
        usage=usage,
        model_id=UUID(model_id),
        region="eu"
    )
    
    # Test global/default region
    global_cost = compute_cost(
        usage=usage,
        model_id=UUID(model_id),
        region=None
    )
    
    print(f"EU region cost: ${eu_cost.total_cost}")
    print(f"Global region cost: ${global_cost.total_cost}")
    
    # EU should be more expensive
    assert eu_cost.total_cost > global_cost.total_cost, "EU pricing should be higher than global"
    
    # Verify EU calculations: (1000/1000)*0.6 + (500/1000)*1.8 = 0.6 + 0.9 = 1.5
    expected_eu_total = Decimal("1.500000")
    assert eu_cost.total_cost == expected_eu_total, f"EU total mismatch: {eu_cost.total_cost} != {expected_eu_total}"
    
    print("✅ Region override test PASSED")

def run_all_tests():
    """Run all acceptance tests."""
    print("Starting Task 13 Acceptance Tests...")
    
    try:
        # Test 1: OpenAI happy path
        model_id = test_openai_happy_path()
        
        # Test 2: No pricing configured
        test_no_pricing_configured(model_id)
        
        # Test 3: Region override
        test_region_override(model_id)
        
        print("\n🎉 All acceptance tests PASSED!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
