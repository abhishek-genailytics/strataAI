"""
Telemetry middleware for API request timing and logging.
Captures request/response sizes, duration, and triggers persistence.
"""
import json
import time
from fastapi import Request, Response
from typing import Callable, Awaitable
from app.services.request_logging import persist_from_request_context


class TelemetryHook:
    """
    FastAPI dependency that measures request timing and sizes.
    Automatically logs all requests to api_requests table after response.
    """
    
    def __init__(self):
        pass
    
    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Middleware function that:
        1. Starts timer and measures request size
        2. Calls the actual route handler
        3. Measures response size and duration
        4. Triggers async persistence (non-blocking)
        """
        t0 = time.perf_counter()
        
        # Best-effort request size measurement
        request_size = None
        try:
            # Try to read request body for size calculation
            body = await request.body()
            request_size = len(body or b"")
            
            # Re-create the request body stream for downstream handlers
            # This is needed because body() consumes the stream
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request._receive = receive
        except Exception:
            # Fallback to Content-Length header if body reading fails
            try:
                content_length = request.headers.get("content-length")
                if content_length:
                    request_size = int(content_length)
            except (ValueError, TypeError):
                request_size = None

        # Call the actual route handler
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.perf_counter() - t0) * 1000)

        # Best-effort response size measurement
        response_size = None
        try:
            # For streaming responses, we need to consume the iterator
            if hasattr(response, 'body_iterator'):
                body_chunks = []
                async for chunk in response.body_iterator:
                    body_chunks.append(chunk)
                response_body = b"".join(body_chunks)
                response_size = len(response_body)
                
                # Recreate the response with the consumed body
                response.body = response_body
                # Remove the iterator to prevent double consumption
                if hasattr(response, 'body_iterator'):
                    delattr(response, 'body_iterator')
            elif hasattr(response, 'body') and response.body:
                response_size = len(response.body)
            else:
                # Try to get from Content-Length header
                content_length = response.headers.get("content-length")
                if content_length:
                    response_size = int(content_length)
        except Exception:
            response_size = None

        # Defer persistence (non-blocking, best-effort)
        # This should never break the user response
        try:
            await persist_from_request_context(
                request=request,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_size=request_size,
                response_size=response_size,
            )
        except Exception:
            # Swallow all errors; never break user response
            # The persistence function already has its own error handling
            pass

        return response


# Convenience function for dependency injection
def get_telemetry_hook() -> TelemetryHook:
    """Factory function for telemetry hook dependency."""
    return TelemetryHook()
