"""
Error handling middleware for FastAPI application.
"""
import json
import traceback
from typing import Any, Dict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.utils.errors import is_public_openai_path, openai_error_body, infer_type_from_status
from app.core.exceptions import UnifiedAPIError

logger = structlog.get_logger()

def _request_id(req: Request) -> str:
    return getattr(getattr(req, "state", None), "request_id", "-")

def _log_exc(req: Request, status_code: int, payload: Dict[str, Any]) -> None:
    logger.error(
        "unified_api_error",
        request_id=_request_id(req),
        method=req.method,
        path=req.url.path,
        status_code=status_code,
        error=payload.get("error", {}),
    )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except UnifiedAPIError as e:
            status_code = e.http_status
            if is_public_openai_path(request.url.path):
                payload = openai_error_body(e.message, type_=e.openai_type, param=e.param, code=e.code)
                _log_exc(request, status_code, payload)
                return JSONResponse(status_code=status_code, content=payload)
            # Non-public routes: default JSON
            return JSONResponse(status_code=status_code, content={"detail": e.message})

        except RequestValidationError as e:
            # Pydantic/FastAPI validation issues (body/path/query), treat as 400 for OpenAI consistency
            status_code = 400
            msg = "Invalid request"
            param = None
            
            # Extract first error for better messaging
            try:
                err0 = e.errors()[0]
                # Build param path, skipping 'body' prefix for cleaner param names
                loc_parts = [str(p) for p in err0.get("loc", []) if isinstance(p, (str, int)) and p != "body"]
                param = ".".join(loc_parts) if loc_parts else None
                
                # Use the actual error message from Pydantic
                pydantic_msg = err0.get("msg", "")
                if pydantic_msg:
                    msg = pydantic_msg
                    # Make message more user-friendly for required fields
                    if err0.get("type") == "missing" and param:
                        msg = f"Field '{param}' is required"
            except Exception:
                param = None
                
            if is_public_openai_path(request.url.path):
                payload = openai_error_body(msg, type_=infer_type_from_status(status_code), param=param)
                _log_exc(request, status_code, payload)
                return JSONResponse(status_code=status_code, content=payload)
            return JSONResponse(status_code=status_code, content={"detail": msg})

        except StarletteHTTPException as e:
            status_code = e.status_code
            # Starlette's detail may be str or dict
            detail = e.detail if isinstance(e.detail, str) else json.dumps(e.detail)
            
            # Map HTTPBearer 403 to 401 for OpenAI compatibility
            if status_code == 403 and "Not authenticated" in str(detail) and is_public_openai_path(request.url.path):
                status_code = 401
                payload = openai_error_body("Missing Authorization header", type_="authentication_error", code="missing_authorization")
                _log_exc(request, status_code, payload)
                return JSONResponse(status_code=status_code, content=payload)
            
            if is_public_openai_path(request.url.path):
                payload = openai_error_body(detail or "Error", type_=infer_type_from_status(status_code))
                _log_exc(request, status_code, payload)
                return JSONResponse(status_code=status_code, content=payload)
            return JSONResponse(status_code=status_code, content={"detail": detail}, headers=getattr(e, "headers", None))

        except Exception as e:
            status_code = 500
            msg = "Internal Server Error"
            if is_public_openai_path(request.url.path):
                payload = openai_error_body(msg, type_="server_error")
                _log_exc(request, status_code, payload)
                return JSONResponse(status_code=status_code, content=payload)
            # Non-public: keep a generic detail, never leak internals
            logger.error("internal_error", request_id=_request_id(request), path=request.url.path, exc=str(e), tb=traceback.format_exc())
            return JSONResponse(status_code=status_code, content={"detail": msg})
