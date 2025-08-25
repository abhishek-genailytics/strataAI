from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.core.config import settings
from app.core.redis import redis_manager
from app.api.routes import api_router
from app.middleware import (
    UsageLoggingMiddleware,
    RateLimitingMiddleware,
    ResponseCachingMiddleware,
    IPRateLimitingMiddleware
)
from app.middleware.error_handling import ErrorHandlingMiddleware, RequestContextMiddleware
from app.services.error_logging_service import error_logging_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_manager.connect()
    yield
    # Shutdown
    await redis_manager.disconnect()

app = FastAPI(
    title="StrataAI API Gateway",
    description="Unified API gateway for multiple AI providers with observability and cost tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware in order (last added = first executed)
# 1. Error handling (should be outermost to catch all errors)
app.add_middleware(ErrorHandlingMiddleware, error_logging_service=error_logging_service)

# 2. Request context (should be early to add context to all requests)
app.add_middleware(RequestContextMiddleware)

# 3. Response caching (should be early to cache before processing)
app.add_middleware(ResponseCachingMiddleware)

# 4. Rate limiting (should be before business logic) - Temporarily disabled for debugging
# app.add_middleware(RateLimitingMiddleware)
# app.add_middleware(IPRateLimitingMiddleware, calls_per_minute=100)

# 5. Usage logging (should be last to capture all requests)
app.add_middleware(UsageLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "StrataAI API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
