from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import api_router
from app.api.unified_api import router as unified_router
from app.middleware.error_handling import ErrorHandlingMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.usage_logging import UsageLoggingMiddleware

def create_app() -> FastAPI:
    """App factory for FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(title=settings.PROJECT_NAME)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    
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
    
    return app

# Create app instance
app = create_app()
