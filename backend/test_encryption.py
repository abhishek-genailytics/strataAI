#!/usr/bin/env python3
"""
Simple test script to verify encryption functionality.
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.encryption import EncryptionService

def test_encryption():
    """Test basic encryption functionality."""
    print("Testing API Key Encryption Service...")
    
    service = EncryptionService()
    
    # Test encryption/decryption
    original_key = "sk-test1234567890abcdef"
    print(f"Original key: {original_key}")
    
    encrypted = service.encrypt_api_key(original_key)
    print(f"Encrypted: {encrypted}")
    
    decrypted = service.decrypt_api_key(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert decrypted == original_key, "Encryption/decryption failed!"
    print("✅ Encryption/decryption test passed")
    
    # Test masking
    masked = service.mask_api_key(original_key)
    print(f"Masked key: {masked}")
    assert masked.startswith("sk-t"), "Masking failed!"
    print("✅ Masking test passed")
    
    # Test prefix extraction
    prefix = service.get_key_prefix(original_key)
    print(f"Key prefix: {prefix}")
    assert prefix == "sk-test", "Prefix extraction failed!"
    print("✅ Prefix extraction test passed")
    
    print("\n🎉 All encryption tests passed!")

if __name__ == "__main__":
    test_encryption()
