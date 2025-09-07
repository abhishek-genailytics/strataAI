#!/usr/bin/env python3
"""
Test Anthropic model with session logging (using different provider)
"""
import asyncio
import sys
import os
from uuid import UUID
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.playground_logging import ensure_session, append_turn
from app.models.openai_chat import ChatMessage, ChatCompletionUsage
from app.services.costing import CostBreakdown

async def test_anthropic_session():
    """Test session logging with Anthropic provider"""
    print("Testing Anthropic model with session logging...")
    
    # Test data - different session and provider
    org_id = UUID("05944f2b-54cc-43a1-9b02-7c93df11972f")
    user_id = UUID("5162d3cd-f700-4970-9bed-0c08b36d7d92")
    client_session_id = "anthropic-session-xyz-789"  # Different session ID
    anthropic_provider_id = UUID("e8ec214a-0481-4f23-bb7e-8349f7ef09eb")  # Anthropic provider
    # Use OpenAI model ID for testing since Anthropic models aren't available
    model_id = UUID("0997215c-4a26-43d8-9d29-a39c6fc351a9")
    
    try:
        # Create new session for Anthropic
        session_id = ensure_session(
            organization_id=org_id,
            user_id=user_id,
            client_session_id=client_session_id,
            default_title="anthropic/claude-3-sonnet"
        )
        print(f"   ✓ Anthropic session created: {session_id}")
        
        # Add turn with Anthropic provider
        user_message = ChatMessage(role="user", content="Hello from Anthropic test!")
        usage = ChatCompletionUsage(prompt_tokens=8, completion_tokens=12, total_tokens=20)
        cost = CostBreakdown(
            currency="USD",
            input_cost=Decimal("0.0008"),
            output_cost=Decimal("0.0016"),
            request_cost=Decimal("0.000"),
            total_cost=Decimal("0.0024")
        )
        
        user_msg_id, assistant_msg_id = append_turn(
            session_id=session_id,
            provider_id=anthropic_provider_id,
            model_id=model_id,
            last_user_message=user_message,
            assistant_text="Hello! This is an Anthropic response.",
            usage=usage,
            cost=cost
        )
        print(f"   ✓ Anthropic turn appended - User: {user_msg_id}, Assistant: {assistant_msg_id}")
        
        print("\n✅ Anthropic session logging test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Anthropic session test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_anthropic_session())
    sys.exit(0 if success else 1)
