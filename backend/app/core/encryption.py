"""
Encryption utilities for secure API key storage.
"""
import base64
import hashlib
from cryptography.fernet import Fernet


class EncryptionService:
    """Service for encrypting and decrypting API keys."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment - REQUIRED."""
        from ..core.config import get_settings
        
        settings = get_settings()
        if not settings.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        
        # Use consistent key encoding format
        return settings.ENCRYPTION_KEY.encode("utf-8")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage."""
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        encrypted_key = self.cipher_suite.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an API key for use."""
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted_key = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_key.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """Mask an API key for display purposes."""
        if not api_key:
            return ""
        
        if len(api_key) <= visible_chars:
            return "*" * len(api_key)
        
        return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)
    
    def get_key_prefix(self, api_key: str, prefix_length: int = 7) -> str:
        """Extract a prefix from the API key for identification."""
        if not api_key:
            return ""
        
        return api_key[:min(prefix_length, len(api_key))]


# Utility functions for hashing and token operations
def sha256_hex(value: str) -> str:
    """Generate SHA-256 hash of a string value and return as hex string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_prefix(token: str, length: int = 6) -> str:
    """Extract prefix from token for efficient lookup."""
    return token[:length]


# Global encryption service instance - lazy initialization
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get or create the global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

# For backward compatibility - create a lazy property-like object
class _EncryptionServiceProxy:
    def __getattr__(self, name):
        return getattr(get_encryption_service(), name)

encryption_service = _EncryptionServiceProxy()
