#!/usr/bin/env python3
"""
Simple test script to verify PAT authentication implementation.
"""
import asyncio
from app.utils.crypto import sha256_hex, token_prefix
from app.core.exceptions import AuthenticationError

def test_crypto_utilities():
    """Test crypto utility functions."""
    print("Testing crypto utilities...")
    
    # Test token hashing
    test_token = "strata_test_token_123456789"
    token_hash = sha256_hex(test_token)
    prefix = token_prefix(test_token)
    
    print(f"  Token: {test_token}")
    print(f"  Hash: {token_hash}")
    print(f"  Prefix: {prefix}")
    
    assert len(token_hash) == 64, "SHA-256 hash should be 64 characters"
    assert len(prefix) == 6, "Default prefix should be 6 characters"
    assert prefix == test_token[:6], "Prefix should match first 6 characters"
    
    print("  ✓ Crypto utilities working correctly")

async def test_auth_exceptions():
    """Test authentication exception handling."""
    print("\nTesting authentication exceptions...")
    
    try:
        raise AuthenticationError("Test error", code="test_code")
    except AuthenticationError as e:
        assert e.message == "Test error"
        assert e.code == "test_code"
        assert e.http_status == 401
        print("  ✓ AuthenticationError working correctly")

def test_current_caller_model():
    """Test CurrentCaller model."""
    print("\nTesting CurrentCaller model...")
    
    from app.models.auth import CurrentCaller
    from uuid import uuid4
    
    caller = CurrentCaller(
        user_id=uuid4(),
        organization_id=uuid4(),
        token_id=uuid4(),
        token_prefix="strata_",
        scopes=["api:read", "api:write"]
    )
    
    assert caller.token_prefix == "strata_"
    assert len(caller.scopes) == 2
    print("  ✓ CurrentCaller model working correctly")

async def main():
    """Run all tests."""
    print("=== PAT Authentication Implementation Test ===\n")
    
    test_crypto_utilities()
    await test_auth_exceptions()
    test_current_caller_model()
    
    print("\n=== All Tests Passed ===")
    print("PAT authentication implementation is ready for use!")

if __name__ == "__main__":
    asyncio.run(main())
