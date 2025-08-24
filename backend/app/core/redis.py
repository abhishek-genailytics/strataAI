import redis.asyncio as redis
from typing import Optional
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis connection manager for caching and rate limiting"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        
    async def connect(self) -> redis.Redis:
        """Connect to Redis server"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                # Test connection
                await self._redis.ping()
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis
    
    async def disconnect(self):
        """Disconnect from Redis server"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")
    
    async def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._redis is None:
            await self.connect()
        return self._redis
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair with optional TTL"""
        try:
            client = await self.get_client()
            if ttl:
                return await client.setex(key, ttl, value)
            else:
                return await client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            client = await self.get_client()
            return bool(await client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            client = await self.get_client()
            return bool(await client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a key's value"""
        try:
            client = await self.get_client()
            return await client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for a key"""
        try:
            client = await self.get_client()
            return await client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for a key"""
        try:
            client = await self.get_client()
            return await client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -1
    
    async def set_json(self, key: str, value: dict, ttl: Optional[int] = None) -> bool:
        """Set a JSON value"""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, ttl)
        except Exception as e:
            logger.error(f"Redis SET_JSON error: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get a JSON value"""
        try:
            json_str = await self.get(key)
            if json_str:
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"Redis GET_JSON error: {e}")
            return None
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching a pattern"""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error: {e}")
            return 0

# Global Redis manager instance
redis_manager = RedisManager()

async def get_redis() -> redis.Redis:
    """Dependency to get Redis client"""
    return await redis_manager.get_client()
