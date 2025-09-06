"""
Error handling middleware for FastAPI application - MVP version.
"""
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Outermost middleware; produces OpenAI-style errors for public endpoints"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log structured record
            logger.error(
                "Internal server error",
                error=str(exc),
                request_id=getattr(request.state, 'request_id', 'unknown'),
                method=request.method,
                url=str(request.url)
            )
            
            # Return minimal JSON body with OpenAI-style error format
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal Server Error",
                        "type": "internal_server_error",
                        "param": None,
                        "code": None
                    }
                }
            )
