import logging
import re
import structlog
from typing import Any, Dict


# Patterns to detect and redact secrets in logs
_SECRET_PATTERNS = [
    # OpenAI API keys (sk-...)
    re.compile(r"sk-[A-Za-z0-9\-_]{10,}"),
    # Anthropic API keys (sk-ant-...)
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{10,}"),
    # Authorization Bearer tokens
    re.compile(r"(?i)(authorization:?\s*bearer\s+)([A-Za-z0-9\-_\.]+)"),
    # X-API-Key headers
    re.compile(r"(?i)x-api-key:\s*([A-Za-z0-9\-_\.]+)"),
    # JWT tokens (basic pattern)
    re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]*"),
    # Supabase service keys
    re.compile(r"eyJ[A-Za-z0-9\-_]{100,}"),
    # Generic API key patterns
    re.compile(r"(?i)(api[_-]?key[\"\':\s=]+)([A-Za-z0-9\-_\.]{20,})"),
]

# Field names that should always be redacted
_SECRET_FIELDS = {
    "authorization", "x-api-key", "api_key", "token", "provider_key", 
    "access_token", "refresh_token", "bearer_token", "supabase_key",
    "supabase_service_key", "encryption_key", "secret", "password",
    "encrypted_key_value", "key_value"
}


def _redact_string(value: str) -> str:
    """Redact secrets from a string value."""
    if not isinstance(value, str):
        return value
    
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda m: (m.group(1) if m.lastindex and m.lastindex >= 1 else "") + "<redacted>", 
            redacted
        )
    return redacted


def _redact_processor(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Structlog processor to redact sensitive information from logs."""
    
    # Redact known sensitive field names
    for field in _SECRET_FIELDS:
        if field in event_dict:
            event_dict[field] = "<redacted>"
    
    # Redact the main event message if it contains secrets
    if "event" in event_dict:
        event_dict["event"] = _redact_string(str(event_dict["event"]))
    
    # Recursively redact nested dictionaries (like headers, request data)
    for key, value in event_dict.items():
        if isinstance(value, dict):
            event_dict[key] = _redact_dict(value)
        elif isinstance(value, str):
            event_dict[key] = _redact_string(value)
    
    return event_dict


def _redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redact sensitive information from dictionaries."""
    redacted = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field name indicates sensitive data
        if any(secret_field in key_lower for secret_field in _SECRET_FIELDS):
            redacted[key] = "<redacted>"
        elif isinstance(value, dict):
            redacted[key] = _redact_dict(value)
        elif isinstance(value, str):
            redacted[key] = _redact_string(value)
        else:
            redacted[key] = value
    
    return redacted


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging with secret redaction."""
    
    # Set up standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s"
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _redact_processor,  # Our custom redaction processor
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience function for redacting data before manual logging
def redact_sensitive_data(data: Any) -> Any:
    """Manually redact sensitive data from any structure."""
    if isinstance(data, dict):
        return _redact_dict(data)
    elif isinstance(data, str):
        return _redact_string(data)
    else:
        return data
