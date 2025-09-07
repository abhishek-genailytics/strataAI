#!/usr/bin/env python3
"""
Test script for the new costing service implementation.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from uuid import UUID
from app.services.costing import compute_cost, load_pricing_for_model
from app.models.openai_chat import ChatCompletionUsage

def test_cost_computation():
    """Test cost computation with mock usage data."""
    
    # Mock usage data
    usage = ChatCompletionUsage(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    
    # Test with a mock model ID (this will likely fail gracefully if no pricing data exists)
    mock_model_id = UUID("12345678-1234-5678-9012-123456789012")
    
    try:
        print("Testing cost computation...")
        cost = compute_cost(
            usage=usage,
            model_id=mock_model_id,
            region=None
        )
        
        print(f"Cost breakdown:")
        print(f"  Currency: {cost.currency}")
        print(f"  Input cost: ${cost.input_cost}")
        print(f"  Output cost: ${cost.output_cost}")
        print(f"  Request cost: ${cost.request_cost}")
        print(f"  Total cost: ${cost.total_cost}")
        
    except Exception as e:
        print(f"Cost computation failed (expected if no pricing data): {e}")
    
    try:
        print("\nTesting pricing lookup...")
        pricing = load_pricing_for_model(mock_model_id)
        print(f"Pricing data found: {len(pricing)} entries")
        for pricing_type, row in pricing.items():
            print(f"  {pricing_type}: ${row.price_per_unit} per {row.unit} ({row.currency})")
            
    except Exception as e:
        print(f"Pricing lookup failed (expected if no pricing data): {e}")

if __name__ == "__main__":
    test_cost_computation()
