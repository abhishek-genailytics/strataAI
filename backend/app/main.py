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
from app.api.playground_messages import router as playground_messages_router
from app.api.playground_models import router as playground_models_router
from app.api.playground_keys import router as playground_keys_router
from app.api.playground_usage import router as playground_usage_router
from app.api.playground_actions import router as playground_actions_router
from app.api.playground_picker import router as playground_picker_router
from app.api.playground_system import router as playground_system_router
from app.api.playground_hud import router as playground_hud_router
from app.api.playground_export import router as playground_export_router
from app.api.playground_presets import router as playground_presets_router
from app.middleware.error_handling import ErrorHandlingMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.usage_logging import UsageLoggingMiddleware
from app.utils.errors import is_public_openai_path, openai_error_body, infer_type_from_status
from app.api.error_handlers import register_exception_handlers

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
    
    # Register unified exception handlers for PG-15
    register_exception_handlers(app)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint for health checks and service identification."""
        return {
            "service": "StrataAI Backend",
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": {
                "unified_api": "/v1/chat/completions",
                "playground": "/api/v1",
                "docs": "/docs",
                "health": "/health"
            }
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": "StrataAI Backend"}
    
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
    # Messages fetch & pagination for playground sessions
    app.include_router(playground_messages_router, prefix="/api/v1")
    
    # Playground models listing endpoint
    app.include_router(playground_models_router, prefix=settings.API_V1_STR)
    
    # Playground keys status endpoint
    app.include_router(playground_keys_router, prefix=settings.API_V1_STR)
    
    # Playground usage endpoints
    app.include_router(playground_usage_router, prefix=settings.API_V1_STR)
    
    # Playground actions (regenerate functionality)
    app.include_router(playground_actions_router, prefix=settings.API_V1_STR)
    
    # Playground picker aggregator endpoint
    app.include_router(playground_picker_router, prefix=settings.API_V1_STR)
    
    # Playground system prompt management endpoints
    app.include_router(playground_system_router, prefix=settings.API_V1_STR)
    
    # Playground HUD (Heads-Up Display) analytics endpoint
    app.include_router(playground_hud_router, prefix=settings.API_V1_STR)
    
    # Playground export endpoints (cURL and JSON transcript generation)
    app.include_router(playground_export_router, prefix=settings.API_V1_STR)
    
    # Playground presets endpoints (parameter presets and stop sequences)
    app.include_router(playground_presets_router, prefix=settings.API_V1_STR)
    
    # Legacy exception handlers are replaced by unified PG-15 error handling
    # The register_exception_handlers() call above handles all error scenarios
    
    return app

# Create app instance
app = create_app()
