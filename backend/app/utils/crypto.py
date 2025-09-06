import hashlib

def sha256_hex(value: str) -> str:
    """Generate SHA-256 hash of a string value and return as hex string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def token_prefix(token: str, length: int = 6) -> str:
    """Extract prefix from token for efficient lookup."""
    return token[:length]
