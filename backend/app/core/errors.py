"""
Core error classes and normalization helpers for uniform error handling.
Provides OpenAI-compatible error envelopes across all endpoints.
"""

from typing import Optional, Dict, Any
import uuid


class StrataError(Exception):
    """Base exception class for all Strata-specific errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        openai_type: str,
        status_code: int,
        param: Optional[str] = None,
        provider_request_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.openai_type = openai_type
        self.status_code = status_code
        self.param = param
        self.provider_request_id = provider_request_id
        self.extra = extra or {}


class MissingOrgApiKeyError(StrataError):
    """No provider key configured for the chosen model/provider."""
    
    def __init__(
        self,
        provider: str,
        param: Optional[str] = None,
        provider_request_id: Optional[str] = None
    ):
        message = f"No active API key configured for provider '{provider}' in this organization."
        super().__init__(
            message=message,
            code="missing_org_api_key",
            openai_type="invalid_request_error",
            status_code=400,
            param=param,
            provider_request_id=provider_request_id
        )


class AuthError(StrataError):
    """Provider authentication failed."""
    
    def __init__(
        self,
        message: str = "Provider rejected credentials.",
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code="invalid_api_key",
            openai_type="authentication_error",
            status_code=401,
            provider_request_id=provider_request_id
        )


class PermissionError(StrataError):
    """Model disabled for organization or user."""
    
    def __init__(
        self,
        message: str,
        code: str = "model_disabled_for_org",
        param: Optional[str] = None,
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            openai_type="invalid_request_error",
            status_code=403,
            param=param,
            provider_request_id=provider_request_id
        )


class ModelNotFoundError(StrataError):
    """Provider says unknown/retired model."""
    
    def __init__(
        self,
        model: str,
        provider_request_id: Optional[str] = None
    ):
        message = f"Model '{model}' not found or no longer available."
        super().__init__(
            message=message,
            code="model_not_found",
            openai_type="invalid_request_error",
            status_code=404,
            param="model",
            provider_request_id=provider_request_id
        )


class BadRequestError(StrataError):
    """Provider 400s including max tokens, content shape, etc."""
    
    def __init__(
        self,
        message: str,
        code: str = "invalid_param",
        param: Optional[str] = None,
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code=code,
            openai_type="invalid_request_error",
            status_code=400,
            param=param,
            provider_request_id=provider_request_id
        )


class RateLimitError(StrataError):
    """Provider 429 rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code="rate_limit_exceeded",
            openai_type="rate_limit_error",
            status_code=429,
            provider_request_id=provider_request_id
        )


class TimeoutError(StrataError):
    """HTTP timeout or provider slow response."""
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        provider_request_id: Optional[str] = None
    ):
        message = f"Upstream provider timed out after {timeout_seconds}s."
        super().__init__(
            message=message,
            code="upstream_timeout",
            openai_type="server_error",
            status_code=504,
            provider_request_id=provider_request_id
        )


class UpstreamServerError(StrataError):
    """Provider 5xx server error."""
    
    def __init__(
        self,
        status_code: int,
        message: str = "Upstream provider error.",
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code="upstream_5xx",
            openai_type="server_error",
            status_code=502,
            provider_request_id=provider_request_id
        )


class ServerError(StrataError):
    """Internal server error (our bug/unhandled)."""
    
    def __init__(
        self,
        message: str = "Internal server error.",
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code="internal_error",
            openai_type="server_error",
            status_code=500,
            provider_request_id=provider_request_id
        )


class ValidationError(StrataError):
    """OpenAPI/Pydantic validation error."""
    
    def __init__(
        self,
        message: str,
        param: Optional[str] = None,
        provider_request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            code="invalid_request_body",
            openai_type="invalid_request_error",
            status_code=400,
            param=param,
            provider_request_id=provider_request_id
        )


def to_openai_error(error: StrataError, request_id: str) -> Dict[str, Any]:
    """
    Convert a StrataError to OpenAI-compatible error envelope.
    
    Args:
        error: The StrataError instance
        request_id: The request correlation ID
        
    Returns:
        OpenAI-compatible error response dict
    """
    return {
        "error": {
            "message": error.message,
            "type": error.openai_type,
            "code": error.code,
            "param": error.param
        },
        "request_id": request_id
    }


def generate_request_id() -> str:
    """Generate a unique request ID with 'req_' prefix."""
    return f"req_{uuid.uuid4().hex[:12]}"
