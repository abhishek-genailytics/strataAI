import hashlib
import json
from typing import Optional, List, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import logging

from app.core.redis import redis_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class ResponseCachingMiddleware(BaseHTTPMiddleware):
    """Redis-based response caching middleware"""
    
    def __init__(
        self,
        app,
        default_ttl: int = None,
        cacheable_methods: List[str] = None,
        cache_key_prefix: str = "cache:response"
    ):
        super().__init__(app)
        self.default_ttl = default_ttl or settings.CACHE_TTL_DEFAULT
        self.cacheable_methods = cacheable_methods or ["GET"]
        self.cache_key_prefix = cache_key_prefix
        
        # Define cache TTL for different endpoint patterns
        self.endpoint_ttl_map = {
            "/api/v1/models": settings.CACHE_TTL_MODELS,
            "/api/v1/analytics": settings.CACHE_TTL_ANALYTICS,
            "/api/v1/usage-metrics": settings.CACHE_TTL_ANALYTICS,
            "/api/v1/cost-analysis": settings.CACHE_TTL_ANALYTICS,
        }
        
        # Endpoints that should not be cached
        self.non_cacheable_patterns = [
            "/api/v1/chat/completions",  # Dynamic AI responses
            "/api/v1/auth",              # Authentication endpoints
            "/api/v1/api-keys",          # Sensitive data
            "/health",                   # Health checks
            "/docs",                     # Documentation
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip caching if disabled
        if not settings.CACHE_ENABLED:
            return await call_next(request)
        
        # Only cache specified HTTP methods
        if request.method not in self.cacheable_methods:
            return await call_next(request)
        
        # Skip non-cacheable endpoints
        if self._should_skip_cache(request.url.path):
            return await call_next(request)
        
        # Generate cache key
        cache_key = await self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for key: {cache_key}")
            return self._create_response_from_cache(cached_response)
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if self._should_cache_response(response):
            await self._cache_response(cache_key, response, request.url.path)
            logger.debug(f"Cached response for key: {cache_key}")
        
        return response
    
    def _should_skip_cache(self, path: str) -> bool:
        """Check if endpoint should skip caching"""
        return any(pattern in path for pattern in self.non_cacheable_patterns)
    
    def _should_cache_response(self, response: Response) -> bool:
        """Check if response should be cached"""
        # Only cache successful responses
        if response.status_code not in [200, 201]:
            return False
        
        # Don't cache responses with certain headers
        if response.headers.get("cache-control") == "no-cache":
            return False
        
        return True
    
    async def _generate_cache_key(self, request: Request) -> str:
        """Generate unique cache key for request"""
        # Include method, path, query parameters, and user context
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include user ID for user-specific caching
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            key_components.append(f"user:{user_id}")
        
        # Create hash of components
        key_string = "|".join(key_components)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        return f"{self.cache_key_prefix}:{key_hash}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response from Redis"""
        try:
            cached_data = await redis_manager.get_json(cache_key)
            return cached_data
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None
    
    async def _cache_response(self, cache_key: str, response: Response, path: str):
        """Cache response in Redis"""
        try:
            # Determine TTL based on endpoint
            ttl = self._get_ttl_for_path(path)
            
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Prepare cache data
            cache_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body.decode("utf-8"),
                "content_type": response.headers.get("content-type", "application/json")
            }
            
            # Cache the response
            await redis_manager.set_json(cache_key, cache_data, ttl)
            
            # Recreate response body iterator
            response.body_iterator = self._create_body_iterator(response_body)
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    def _get_ttl_for_path(self, path: str) -> int:
        """Get TTL for specific endpoint path"""
        for pattern, ttl in self.endpoint_ttl_map.items():
            if pattern in path:
                return ttl
        return self.default_ttl
    
    def _create_response_from_cache(self, cached_data: Dict[str, Any]) -> Response:
        """Create FastAPI response from cached data"""
        headers = cached_data.get("headers", {})
        headers["X-Cache-Status"] = "HIT"
        
        return Response(
            content=cached_data["body"],
            status_code=cached_data["status_code"],
            headers=headers,
            media_type=cached_data.get("content_type", "application/json")
        )
    
    def _create_body_iterator(self, body: bytes):
        """Create async iterator for response body"""
        async def body_iterator():
            yield body
        return body_iterator()

class CacheService:
    """Service for managing cache operations"""
    
    @staticmethod
    async def invalidate_cache_pattern(pattern: str) -> int:
        """Invalidate cache entries matching a pattern"""
        try:
            full_pattern = f"cache:response:*{pattern}*"
            deleted_count = await redis_manager.delete_pattern(full_pattern)
            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")
            return 0
    
    @staticmethod
    async def invalidate_user_cache(user_id: str) -> int:
        """Invalidate all cache entries for a specific user"""
        try:
            pattern = f"cache:response:*user:{user_id}*"
            deleted_count = await redis_manager.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries for user: {user_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating user cache {user_id}: {e}")
            return 0
    
    @staticmethod
    async def invalidate_endpoint_cache(endpoint_pattern: str) -> int:
        """Invalidate cache for specific endpoint pattern"""
        try:
            pattern = f"cache:response:*{endpoint_pattern}*"
            deleted_count = await redis_manager.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries for endpoint: {endpoint_pattern}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating endpoint cache {endpoint_pattern}: {e}")
            return 0
    
    @staticmethod
    async def clear_all_cache() -> int:
        """Clear all response cache"""
        try:
            pattern = "cache:response:*"
            deleted_count = await redis_manager.delete_pattern(pattern)
            logger.info(f"Cleared all response cache: {deleted_count} entries")
            return deleted_count
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return 0
    
    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_client = await redis_manager.get_client()
            
            # Get cache keys count
            cache_keys = await redis_client.keys("cache:response:*")
            total_keys = len(cache_keys)
            
            # Get memory usage (approximate)
            info = await redis_client.info("memory")
            memory_usage = info.get("used_memory_human", "N/A")
            
            # Sample TTL information
            ttl_info = {}
            if cache_keys:
                sample_keys = cache_keys[:10]  # Sample first 10 keys
                for key in sample_keys:
                    ttl = await redis_client.ttl(key)
                    ttl_info[key] = ttl
            
            return {
                "total_cached_responses": total_keys,
                "memory_usage": memory_usage,
                "sample_ttls": ttl_info,
                "cache_enabled": settings.CACHE_ENABLED,
                "default_ttl": settings.CACHE_TTL_DEFAULT
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": "Unable to fetch cache statistics"}

# Global cache service instance
cache_service = CacheService()
