"""
Global exception handlers for FastAPI.
Provides uniform OpenAI-compatible error responses across all endpoints.
"""

from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

from ..core.errors import (
    StrataError,
    ValidationError,
    ServerError,
    to_openai_error,
    generate_request_id
)


logger = logging.getLogger(__name__)


async def strata_error_handler(request: Request, exc: StrataError) -> JSONResponse:
    """
    Handle all StrataError exceptions with OpenAI-compatible envelope.
    
    Args:
        request: FastAPI request object
        exc: StrataError instance
        
    Returns:
        JSONResponse with OpenAI error envelope
    """
    # Get request ID from state or generate new one
    request_id = getattr(request.state, 'request_id', generate_request_id())
    duration_ms = getattr(request.state, 'duration_ms', 0.0)
    
    # Build OpenAI-compatible error response
    error_response = to_openai_error(exc, request_id)
    
    # Prepare response headers
    headers = {
        "X-Request-ID": request_id,
        "X-Trace": request_id
    }
    
    # Add provider request ID if available
    if exc.provider_request_id:
        headers["X-Provider-Request-ID"] = exc.provider_request_id
    
    # Log the error for observability
    logger.error(
        f"StrataError: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "provider_request_id": exc.provider_request_id,
            "status_code": exc.status_code,
            "duration_ms": duration_ms,
            "error_type": exc.openai_type,
            "error_code": exc.code,
            "param": exc.param,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Import analytics logger here to avoid circular imports
    try:
        from ..services.analytics_logger import log_failure
        await log_failure(
            request_id=request_id,
            provider_request_id=exc.provider_request_id,
            status_code=exc.status_code,
            duration_ms=duration_ms,
            endpoint=request.url.path,
            provider=None,  # Will be set by calling service if available
            model=None,     # Will be set by calling service if available
            error_type=exc.openai_type,
            error_code=exc.code
        )
    except Exception as log_error:
        logger.warning(f"Failed to log error analytics: {log_error}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=headers
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle FastAPI/Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with OpenAI error envelope
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    
    # Extract validation details
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        param = ".".join(str(loc) for loc in first_error.get("loc", []))
        message = first_error.get("msg", "Validation error")
        
        # Make message more user-friendly
        if "field required" in message.lower():
            message = f"Missing required field: {param}"
        elif "invalid" in message.lower():
            message = f"Invalid value for field: {param}"
    else:
        param = None
        message = "Request validation failed"
    
    # Create ValidationError
    validation_error = ValidationError(
        message=message,
        param=param
    )
    
    return await strata_error_handler(request, validation_error)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException instances.
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSONResponse with OpenAI error envelope
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    
    # Map HTTPException to appropriate StrataError
    if exc.status_code == 400:
        error = ValidationError(message=str(exc.detail))
    elif exc.status_code == 401:
        from ..core.errors import AuthError
        error = AuthError(message=str(exc.detail))
    elif exc.status_code == 403:
        from ..core.errors import PermissionError
        error = PermissionError(message=str(exc.detail))
    elif exc.status_code == 404:
        from ..core.errors import ModelNotFoundError
        error = ModelNotFoundError(model="unknown")
        error.message = str(exc.detail)
    elif exc.status_code == 429:
        from ..core.errors import RateLimitError
        error = RateLimitError(message=str(exc.detail))
    else:
        error = ServerError(message=str(exc.detail))
        error.status_code = exc.status_code
    
    return await strata_error_handler(request, error)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTPException instances.
    
    Args:
        request: FastAPI request object
        exc: StarletteHTTPException instance
        
    Returns:
        JSONResponse with OpenAI error envelope
    """
    # Convert to FastAPI HTTPException and handle
    fastapi_exc = HTTPException(status_code=exc.status_code, detail=exc.detail)
    return await http_exception_handler(request, fastapi_exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions as ServerError.
    
    Args:
        request: FastAPI request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with OpenAI error envelope
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    
    # Log the unexpected error
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Create generic ServerError
    server_error = ServerError(
        message="An unexpected error occurred. Please try again later."
    )
    
    return await strata_error_handler(request, server_error)


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Register handlers in order of specificity
    app.add_exception_handler(StrataError, strata_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
