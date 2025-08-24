import time
import hashlib
from typing import Optional, Tuple
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.redis import redis_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware with sliding window"""
    
    def __init__(self, app, calls_per_minute: int = None, calls_per_hour: int = None, burst_limit: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.calls_per_hour = calls_per_hour or settings.RATE_LIMIT_PER_HOUR
        self.burst_limit = burst_limit or settings.RATE_LIMIT_BURST
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and internal endpoints
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = await self._get_client_id(request)
        
        # Check rate limits
        is_allowed, reset_time, remaining = await self._check_rate_limit(client_id)
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "reset_time": reset_time,
                    "retry_after": max(0, reset_time - int(time.time()))
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(max(1, reset_time - int(time.time())))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    async def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get user ID from JWT token
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Hash IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        return f"ip:{ip_hash}"
    
    async def _check_rate_limit(self, client_id: str) -> Tuple[bool, int, int]:
        """Check if client is within rate limits using sliding window"""
        current_time = int(time.time())
        minute_window = current_time // 60
        hour_window = current_time // 3600
        
        # Keys for different time windows
        minute_key = f"rate_limit:minute:{client_id}:{minute_window}"
        hour_key = f"rate_limit:hour:{client_id}:{hour_window}"
        burst_key = f"rate_limit:burst:{client_id}"
        
        try:
            redis_client = await redis_manager.get_client()
            
            # Use Redis pipeline for atomic operations
            pipe = redis_client.pipeline()
            
            # Get current counts
            pipe.get(minute_key)
            pipe.get(hour_key)
            pipe.get(burst_key)
            
            results = await pipe.execute()
            minute_count = int(results[0] or 0)
            hour_count = int(results[1] or 0)
            burst_count = int(results[2] or 0)
            
            # Check burst limit (short-term protection)
            if burst_count >= self.burst_limit:
                burst_reset = await redis_manager.ttl(burst_key)
                if burst_reset > 0:
                    return False, current_time + burst_reset, 0
            
            # Check minute limit
            if minute_count >= self.calls_per_minute:
                next_minute = (minute_window + 1) * 60
                remaining = max(0, self.calls_per_minute - minute_count)
                return False, next_minute, remaining
            
            # Check hour limit
            if hour_count >= self.calls_per_hour:
                next_hour = (hour_window + 1) * 3600
                remaining = max(0, self.calls_per_hour - hour_count)
                return False, next_hour, remaining
            
            # Increment counters
            pipe = redis_client.pipeline()
            
            # Increment minute counter
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # Keep for 2 minutes
            
            # Increment hour counter
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # Keep for 2 hours
            
            # Increment burst counter
            pipe.incr(burst_key)
            pipe.expire(burst_key, 10)  # 10-second burst window
            
            await pipe.execute()
            
            # Calculate remaining requests
            remaining_minute = max(0, self.calls_per_minute - minute_count - 1)
            remaining_hour = max(0, self.calls_per_hour - hour_count - 1)
            remaining = min(remaining_minute, remaining_hour)
            
            next_reset = (minute_window + 1) * 60
            return True, next_reset, remaining
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if Redis is down
            return True, current_time + 60, self.calls_per_minute

class IPRateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple IP-based rate limiting for unauthenticated requests"""
    
    def __init__(self, app, calls_per_minute: int = 20):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
    
    async def dispatch(self, request: Request, call_next):
        # Skip for authenticated requests (handled by main rate limiter)
        if hasattr(request.state, 'user_id'):
            return await call_next(request)
        
        # Skip for health checks
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Hash IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        
        current_time = int(time.time())
        minute_window = current_time // 60
        key = f"ip_rate_limit:{ip_hash}:{minute_window}"
        
        try:
            redis_client = await redis_manager.get_client()
            
            # Get current count
            count = await redis_client.get(key)
            count = int(count or 0)
            
            if count >= self.calls_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests from this IP. Please try again later."
                    },
                    headers={
                        "Retry-After": "60"
                    }
                )
            
            # Increment counter
            await redis_client.incr(key)
            await redis_client.expire(key, 120)  # Keep for 2 minutes
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"IP rate limiting error: {e}")
            # Fail open
            return await call_next(request)

async def get_rate_limit_status(client_id: str) -> dict:
    """Get current rate limit status for a client"""
    current_time = int(time.time())
    minute_window = current_time // 60
    hour_window = current_time // 3600
    
    minute_key = f"rate_limit:minute:{client_id}:{minute_window}"
    hour_key = f"rate_limit:hour:{client_id}:{hour_window}"
    burst_key = f"rate_limit:burst:{client_id}"
    
    try:
        redis_client = await redis_manager.get_client()
        
        pipe = redis_client.pipeline()
        pipe.get(minute_key)
        pipe.get(hour_key)
        pipe.get(burst_key)
        pipe.ttl(minute_key)
        pipe.ttl(hour_key)
        pipe.ttl(burst_key)
        
        results = await pipe.execute()
        
        return {
            "minute_count": int(results[0] or 0),
            "hour_count": int(results[1] or 0),
            "burst_count": int(results[2] or 0),
            "minute_reset": results[3],
            "hour_reset": results[4],
            "burst_reset": results[5],
            "limits": {
                "per_minute": settings.RATE_LIMIT_PER_MINUTE,
                "per_hour": settings.RATE_LIMIT_PER_HOUR,
                "burst": settings.RATE_LIMIT_BURST
            }
        }
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return {
            "error": "Unable to fetch rate limit status",
            "limits": {
                "per_minute": settings.RATE_LIMIT_PER_MINUTE,
                "per_hour": settings.RATE_LIMIT_PER_HOUR,
                "burst": settings.RATE_LIMIT_BURST
            }
        }
