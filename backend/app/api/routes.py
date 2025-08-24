from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.api_keys import router as api_keys_router
from app.api.chat import router as chat_router
from app.api.usage_analytics import router as usage_analytics_router
from app.api.organizations import router as organizations_router
from .cache_management import router as cache_management_router
from .error_management import router as error_management_router
from .scalekit_auth import router as scalekit_auth_router

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth_router)

# Include API key management routes
api_router.include_router(api_keys_router)

# Include chat completion routes
api_router.include_router(chat_router)

# Include usage analytics routes
api_router.include_router(usage_analytics_router, prefix="/analytics", tags=["analytics"])

# Include organization management routes
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])

# Include system management routes
api_router.include_router(cache_management_router, prefix="/system", tags=["system"])

# Include error management routes
api_router.include_router(error_management_router, prefix="/errors", tags=["errors"])

# Include ScaleKit authentication routes
api_router.include_router(scalekit_auth_router)

# Placeholder for API routes - will be expanded in later tasks
@api_router.get("/status")
async def api_status():
    return {"status": "API routes ready"}
