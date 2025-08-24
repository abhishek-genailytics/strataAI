import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.redis import RedisManager, redis_manager, get_redis


class TestRedisManager:
    """Test Redis connection manager"""
    
    @pytest.fixture
    def redis_manager_instance(self):
        """Create a fresh Redis manager instance for testing"""
        return RedisManager()
    
    @pytest_asyncio.async_test
    async def test_connect_success(self, redis_manager_instance):
        """Test successful Redis connection"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis
            
            result = await redis_manager_instance.connect()
            
            assert result == mock_redis
            mock_redis.ping.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_connect_failure(self, redis_manager_instance):
        """Test Redis connection failure"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            mock_from_url.return_value = mock_redis
            
            with pytest.raises(Exception, match="Connection failed"):
                await redis_manager_instance.connect()
    
    @pytest_asyncio.async_test
    async def test_disconnect(self, redis_manager_instance):
        """Test Redis disconnection"""
        # First connect
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            await redis_manager_instance.disconnect()
            
            mock_redis.close.assert_called_once()
            assert redis_manager_instance._redis is None
    
    @pytest_asyncio.async_test
    async def test_set_and_get(self, redis_manager_instance):
        """Test Redis set and get operations"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value="test_value")
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            # Test set
            result = await redis_manager_instance.set("test_key", "test_value")
            assert result is True
            mock_redis.set.assert_called_with("test_key", "test_value")
            
            # Test get
            result = await redis_manager_instance.get("test_key")
            assert result == "test_value"
            mock_redis.get.assert_called_with("test_key")
    
    @pytest_asyncio.async_test
    async def test_set_with_ttl(self, redis_manager_instance):
        """Test Redis set with TTL"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.setex = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            result = await redis_manager_instance.set("test_key", "test_value", ttl=300)
            assert result is True
            mock_redis.setex.assert_called_with("test_key", 300, "test_value")
    
    @pytest_asyncio.async_test
    async def test_json_operations(self, redis_manager_instance):
        """Test JSON set and get operations"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.set = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(return_value='{"key": "value"}')
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            test_data = {"key": "value"}
            
            # Test set_json
            result = await redis_manager_instance.set_json("test_key", test_data)
            assert result is True
            
            # Test get_json
            result = await redis_manager_instance.get_json("test_key")
            assert result == test_data
    
    @pytest_asyncio.async_test
    async def test_incr_operation(self, redis_manager_instance):
        """Test Redis increment operation"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.incr = AsyncMock(return_value=5)
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            result = await redis_manager_instance.incr("counter_key", 2)
            assert result == 5
            mock_redis.incr.assert_called_with("counter_key", 2)
    
    @pytest_asyncio.async_test
    async def test_delete_pattern(self, redis_manager_instance):
        """Test pattern-based key deletion"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.keys = AsyncMock(return_value=["key1", "key2", "key3"])
            mock_redis.delete = AsyncMock(return_value=3)
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            result = await redis_manager_instance.delete_pattern("test:*")
            assert result == 3
            mock_redis.keys.assert_called_with("test:*")
            mock_redis.delete.assert_called_with("key1", "key2", "key3")
    
    @pytest_asyncio.async_test
    async def test_error_handling(self, redis_manager_instance):
        """Test error handling in Redis operations"""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
            mock_from_url.return_value = mock_redis
            
            await redis_manager_instance.connect()
            
            # Should return None on error, not raise exception
            result = await redis_manager_instance.get("test_key")
            assert result is None

@pytest_asyncio.async_test
async def test_get_redis_dependency():
    """Test the get_redis dependency function"""
    with patch.object(redis_manager, 'get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        result = await get_redis()
        assert result == mock_client
        mock_get_client.assert_called_once()
