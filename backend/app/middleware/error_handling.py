"""
Error handling middleware for FastAPI application.
"""
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.exceptions import StrataAIException, create_http_exception
from ..models.error_response import (
    ErrorResponse,
    ErrorType,
    ErrorSeverity,
    ErrorDetail,
    ValidationErrorResponse,
    InternalErrorResponse,
)
from ..services.error_logging_service import ErrorLoggingService


logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging."""
    
    def __init__(self, app, error_logging_service: Optional[ErrorLoggingService] = None):
        super().__init__(app)
        self.error_logging_service = error_logging_service or ErrorLoggingService()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and handle any errors that occur."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except StrataAIException as exc:
            # Handle custom application exceptions
            return await self._handle_strata_exception(exc, request, request_id)
            
        except ValidationError as exc:
            # Handle Pydantic validation errors
            return await self._handle_validation_error(exc, request, request_id)
            
        except Exception as exc:
            # Handle unexpected exceptions
            return await self._handle_unexpected_error(exc, request, request_id)
    
    async def _handle_strata_exception(
        self, 
        exc: StrataAIException, 
        request: Request, 
        request_id: str
    ) -> JSONResponse:
        """Handle custom StrataAI exceptions."""
        
        # Log the error
        await self.error_logging_service.log_error(
            error=exc,
            request=request,
            request_id=request_id,
        )
        
        # Create error response
        error_response = ErrorResponse(
            error_type=exc.error_type,
            message=exc.message,
            details=exc.details,
            error_code=exc.error_code,
            request_id=request_id,
            severity=exc.severity,
            help_url=exc.help_url,
        )
        
        # Add retry_after for rate limit errors
        if hasattr(exc, 'retry_after'):
            error_response.retry_after = exc.retry_after
        
        # Map error type to HTTP status code
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
        
        http_status = status_map.get(exc.error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return JSONResponse(
            status_code=http_status,
            content=error_response.dict(),
        )
    
    async def _handle_validation_error(
        self, 
        exc: ValidationError, 
        request: Request, 
        request_id: str
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        
        # Convert validation errors to ErrorDetail objects
        details = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            details.append(ErrorDetail(
                field=field_path,
                message=error["msg"],
                code=error["type"],
                value=error.get("input"),
            ))
        
        # Create validation error response
        error_response = ValidationErrorResponse(
            message="Validation failed",
            details=details,
            request_id=request_id,
            error_code="VALIDATION_FAILED",
        )
        
        # Log the validation error
        await self.error_logging_service.log_validation_error(
            validation_error=exc,
            request=request,
            request_id=request_id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.dict(),
        )
    
    async def _handle_unexpected_error(
        self, 
        exc: Exception, 
        request: Request, 
        request_id: str
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        # Log the unexpected error with full traceback
        logger.error(
            f"Unexpected error in request {request_id}: {str(exc)}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Log to error service
        await self.error_logging_service.log_unexpected_error(
            error=exc,
            request=request,
            request_id=request_id,
            traceback_str=traceback.format_exc(),
        )
        
        # Create internal error response (don't expose internal details in production)
        error_response = InternalErrorResponse(
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id,
            error_code="INTERNAL_ERROR",
        )
        
        # Ensure the response content is JSON serializable
        try:
            content = error_response.dict()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=content,
            )
        except (TypeError, ValueError) as e:
            # Fallback to a simple error response if serialization fails
            logger.error(f"Error serializing error response: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "error_code": "INTERNAL_ERROR",
                },
            )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context for error tracking."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add request context information."""
        
        # Add request metadata
        request.state.start_time = datetime.utcnow()
        request.state.user_agent = request.headers.get("user-agent")
        request.state.client_ip = self._get_client_ip(request)
        
        response = await call_next(request)
        
        # Add response time
        if hasattr(request.state, "start_time"):
            response_time = (datetime.utcnow() - request.state.start_time).total_seconds()
            response.headers["X-Response-Time"] = str(response_time)
        
        # Add request ID to response headers
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-ID"] = request.state.request_id
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
