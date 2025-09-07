#!/usr/bin/env python3
"""
Test script for playground session logging functionality
"""
import asyncio
import sys
import os
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.playground_logging import ensure_session, append_turn
from app.models.openai_chat import ChatMessage, ChatCompletionUsage
from app.services.costing import CostBreakdown

async def test_session_logging():
    """Test the session logging functionality"""
    print("Testing playground session logging...")
    
    # Test data
    org_id = UUID("05944f2b-54cc-43a1-9b02-7c93df11972f")  # From our test token
    user_id = UUID("5162d3cd-f700-4970-9bed-0c08b36d7d92")  # From our test token
    client_session_id = "test-session-abc-123"
    provider_id = UUID("dad6b96d-3850-48ba-a206-e36733485cfc")  # Real OpenAI provider ID
    model_id = UUID("0997215c-4a26-43d8-9d29-a39c6fc351a9")  # Real model ID
    
    try:
        # Test 1: Create/find session
        print("1. Testing session creation...")
        session_id = ensure_session(
            organization_id=org_id,
            user_id=user_id,
            client_session_id=client_session_id,
            default_title="Test Session"
        )
        print(f"   ✓ Session created/found: {session_id}")
        
        # Test 2: Same session ID should return same session
        print("2. Testing session reuse...")
        session_id_2 = ensure_session(
            organization_id=org_id,
            user_id=user_id,
            client_session_id=client_session_id,
            default_title="Test Session"
        )
        assert session_id == session_id_2, "Session ID should be reused"
        print(f"   ✓ Session reused correctly: {session_id_2}")
        
        # Test 3: Append turn
        print("3. Testing turn append...")
        user_message = ChatMessage(role="user", content="Hello, test message!")
        usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25)
        from decimal import Decimal
        cost = CostBreakdown(
            currency="USD",
            input_cost=Decimal("0.001"),
            output_cost=Decimal("0.002"),
            request_cost=Decimal("0.000"),
            total_cost=Decimal("0.003")
        )
        
        user_msg_id, assistant_msg_id = append_turn(
            session_id=session_id,
            provider_id=provider_id,
            model_id=model_id,
            last_user_message=user_message,
            assistant_text="Hello! This is a test response.",
            usage=usage,
            cost=cost
        )
        print(f"   ✓ Turn appended - User: {user_msg_id}, Assistant: {assistant_msg_id}")
        
        print("\n✅ All session logging tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Session logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_session_logging())
    sys.exit(0 if success else 1)
