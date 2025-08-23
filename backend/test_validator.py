#!/usr/bin/env python3
"""
Simple test script to verify API key validation functionality.
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.api_key_validator import APIKeyValidator

def test_validation():
    """Test basic validation functionality."""
    print("Testing API Key Validation Service...")
    
    validator = APIKeyValidator()
    
    # Test OpenAI key format validation
    valid_openai = "sk-" + "a" * 48
    invalid_openai = "invalid-key"
    
    print(f"Testing OpenAI key format validation...")
    assert validator._validate_key_format(valid_openai, "openai") is True
    assert validator._validate_key_format(invalid_openai, "openai") is False
    print("✅ OpenAI format validation test passed")
    
    # Test Anthropic key format validation
    valid_anthropic = "sk-ant-api03-" + "a" * 95
    invalid_anthropic = "sk-invalid-key"
    
    print(f"Testing Anthropic key format validation...")
    assert validator._validate_key_format(valid_anthropic, "anthropic") is True
    assert validator._validate_key_format(invalid_anthropic, "anthropic") is False
    print("✅ Anthropic format validation test passed")
    
    # Test Google key format validation
    valid_google = "AIza" + "a" * 35
    invalid_google = "invalid-key"
    
    print(f"Testing Google key format validation...")
    assert validator._validate_key_format(valid_google, "google") is True
    assert validator._validate_key_format(invalid_google, "google") is False
    print("✅ Google format validation test passed")
    
    # Test unknown provider (should return True)
    print(f"Testing unknown provider validation...")
    assert validator._validate_key_format("any-key", "unknown") is True
    print("✅ Unknown provider validation test passed")
    
    print("\n🎉 All validation tests passed!")

if __name__ == "__main__":
    test_validation()
