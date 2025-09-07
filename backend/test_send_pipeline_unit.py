#!/usr/bin/env python3
"""
PG-9 Send Pipeline Unit Tests
Direct testing of SendPipeline class functionality without HTTP layer.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
from typing import Dict, Any

# Import the classes we need to test
from app.services.send_pipeline import SendPipeline, SendHeaders, SendContext
from app.models.openai_chat import ChatCompletionRequest, ChatMessage, ChatCompletionResponse
from app.core.deps import CurrentUser

class MockCurrentUser:
    """Mock user for testing."""
    def __init__(self):
        self.id = UUID("12345678-1234-5678-9012-123456789012")
        self.jwt_token = "mock_jwt_token"

class MockGatewayBridge:
    """Mock gateway bridge for testing."""
    
    async def chat_completion(self, request: ChatCompletionRequest, session_id: str) -> Dict[str, Any]:
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! This is a test response from Gateway mode."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }

class MockAnalyticsLogger:
    """Mock analytics logger for testing."""
    
    async def log_playground_request(self, **kwargs):
        print(f"Analytics logged: {kwargs}")
        return True

async def test_send_pipeline_gateway_mode():
    """Test Gateway mode happy path."""
    print("🧪 Testing SendPipeline - Gateway Mode")
    print("-" * 40)
    
    # Setup mocks
    mock_gateway = MockGatewayBridge()
    mock_analytics = MockAnalyticsLogger()
    
    # Create pipeline
    pipeline = SendPipeline(
        gateway_bridge=mock_gateway,
        analytics_logger=mock_analytics
    )
    
    # Mock user context
    user_ctx = MockCurrentUser()
    organization_id = UUID("87654321-4321-8765-2109-876543210987")
    
    # Prepare test request
    request = ChatCompletionRequest(
        model="openai/gpt-4o-mini",
        messages=[
            ChatMessage(role="user", content="Hello! This is a Gateway mode test.")
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    headers = SendHeaders(
        session_id=str(uuid.uuid4()),
        client_message_id=str(uuid.uuid4()),
        idempotency_key=str(uuid.uuid4())
    )
    
    session_id = UUID("11111111-2222-3333-4444-555555555555")
    
    # Mock all the database operations
    with patch('app.services.send_pipeline.supabase_service') as mock_supabase, \
         patch('app.services.send_pipeline.get_supabase_user_client') as mock_user_client, \
         patch('app.services.send_pipeline.require_active_key', new_callable=AsyncMock) as mock_preflight, \
         patch('app.services.send_pipeline.next_index', new_callable=AsyncMock) as mock_next_index, \
         patch('app.services.send_pipeline.append_messages', new_callable=AsyncMock) as mock_append, \
         patch('app.services.send_pipeline.find_prior_result', new_callable=AsyncMock) as mock_prior:
        
        # Setup mock returns
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{
            "metadata": {"request_source": "gateway"},
            "user_id": str(user_ctx.id)
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute_result
        
        mock_prior.return_value = None
        mock_next_index.return_value = 1
        mock_append.return_value = [UUID("11111111-1111-1111-1111-111111111111"), UUID("22222222-2222-2222-2222-222222222222")]
        mock_preflight.return_value = None
        
        try:
            # Execute the pipeline
            response, context = await pipeline.run(
                session_id=session_id,
                request=request,
                user_ctx=user_ctx,
                organization_id=organization_id,
                headers=headers
            )
            
            # Verify response structure
            assert isinstance(response, ChatCompletionResponse)
            assert response.object == "chat.completion"
            assert len(response.choices) > 0
            assert response.choices[0].message.role == "assistant"
            assert response.usage is not None
            
            print("✅ Gateway mode response structure correct")
            
            # Verify context
            assert isinstance(context, SendContext)
            assert context.user_msg_id is not None
            assert context.assistant_msg_id is not None
            
            print("✅ Gateway mode context populated")
            print(f"   Response ID: {response.id}")
            print(f"   Usage: {response.usage}")
            
        except Exception as e:
            print(f"❌ Gateway mode test failed: {e}")
            raise

async def test_send_pipeline_direct_mode():
    """Test Direct mode with adapter."""
    print("\n🧪 Testing SendPipeline - Direct Mode")
    print("-" * 40)
    
    # Mock adapter
    mock_adapter = AsyncMock()
    mock_adapter.chat_completion.return_value = ChatCompletionResponse(
        id="chatcmpl-direct123",
        object="chat.completion",
        created=1234567890,
        model="claude-3-haiku-20240307",
        choices=[
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! This is a test response from Direct mode."
                },
                "finish_reason": "stop"
            }
        ],
        usage={
            "prompt_tokens": 12,
            "completion_tokens": 18,
            "total_tokens": 30
        }
    )
    
    # Create pipeline
    pipeline = SendPipeline(analytics_logger=MockAnalyticsLogger())
    
    # Mock user context
    user_ctx = MockCurrentUser()
    organization_id = UUID("87654321-4321-8765-2109-876543210987")
    
    # Prepare test request
    request = ChatCompletionRequest(
        model="anthropic/claude-3-haiku-20240307",
        messages=[
            ChatMessage(role="user", content="Hello! This is a Direct mode test.")
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    headers = SendHeaders(
        session_id=str(uuid.uuid4()),
        client_message_id=str(uuid.uuid4()),
        idempotency_key=str(uuid.uuid4())
    )
    
    session_id = UUID("22222222-3333-4444-5555-666666666666")
    
    # Mock all the database operations and adapter
    with patch('app.services.send_pipeline.supabase_service') as mock_supabase, \
         patch('app.services.send_pipeline.get_adapter') as mock_get_adapter, \
         patch('app.services.send_pipeline.require_active_key', new_callable=AsyncMock) as mock_preflight, \
         patch('app.services.send_pipeline.next_index', new_callable=AsyncMock) as mock_next_index, \
         patch('app.services.send_pipeline.append_messages', new_callable=AsyncMock) as mock_append, \
         patch('app.services.send_pipeline.find_prior_result', new_callable=AsyncMock) as mock_prior:
        
        # Setup mock returns
        mock_execute_result = MagicMock()
        mock_execute_result.data = [{
            "metadata": {"request_source": "direct"},
            "user_id": str(user_ctx.id)
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_execute_result
        
        mock_get_adapter.return_value = mock_adapter
        mock_prior.return_value = None
        mock_next_index.return_value = 1
        mock_append.return_value = [UUID("33333333-3333-3333-3333-333333333333"), UUID("44444444-4444-4444-4444-444444444444")]
        mock_preflight.return_value = None
        
        # Mock encrypted key retrieval
        with patch.object(pipeline, '_get_decrypted_api_key') as mock_get_key:
            mock_get_key.return_value = "mock_api_key"
            
            try:
                # Execute the pipeline
                response, context = await pipeline.run(
                    session_id=session_id,
                    request=request,
                    user_ctx=user_ctx,
                    organization_id=organization_id,
                    headers=headers
                )
                
                # Verify response structure (same as Gateway)
                assert isinstance(response, ChatCompletionResponse)
                assert response.object == "chat.completion"
                assert len(response.choices) > 0
                assert response.choices[0].message.role == "assistant"
                assert response.usage is not None
                
                print("✅ Direct mode response structure correct")
                
                # Verify adapter was called
                mock_adapter.chat_completion.assert_called_once()
                
                print("✅ Direct mode adapter called")
                print(f"   Response ID: {response.id}")
                print(f"   Usage: {response.usage}")
                
            except Exception as e:
                print(f"❌ Direct mode test failed: {e}")
                raise

async def test_send_pipeline_idempotency():
    """Test idempotency handling."""
    print("\n🧪 Testing SendPipeline - Idempotency")
    print("-" * 40)
    
    pipeline = SendPipeline(analytics_logger=MockAnalyticsLogger())
    
    # Mock cached response
    cached_response = {
        "response": ChatCompletionResponse(
            id="chatcmpl-cached123",
            object="chat.completion",
            created=1234567890,
            model="gpt-4o-mini",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a cached response."
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": 8,
                "completion_tokens": 12,
                "total_tokens": 20
            }
        ),
        "user_message_id": UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        "assistant_message_id": UUID("ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj"),
        "start_index": 1,
        "usage": {"prompt_tokens": 8, "completion_tokens": 12, "total_tokens": 20},
        "provider_request_id": "cached_req_123"
    }
    
    with patch('app.services.send_pipeline.find_prior_result') as mock_prior:
        mock_prior.return_value = cached_response
        
        # Mock user context
        user_ctx = MockCurrentUser()
        organization_id = UUID("87654321-4321-8765-2109-876543210987")
        
        request = ChatCompletionRequest(
            model="openai/gpt-4o-mini",
            messages=[
                ChatMessage(role="user", content="This should return cached response.")
            ]
        )
        
        headers = SendHeaders(
            idempotency_key="test_idempotency_key_123"
        )
        
        session_id = UUID("33333333-4444-5555-6666-777777777777")
        
        try:
            # This should return the cached response immediately
            response, context = await pipeline.run(
                session_id=session_id,
                request=request,
                user_ctx=user_ctx,
                organization_id=organization_id,
                headers=headers
            )
            
            # Verify we got the cached response
            assert response.id == "chatcmpl-cached123"
            assert response.choices[0].message.content == "This is a cached response."
            
            print("✅ Idempotency returned cached response")
            print(f"   Cached response ID: {response.id}")
            
        except Exception as e:
            print(f"❌ Idempotency test failed: {e}")
            raise

async def main():
    """Run all unit tests."""
    print("🚀 PG-9 Send Pipeline Unit Tests")
    print("=" * 50)
    
    try:
        await test_send_pipeline_gateway_mode()
        await test_send_pipeline_direct_mode()
        await test_send_pipeline_idempotency()
        
        print("\n" + "=" * 50)
        print("🎉 All unit tests PASSED!")
        print("✅ Gateway mode working")
        print("✅ Direct mode working") 
        print("✅ Idempotency working")
        
    except Exception as e:
        print(f"\n❌ Unit tests FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
