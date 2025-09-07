"""
OpenAI-style error envelope helpers for consistent error formatting.
All playground errors should use this envelope to match OpenAI API format.
"""
from fastapi import HTTPException


def openai_error(
    status_code: int, 
    message: str, 
    *, 
    code: str = None, 
    error_type: str = None
):
    """
    Create an OpenAI-compatible error response.
    
    Args:
        status_code: HTTP status code (400, 401, 403, 404, 500, etc.)
        message: Human-readable error message
        code: Optional error code for programmatic handling
        error_type: Optional error type (defaults to "invalid_request_error")
    
    Raises:
        HTTPException: With OpenAI-style error envelope in detail
    """
    payload = {
        "error": {
            "message": message,
            "type": error_type or "invalid_request_error",
            "param": None,
            "code": code,
        }
    }
    raise HTTPException(status_code=status_code, detail=payload)


def model_not_found_error(model: str):
    """Standard error for unknown or disabled models."""
    openai_error(
        400, 
        f"Unknown or disabled model: {model}", 
        code="model_not_found"
    )


def invalid_model_format_error(model: str):
    """Standard error for invalid model format."""
    openai_error(
        400,
        f"Invalid model format: {model}. Expected format: 'provider/model'",
        code="invalid_model_format"
    )


def provider_key_missing_error(provider: str):
    """Standard error for missing provider API key."""
    openai_error(
        400,
        f"No active API key configured for provider: {provider}",
        code="provider_key_missing"
    )


def session_not_found_error(session_id: str):
    """Standard error for session not found."""
    openai_error(
        404,
        f"Session not found: {session_id}",
        code="session_not_found"
    )


def authentication_error(message: str = "Invalid authentication"):
    """Standard authentication error."""
    openai_error(
        401,
        message,
        code="invalid_authentication",
        error_type="authentication_error"
    )


def rate_limit_error(message: str = "Rate limit exceeded"):
    """Standard rate limit error."""
    openai_error(
        429,
        message,
        code="rate_limit_exceeded",
        error_type="rate_limit_error"
    )


def server_error(message: str = "Internal server error"):
    """Standard server error."""
    openai_error(
        500,
        message,
        code="server_error",
        error_type="server_error"
    )
