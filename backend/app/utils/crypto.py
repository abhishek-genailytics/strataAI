import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import get_settings

def sha256_hex(value: str) -> str:
    """Generate SHA-256 hash of a string value and return as hex string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def token_prefix(token: str, length: int = 6) -> str:
    """Extract prefix from token for efficient lookup."""
    return token[:length]

def fernet_decrypt(encrypted_text: str) -> str:
    """
    Decrypts a base64 Fernet token string using ENCRYPTION_KEY.
    """
    settings = get_settings()
    f = Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))
    try:
        return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Will be mapped to OpenAI-style error by middleware
        raise ValueError("Invalid encryption token")
