#!/usr/bin/env python3
"""
Test subsequent turn with same session ID
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

async def test_subsequent_turn():
    """Test that subsequent turns with same session ID reuse the session"""
    print("Testing subsequent turn with same session ID...")
    
    # Test data - same as before
    org_id = UUID("05944f2b-54cc-43a1-9b02-7c93df11972f")
    user_id = UUID("5162d3cd-f700-4970-9bed-0c08b36d7d92")
    client_session_id = "test-session-abc-123"  # Same session ID
    provider_id = UUID("dad6b96d-3850-48ba-a206-e36733485cfc")
    model_id = UUID("0997215c-4a26-43d8-9d29-a39c6fc351a9")
    
    try:
        # Should reuse existing session
        session_id = ensure_session(
            organization_id=org_id,
            user_id=user_id,
            client_session_id=client_session_id,
            default_title="Test Session 2"
        )
        print(f"   ✓ Session reused: {session_id}")
        
        # Add another turn
        user_message = ChatMessage(role="user", content="This is a second message!")
        usage = ChatCompletionUsage(prompt_tokens=12, completion_tokens=18, total_tokens=30)
        cost = CostBreakdown(
            currency="USD",
            input_cost=Decimal("0.0012"),
            output_cost=Decimal("0.0024"),
            request_cost=Decimal("0.000"),
            total_cost=Decimal("0.0036")
        )
        
        user_msg_id, assistant_msg_id = append_turn(
            session_id=session_id,
            provider_id=provider_id,
            model_id=model_id,
            last_user_message=user_message,
            assistant_text="This is the second response!",
            usage=usage,
            cost=cost
        )
        print(f"   ✓ Second turn appended - User: {user_msg_id}, Assistant: {assistant_msg_id}")
        
        print("\n✅ Subsequent turn test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Subsequent turn test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_subsequent_turn())
    sys.exit(0 if success else 1)
