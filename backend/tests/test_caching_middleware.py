import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request, Response
from starlette.responses import JSONResponse

from app.middleware.caching import ResponseCachingMiddleware, CacheService, cache_service
from app.core.redis import redis_manager


class TestResponseCachingMiddleware:
    """Test response caching middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        async def app(scope, receive, send):
            response = JSONResponse({"data": "test_response"})
            await response(scope, receive, send)
        return app
    
    @pytest.fixture
    def cache_middleware(self, mock_app):
        """Create caching middleware instance"""
        return ResponseCachingMiddleware(mock_app, default_ttl=300)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock GET request"""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/v1/models"
        request.url.query = ""
        request.query_params = {}
        request.state = MagicMock()
        request.state.user_id = "test_user_123"
        return request
    
    @pytest_asyncio.async_test
    async def test_skip_caching_disabled(self, cache_middleware, mock_request):
        """Test that caching is skipped when disabled"""
        with patch('app.core.config.settings.CACHE_ENABLED', False):
            async def mock_call_next(request):
                return JSONResponse({"message": "success"})
            
            response = await cache_middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_skip_non_cacheable_methods(self, cache_middleware, mock_request):
        """Test that non-GET methods are not cached"""
        mock_request.method = "POST"
        
        async def mock_call_next(request):
            return JSONResponse({"message": "success"})
        
        response = await cache_middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_skip_non_cacheable_endpoints(self, cache_middleware, mock_request):
        """Test that certain endpoints are not cached"""
        mock_request.url.path = "/api/v1/chat/completions"
        
        async def mock_call_next(request):
            return JSONResponse({"message": "success"})
        
        response = await cache_middleware.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_generate_cache_key(self, cache_middleware, mock_request):
        """Test cache key generation"""
        cache_key = await cache_middleware._generate_cache_key(mock_request)
        
        assert cache_key.startswith("cache:response:")
        assert len(cache_key) > 20  # Should be a hash
    
    @pytest_asyncio.async_test
    async def test_generate_cache_key_with_query_params(self, cache_middleware, mock_request):
        """Test cache key generation with query parameters"""
        mock_request.query_params = {"limit": "10", "offset": "0"}
        
        cache_key1 = await cache_middleware._generate_cache_key(mock_request)
        
        # Change query params
        mock_request.query_params = {"limit": "20", "offset": "0"}
        cache_key2 = await cache_middleware._generate_cache_key(mock_request)
        
        # Keys should be different
        assert cache_key1 != cache_key2
    
    @pytest_asyncio.async_test
    async def test_cache_hit(self, cache_middleware, mock_request):
        """Test cache hit scenario"""
        cached_data = {
            "status_code": 200,
            "headers": {"content-type": "application/json"},
            "body": '{"cached": true}',
            "content_type": "application/json"
        }
        
        with patch.object(cache_middleware, '_get_cached_response') as mock_get_cache:
            mock_get_cache.return_value = cached_data
            
            async def mock_call_next(request):
                return JSONResponse({"message": "should not be called"})
            
            response = await cache_middleware.dispatch(mock_request, mock_call_next)
            
            assert response.status_code == 200
            assert response.headers.get("X-Cache-Status") == "HIT"
            assert '{"cached": true}' in response.body.decode()
    
    @pytest_asyncio.async_test
    async def test_cache_miss_and_store(self, cache_middleware, mock_request):
        """Test cache miss and subsequent storage"""
        with patch.object(cache_middleware, '_get_cached_response') as mock_get_cache, \
             patch.object(cache_middleware, '_cache_response') as mock_cache_response:
            
            mock_get_cache.return_value = None  # Cache miss
            
            async def mock_call_next(request):
                return JSONResponse({"message": "fresh response"})
            
            response = await cache_middleware.dispatch(mock_request, mock_call_next)
            
            assert response.status_code == 200
            mock_cache_response.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_should_cache_response_success(self, cache_middleware):
        """Test should_cache_response for successful responses"""
        response = MagicMock()
        response.status_code = 200
        response.headers = {}
        
        assert cache_middleware._should_cache_response(response) is True
    
    @pytest_asyncio.async_test
    async def test_should_cache_response_error(self, cache_middleware):
        """Test should_cache_response for error responses"""
        response = MagicMock()
        response.status_code = 500
        response.headers = {}
        
        assert cache_middleware._should_cache_response(response) is False
    
    @pytest_asyncio.async_test
    async def test_should_cache_response_no_cache_header(self, cache_middleware):
        """Test should_cache_response with no-cache header"""
        response = MagicMock()
        response.status_code = 200
        response.headers = {"cache-control": "no-cache"}
        
        assert cache_middleware._should_cache_response(response) is False
    
    @pytest_asyncio.async_test
    async def test_get_ttl_for_path(self, cache_middleware):
        """Test TTL determination for different paths"""
        # Models endpoint
        ttl = cache_middleware._get_ttl_for_path("/api/v1/models")
        assert ttl == cache_middleware.endpoint_ttl_map["/api/v1/models"]
        
        # Analytics endpoint
        ttl = cache_middleware._get_ttl_for_path("/api/v1/analytics/usage")
        assert ttl == cache_middleware.endpoint_ttl_map["/api/v1/analytics"]
        
        # Default TTL
        ttl = cache_middleware._get_ttl_for_path("/api/v1/unknown")
        assert ttl == cache_middleware.default_ttl
    
    @pytest_asyncio.async_test
    async def test_get_cached_response(self, cache_middleware):
        """Test getting cached response from Redis"""
        cache_key = "test_cache_key"
        cached_data = {"status_code": 200, "body": "cached"}
        
        with patch.object(redis_manager, 'get_json') as mock_get_json:
            mock_get_json.return_value = cached_data
            
            result = await cache_middleware._get_cached_response(cache_key)
            assert result == cached_data
            mock_get_json.assert_called_with(cache_key)
    
    @pytest_asyncio.async_test
    async def test_get_cached_response_error(self, cache_middleware):
        """Test getting cached response with Redis error"""
        cache_key = "test_cache_key"
        
        with patch.object(redis_manager, 'get_json') as mock_get_json:
            mock_get_json.side_effect = Exception("Redis error")
            
            result = await cache_middleware._get_cached_response(cache_key)
            assert result is None


