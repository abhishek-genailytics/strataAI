"""
Error response models for structured error handling.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Error type enumeration for categorizing errors."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    PROVIDER_ERROR = "provider_error"
    INTERNAL_ERROR = "internal_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorDetail(BaseModel):
    """Detailed error information for specific field or validation errors."""
    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Detailed error message")
    code: Optional[str] = Field(None, description="Specific error code")
    value: Optional[Any] = Field(None, description="Invalid value that caused the error")


class ErrorResponse(BaseModel):
    """Structured error response model."""
    error: bool = Field(True, description="Always true for error responses")
    error_type: ErrorType = Field(..., description="Type of error")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Specific error code for programmatic handling")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying (for rate limits)")
    help_url: Optional[str] = Field(None, description="URL to documentation or help")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorResponse(ErrorResponse):
    """Specialized error response for validation errors."""
    error_type: Literal[ErrorType.VALIDATION_ERROR] = ErrorType.VALIDATION_ERROR
    details: List[ErrorDetail] = Field(..., description="Validation error details")


class AuthenticationErrorResponse(ErrorResponse):
    """Specialized error response for authentication errors."""
    error_type: Literal[ErrorType.AUTHENTICATION_ERROR] = ErrorType.AUTHENTICATION_ERROR
    message: str = Field("Authentication required", description="Authentication error message")


class AuthorizationErrorResponse(ErrorResponse):
    """Specialized error response for authorization errors."""
    error_type: Literal[ErrorType.AUTHORIZATION_ERROR] = ErrorType.AUTHORIZATION_ERROR
    message: str = Field("Insufficient permissions", description="Authorization error message")


class NotFoundErrorResponse(ErrorResponse):
    """Specialized error response for resource not found errors."""
    error_type: Literal[ErrorType.NOT_FOUND_ERROR] = ErrorType.NOT_FOUND_ERROR
    message: str = Field("Resource not found", description="Not found error message")


class RateLimitErrorResponse(ErrorResponse):
    """Specialized error response for rate limit errors."""
    error_type: Literal[ErrorType.RATE_LIMIT_ERROR] = ErrorType.RATE_LIMIT_ERROR
    message: str = Field("Rate limit exceeded", description="Rate limit error message")
    retry_after: int = Field(..., description="Seconds to wait before retrying")


class ProviderErrorResponse(ErrorResponse):
    """Specialized error response for AI provider errors."""
    error_type: Literal[ErrorType.PROVIDER_ERROR] = ErrorType.PROVIDER_ERROR
    provider: Optional[str] = Field(None, description="AI provider that caused the error")
    provider_error_code: Optional[str] = Field(None, description="Original provider error code")
    provider_message: Optional[str] = Field(None, description="Original provider error message")


class InternalErrorResponse(ErrorResponse):
    """Specialized error response for internal server errors."""
    error_type: Literal[ErrorType.INTERNAL_ERROR] = ErrorType.INTERNAL_ERROR
    message: str = Field("Internal server error", description="Internal error message")
    severity: Literal[ErrorSeverity.HIGH] = ErrorSeverity.HIGH


# Error response union type for OpenAPI documentation
ErrorResponseUnion = Union[
    ErrorResponse,
    ValidationErrorResponse,
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    ProviderErrorResponse,
    InternalErrorResponse,
]


# Common error responses for OpenAPI documentation
COMMON_ERROR_RESPONSES = {
    400: {"model": ValidationErrorResponse, "description": "Validation error"},
    401: {"model": AuthenticationErrorResponse, "description": "Authentication required"},
    403: {"model": AuthorizationErrorResponse, "description": "Insufficient permissions"},
    404: {"model": NotFoundErrorResponse, "description": "Resource not found"},
    500: {"model": InternalErrorResponse, "description": "Internal server error"},
}
