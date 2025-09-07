from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.preflight import run_preflight
from app.api.routes import api_router
from app.api.unified_api import router as unified_router
from app.api.playground_read import router as playground_read_router
from app.api.playground import router as playground_router
from app.api.playground_sessions import router as playground_sessions_router
from app.api.playground_models import router as playground_models_router
from app.api.playground_keys import router as playground_keys_router
from app.middleware.error_handling import ErrorHandlingMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.usage_logging import UsageLoggingMiddleware
from app.utils.errors import is_public_openai_path, openai_error_body, infer_type_from_status

def create_app() -> FastAPI:
    """App factory for FastAPI application"""
    settings = get_settings()

    # Setup logging first
    setup_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)

    # Run preflight validation
    run_preflight()

    app = FastAPI(title=settings.PROJECT_NAME)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    
    # Feature flags exposed to app.state for later checks
    app.state.force_echo = settings.FORCE_ECHO_ADAPTER
    app.state.enable_request_logging = settings.ENABLE_REQUEST_LOGGING
    app.state.enable_usage_rollups = settings.ENABLE_USAGE_ROLLUPS
    app.state.enable_playground_logging = settings.ENABLE_PLAYGROUND_LOGGING

    # Log a safe snapshot once at startup
    logger.info("config_loaded", **settings.safe_export())
    
    # Add middleware in order (outer → inner)
    # 1. ErrorHandlingMiddleware (outermost)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 2. RequestContextMiddleware
    app.add_middleware(RequestContextMiddleware)
    
    # 3. UsageLoggingMiddleware (innermost)
    app.add_middleware(UsageLoggingMiddleware)
    
    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Public OpenAI-compatible gateway
    app.include_router(unified_router, prefix="/v1")
    
    # Playground read endpoints
    app.include_router(playground_read_router, prefix="/v1")
    
    # Playground endpoints (session management and chat completions)
    app.include_router(playground_router, prefix=settings.API_V1_STR)
    
    # Mount playground sessions router (session lifecycle management)
    app.include_router(playground_sessions_router, prefix="/api/v1")
    
    # Playground models listing endpoint
    app.include_router(playground_models_router, prefix=settings.API_V1_STR)
    
    # Playground keys status endpoint
    app.include_router(playground_keys_router, prefix=settings.API_V1_STR)
    
    # Custom exception handler for RequestValidationError on OpenAI paths
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        status_code = 400
        msg = "Invalid request"
        param = None
        
        # Extract first error for better messaging
        try:
            err0 = exc.errors()[0]
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
            return JSONResponse(status_code=status_code, content=payload)
        
        # For non-OpenAI paths, return default FastAPI validation error format
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
    
    # Custom exception handler for HTTP exceptions on OpenAI paths
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if is_public_openai_path(request.url.path):
            payload = openai_error_body(
                exc.detail or "Error", 
                type_=infer_type_from_status(exc.status_code)
            )
            return JSONResponse(status_code=exc.status_code, content=payload)
        
        # For non-OpenAI paths, return default format
        return JSONResponse(
            status_code=exc.status_code, 
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    
    return app

# Create app instance
app = create_app()
