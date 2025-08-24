from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from app.middleware.caching import cache_service
from app.middleware.rate_limiting import get_rate_limit_status
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/cache/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get cache statistics and metrics"""
    try:
        stats = await cache_service.get_cache_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@router.delete("/cache/clear")
async def clear_all_cache(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear all cached responses (admin only)"""
    # TODO: Add admin role check when role system is implemented
    try:
        deleted_count = await cache_service.clear_all_cache()
        return {
            "success": True,
            "message": f"Cleared {deleted_count} cache entries",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.delete("/cache/user/{user_id}")
async def clear_user_cache(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear cache for specific user"""
    # Users can only clear their own cache unless they're admin
    if current_user.id != user_id:
        # TODO: Add admin role check when role system is implemented
        raise HTTPException(status_code=403, detail="Can only clear your own cache")
    
    try:
        deleted_count = await cache_service.invalidate_user_cache(user_id)
        return {
            "success": True,
            "message": f"Cleared {deleted_count} cache entries for user",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error clearing user cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear user cache")

@router.delete("/cache/endpoint")
async def clear_endpoint_cache(
    endpoint_pattern: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear cache for specific endpoint pattern"""
    try:
        deleted_count = await cache_service.invalidate_endpoint_cache(endpoint_pattern)
        return {
            "success": True,
            "message": f"Cleared {deleted_count} cache entries for endpoint pattern",
            "deleted_count": deleted_count,
            "pattern": endpoint_pattern
        }
    except Exception as e:
        logger.error(f"Error clearing endpoint cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear endpoint cache")

@router.get("/rate-limit/status")
async def get_current_rate_limit_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current rate limit status for the authenticated user"""
    try:
        client_id = f"user:{current_user.id}"
        status = await get_rate_limit_status(client_id)
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")

@router.post("/cache/invalidate")
async def invalidate_cache_pattern(
    pattern: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Invalidate cache entries matching a pattern"""
    try:
        deleted_count = await cache_service.invalidate_cache_pattern(pattern)
        return {
            "success": True,
            "message": f"Invalidated {deleted_count} cache entries matching pattern",
            "deleted_count": deleted_count,
            "pattern": pattern
        }
    except Exception as e:
        logger.error(f"Error invalidating cache pattern: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache pattern")
