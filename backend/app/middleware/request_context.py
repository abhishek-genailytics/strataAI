import uuid
import time
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.errors import generate_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Request context middleware for X-Request-ID generation and timing.
    
    Features:
    - Generates or uses existing X-Request-ID header
    - Tracks request timing for observability
    - Adds correlation headers to responses
    - Handles exceptions gracefully for timing
    """
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("x-request-id")
        if not request_id:
            request_id = generate_request_id()
        
        # Store in request state
        request.state.request_id = request_id
        request.state.start_time = time.monotonic_ns()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            end_time = time.monotonic_ns()
            duration_ms = (end_time - request.state.start_time) / 1_000_000
            request.state.duration_ms = duration_ms
            
            # Add correlation headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace"] = request_id  # Alias for frontend dev tools
            
            return response
            
        except Exception as e:
            # Calculate best-effort duration even on exception
            try:
                end_time = time.monotonic_ns()
                duration_ms = (end_time - request.state.start_time) / 1_000_000
                request.state.duration_ms = duration_ms
            except:
                request.state.duration_ms = 0.0
            
            # Re-raise exception for handlers to process
            raise e
