"""
Usage logging middleware for tracking request metrics - MVP version.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class UsageLoggingMiddleware(BaseHTTPMiddleware):
    """On response, compute duration and attach to header X-Request-Duration-ms"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Use duration_ms from RequestContextMiddleware if available
        if hasattr(request.state, 'duration_ms'):
            duration_ms = request.state.duration_ms
            response.headers["X-Request-Duration-ms"] = f"{duration_ms:.2f}"
            
            # Placeholder print/log (no DB writes yet; will add in Task 14)
            print(f"Request {getattr(request.state, 'request_id', 'unknown')} took {duration_ms:.2f}ms")
        
        return response
