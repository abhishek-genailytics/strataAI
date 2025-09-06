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
        
        # Compute duration if start_time is available
        if hasattr(request.state, 'start_time'):
            duration = (time.monotonic() - request.state.start_time) * 1000  # Convert to ms
            response.headers["X-Request-Duration-ms"] = f"{duration:.2f}"
            
            # Placeholder print/log (no DB writes yet; will add in Task 14)
            print(f"Request {getattr(request.state, 'request_id', 'unknown')} took {duration:.2f}ms")
        
        return response
