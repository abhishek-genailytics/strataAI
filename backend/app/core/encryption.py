"""
Encryption utilities for secure API key storage.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting API keys."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate a new one."""
        key_string = os.getenv("ENCRYPTION_KEY")
        
        if key_string:
            return key_string.encode()
        
        # Generate key from password and salt for development
        password = os.getenv("ENCRYPTION_PASSWORD", "dev-password-change-in-production").encode()
        salt = os.getenv("ENCRYPTION_SALT", "dev-salt-change-in-production").encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
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


# Global encryption service instance
encryption_service = EncryptionService()
