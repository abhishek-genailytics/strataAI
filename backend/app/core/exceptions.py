"""
Custom exception classes for structured error handling.
"""
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from ..models.error_response import ErrorType, ErrorSeverity, ErrorDetail


class StrataAIException(Exception):
    """Base exception class for StrataAI application."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.INTERNAL_ERROR,
        error_code: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        help_url: Optional[str] = None,
    ):
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.details = details or []
        self.severity = severity
        self.help_url = help_url
        super().__init__(message)


class ValidationException(StrataAIException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[ErrorDetail]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            error_code=error_code,
            details=details,
            severity=ErrorSeverity.LOW,
        )


class AuthenticationException(StrataAIException):
    """Exception for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
        )


class AuthorizationException(StrataAIException):
    """Exception for authorization errors."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        error_code: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
        )


class NotFoundException(StrataAIException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        if resource_type and resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        elif resource_type:
            message = f"{resource_type} not found"
            
        super().__init__(
            message=message,
            error_type=ErrorType.NOT_FOUND_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.LOW,
        )


class RateLimitException(StrataAIException):
    """Exception for rate limit errors."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        error_code: Optional[str] = None,
    ):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_type=ErrorType.RATE_LIMIT_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
        )


class ProviderException(StrataAIException):
    """Exception for AI provider errors."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        provider_error_code: Optional[str] = None,
        provider_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.provider = provider
        self.provider_error_code = provider_error_code
        self.provider_message = provider_message
        
        super().__init__(
            message=message,
            error_type=ErrorType.PROVIDER_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.HIGH,
        )


class NetworkException(StrataAIException):
    """Exception for network-related errors."""
    
    def __init__(
        self,
        message: str = "Network error occurred",
        error_code: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_type=ErrorType.NETWORK_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
        )


class TimeoutException(StrataAIException):
    """Exception for timeout errors."""
    
    def __init__(
        self,
        message: str = "Request timeout",
        timeout_seconds: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        if timeout_seconds:
            message = f"Request timeout after {timeout_seconds} seconds"
            
        super().__init__(
            message=message,
            error_type=ErrorType.TIMEOUT_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.MEDIUM,
        )


class ConfigurationException(StrataAIException):
    """Exception for configuration errors."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        if config_key:
            message = f"Configuration error for '{config_key}': {message}"
            
        super().__init__(
            message=message,
            error_type=ErrorType.CONFIGURATION_ERROR,
            error_code=error_code,
            severity=ErrorSeverity.HIGH,
        )


def create_http_exception(
    exception: StrataAIException,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> HTTPException:
    """Convert StrataAI exception to FastAPI HTTPException."""
    
    # Map exception types to HTTP status codes
    status_map = {
        ErrorType.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorType.AUTHENTICATION_ERROR: status.HTTP_401_UNAUTHORIZED,
        ErrorType.AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
        ErrorType.NOT_FOUND_ERROR: status.HTTP_404_NOT_FOUND,
        ErrorType.RATE_LIMIT_ERROR: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorType.PROVIDER_ERROR: status.HTTP_502_BAD_GATEWAY,
        ErrorType.NETWORK_ERROR: status.HTTP_502_BAD_GATEWAY,
        ErrorType.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
        ErrorType.CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorType.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    http_status = status_map.get(exception.error_type, status_code)
    
    return HTTPException(
        status_code=http_status,
        detail={
            "error": True,
            "error_type": exception.error_type,
            "message": exception.message,
            "error_code": exception.error_code,
            "details": [detail.dict() for detail in exception.details],
            "severity": exception.severity,
            "help_url": exception.help_url,
        }
    )
