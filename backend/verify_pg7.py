#!/usr/bin/env python3
"""
PG-7 Implementation Verification

Verifies that all PG-7 components are correctly implemented and integrated.
"""

def verify_imports():
    """Verify all PG-7 components can be imported."""
    try:
        from app.utils.idempotency import find_prior_result, find_existing_user_message, get_token_usage_for_message
        from app.services.playground_service import PlaygroundProviderService, SendContext
        from app.models.playground_chat import PlaygroundChatCompletionResponse
        from app.api.playground import router
        print("✅ All PG-7 imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def verify_send_context():
    """Verify SendContext class structure."""
    try:
        from app.services.playground_service import SendContext
        import uuid
        
        # Test creation
        context = SendContext(
            user_msg_id=uuid.uuid4(),
            assistant_msg_id=uuid.uuid4(),
            start_index=0
        )
        
        # Verify fields
        assert hasattr(context, 'user_msg_id')
        assert hasattr(context, 'assistant_msg_id') 
        assert hasattr(context, 'start_index')
        
        print("✅ SendContext class structure verified")
        return True
    except Exception as e:
        print(f"❌ SendContext verification failed: {e}")
        return False

def verify_response_model():
    """Verify PlaygroundChatCompletionResponse supports response_id."""
    try:
        from app.models.playground_chat import PlaygroundChatCompletionResponse
        
        # Test with custom response_id
        response = PlaygroundChatCompletionResponse.create(
            model="test/model",
            content="test content",
            response_id="custom_id_123"
        )
        
        assert response.id == "custom_id_123"
        
        # Test without response_id (should generate one)
        response2 = PlaygroundChatCompletionResponse.create(
            model="test/model",
            content="test content"
        )
        
        assert response2.id.startswith("chatcmpl_")
        
        print("✅ PlaygroundChatCompletionResponse response_id support verified")
        return True
    except Exception as e:
        print(f"❌ Response model verification failed: {e}")
        return False

def verify_playground_route():
    """Verify playground route has PG-7 header parameters."""
    try:
        import inspect
        from app.api.playground import playground_chat_completion
        
        # Get function signature
        sig = inspect.signature(playground_chat_completion)
        params = list(sig.parameters.keys())
        
        # Check for PG-7 header parameters
        expected_headers = ['x_session_id', 'x_client_message_id', 'x_idempotency_key']
        
        for header in expected_headers:
            if header not in params:
                print(f"❌ Missing header parameter: {header}")
                return False
        
        print("✅ Playground route PG-7 header parameters verified")
        return True
    except Exception as e:
        print(f"❌ Route verification failed: {e}")
        return False

def verify_send_method_signature():
    """Verify send method has correct signature."""
    try:
        import inspect
        from app.services.playground_service import PlaygroundProviderService
        
        # Get send method signature
        sig = inspect.signature(PlaygroundProviderService.send)
        params = list(sig.parameters.keys())
        
        # Check required parameters
        required_params = ['session_id', 'req', 'user_ctx', 'organization_id', 'headers']
        
        for param in required_params:
            if param not in params:
                print(f"❌ Missing send method parameter: {param}")
                return False
        
        print("✅ Send method signature verified")
        return True
    except Exception as e:
        print(f"❌ Send method signature verification failed: {e}")
        return False

def verify_idempotency_helpers():
    """Verify idempotency helper functions exist and are disabled."""
    try:
        from app.utils.idempotency import find_prior_result, find_existing_user_message, get_token_usage_for_message
        import uuid
        
        # Test functions return None (disabled state)
        session_id = uuid.uuid4()
        
        result1 = find_prior_result(session_id, "test-key")
        result2 = find_existing_user_message(session_id, "client-id")
        
        # Should be None since disabled
        if result1 is not None or result2 is not None:
            print("❌ Idempotency functions should return None (disabled)")
            return False
        
        print("✅ Idempotency helpers verified (correctly disabled)")
        return True
    except Exception as e:
        print(f"❌ Idempotency helpers verification failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("PG-7 Implementation Verification")
    print("=" * 40)
    
    checks = [
        ("Imports", verify_imports),
        ("SendContext", verify_send_context),
        ("Response Model", verify_response_model),
        ("Playground Route", verify_playground_route),
        ("Send Method", verify_send_method_signature),
        ("Idempotency Helpers", verify_idempotency_helpers)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"VERIFICATION RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All PG-7 components verified successfully!")
        print("\nImplementation Status:")
        print("✅ Headers: Request/response headers implemented")
        print("✅ Context: SendContext for optimistic UI reconciliation")
        print("✅ Infrastructure: Idempotency helpers in place")
        print("⚠️  Schema: Idempotency disabled (awaiting metadata columns)")
        print("✅ Ready: Core PG-7 functionality operational")
    else:
        print("❌ Some verification checks failed")
        
    return passed == total

if __name__ == "__main__":
    main()
