from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.api_keys import router as api_keys_router

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth_router)

# Include API key management routes
api_router.include_router(api_keys_router)

# Placeholder for API routes - will be expanded in later tasks
@api_router.get("/status")
async def api_status():
    return {"status": "API routes ready"}