class TestCacheService:
    """Test cache service functionality"""
    
    @pytest_asyncio.async_test
    async def test_invalidate_cache_pattern(self):
        """Test invalidating cache by pattern"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.return_value = 5
            
            result = await cache_service.invalidate_cache_pattern("models")
            assert result == 5
            mock_delete.assert_called_with("cache:response:*models*")
    
    @pytest_asyncio.async_test
    async def test_invalidate_user_cache(self):
        """Test invalidating cache for specific user"""
        user_id = "test_user_123"
        
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.return_value = 3
            
            result = await cache_service.invalidate_user_cache(user_id)
            assert result == 3
            mock_delete.assert_called_with(f"cache:response:*user:{user_id}*")
    
    @pytest_asyncio.async_test
    async def test_invalidate_endpoint_cache(self):
        """Test invalidating cache for specific endpoint"""
        endpoint = "/api/v1/models"
        
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.return_value = 2
            
            result = await cache_service.invalidate_endpoint_cache(endpoint)
            assert result == 2
            mock_delete.assert_called_with(f"cache:response:*{endpoint}*")
    
    @pytest_asyncio.async_test
    async def test_clear_all_cache(self):
        """Test clearing all cache"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.return_value = 10
            
            result = await cache_service.clear_all_cache()
            assert result == 10
            mock_delete.assert_called_with("cache:response:*")
    
    @pytest_asyncio.async_test
    async def test_get_cache_stats(self):
        """Test getting cache statistics"""
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.keys.return_value = ["key1", "key2", "key3"]
            mock_redis.info.return_value = {"used_memory_human": "1.5MB"}
            mock_redis.ttl.return_value = 300
            mock_get_client.return_value = mock_redis
            
            stats = await cache_service.get_cache_stats()
            
            assert stats["total_cached_responses"] == 3
            assert stats["memory_usage"] == "1.5MB"
            assert "sample_ttls" in stats
            assert "cache_enabled" in stats
    
    @pytest_asyncio.async_test
    async def test_get_cache_stats_error(self):
        """Test getting cache statistics with Redis error"""
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Redis connection error")
            
            stats = await cache_service.get_cache_stats()
            
            assert "error" in stats
            assert stats["error"] == "Unable to fetch cache statistics"
    
    @pytest_asyncio.async_test
    async def test_invalidate_cache_pattern_error(self):
        """Test invalidating cache pattern with Redis error"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.side_effect = Exception("Redis error")
            
            result = await cache_service.invalidate_cache_pattern("test")
            assert result == 0
    
    @pytest_asyncio.async_test
    async def test_invalidate_user_cache_error(self):
        """Test invalidating user cache with Redis error"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.side_effect = Exception("Redis error")
            
            result = await cache_service.invalidate_user_cache("user123")
            assert result == 0
    
    @pytest_asyncio.async_test
    async def test_invalidate_endpoint_cache_error(self):
        """Test invalidating endpoint cache with Redis error"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.side_effect = Exception("Redis error")
            
            result = await cache_service.invalidate_endpoint_cache("/api/test")
            assert result == 0
    
    @pytest_asyncio.async_test
    async def test_clear_all_cache_error(self):
        """Test clearing all cache with Redis error"""
        with patch.object(redis_manager, 'delete_pattern') as mock_delete:
            mock_delete.side_effect = Exception("Redis error")
            
            result = await cache_service.clear_all_cache()
            assert result == 0
