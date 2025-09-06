import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Generate and attach request_id (uuid4) and start_time to request.state"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID and start time
        request.state.request_id = str(uuid.uuid4())
        request.state.start_time = time.monotonic()
        
        response = await call_next(request)
        return response
