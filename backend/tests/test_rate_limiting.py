import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware.rate_limiting import RateLimitingMiddleware, IPRateLimitingMiddleware, get_rate_limit_status
from app.core.redis import redis_manager


class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        async def app(scope, receive, send):
            response = JSONResponse({"message": "success"})
            await response(scope, receive, send)
        return app
    
    @pytest.fixture
    def rate_limiter(self, mock_app):
        """Create rate limiting middleware instance"""
        return RateLimitingMiddleware(mock_app, calls_per_minute=5, calls_per_hour=100, burst_limit=2)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = MagicMock()
        request.state.user_id = "test_user_123"
        return request
    
    @pytest_asyncio.async_test
    async def test_get_client_id_with_user(self, rate_limiter, mock_request):
        """Test client ID generation with authenticated user"""
        client_id = await rate_limiter._get_client_id(mock_request)
        assert client_id == "user:test_user_123"
    
    @pytest_asyncio.async_test
    async def test_get_client_id_with_ip(self, rate_limiter, mock_request):
        """Test client ID generation with IP address"""
        mock_request.state.user_id = None
        client_id = await rate_limiter._get_client_id(mock_request)
        assert client_id.startswith("ip:")
        assert len(client_id) == 19  # "ip:" + 16 char hash
    
    @pytest_asyncio.async_test
    async def test_get_client_id_with_forwarded_ip(self, rate_limiter, mock_request):
        """Test client ID generation with X-Forwarded-For header"""
        mock_request.state.user_id = None
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        client_id = await rate_limiter._get_client_id(mock_request)
        assert client_id.startswith("ip:")
    
    @pytest_asyncio.async_test
    async def test_skip_health_endpoints(self, rate_limiter, mock_request):
        """Test that health check endpoints are skipped"""
        mock_request.url.path = "/health"
        
        async def mock_call_next(request):
            return JSONResponse({"status": "healthy"})
        
        response = await rate_limiter.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_rate_limit_allowed(self, rate_limiter, mock_request):
        """Test request allowed within rate limits"""
        with patch.object(rate_limiter, '_check_rate_limit') as mock_check:
            mock_check.return_value = (True, int(time.time()) + 60, 4)
            
            async def mock_call_next(request):
                return JSONResponse({"message": "success"})
            
            response = await rate_limiter.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    @pytest_asyncio.async_test
    async def test_rate_limit_exceeded(self, rate_limiter, mock_request):
        """Test request blocked when rate limit exceeded"""
        with patch.object(rate_limiter, '_check_rate_limit') as mock_check:
            reset_time = int(time.time()) + 60
            mock_check.return_value = (False, reset_time, 0)
            
            async def mock_call_next(request):
                return JSONResponse({"message": "success"})
            
            response = await rate_limiter.dispatch(mock_request, mock_call_next)
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.body.decode()
            assert "Retry-After" in response.headers
    
    @pytest_asyncio.async_test
    async def test_check_rate_limit_within_limits(self, rate_limiter):
        """Test rate limit check when within limits"""
        client_id = "user:test_123"
        
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.pipeline.return_value = mock_redis
            mock_redis.get.return_value = None
            mock_redis.execute.return_value = [None, None, None]  # No existing counts
            mock_get_client.return_value = mock_redis
            
            is_allowed, reset_time, remaining = await rate_limiter._check_rate_limit(client_id)
            
            assert is_allowed is True
            assert remaining >= 0
            assert reset_time > int(time.time())
    
    @pytest_asyncio.async_test
    async def test_check_rate_limit_minute_exceeded(self, rate_limiter):
        """Test rate limit check when minute limit exceeded"""
        client_id = "user:test_123"
        
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.pipeline.return_value = mock_redis
            mock_redis.execute.return_value = [str(rate_limiter.calls_per_minute), "0", "0"]
            mock_get_client.return_value = mock_redis
            
            is_allowed, reset_time, remaining = await rate_limiter._check_rate_limit(client_id)
            
            assert is_allowed is False
            assert remaining == 0
    
    @pytest_asyncio.async_test
    async def test_check_rate_limit_burst_exceeded(self, rate_limiter):
        """Test rate limit check when burst limit exceeded"""
        client_id = "user:test_123"
        
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.pipeline.return_value = mock_redis
            mock_redis.execute.return_value = ["0", "0", str(rate_limiter.burst_limit)]
            mock_get_client.return_value = mock_redis
            
            with patch.object(redis_manager, 'ttl') as mock_ttl:
                mock_ttl.return_value = 5  # 5 seconds remaining
                
                is_allowed, reset_time, remaining = await rate_limiter._check_rate_limit(client_id)
                
                assert is_allowed is False
    
    @pytest_asyncio.async_test
    async def test_check_rate_limit_redis_error(self, rate_limiter):
        """Test rate limit check with Redis error (fail open)"""
        client_id = "user:test_123"
        
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Redis connection failed")
            
            is_allowed, reset_time, remaining = await rate_limiter._check_rate_limit(client_id)
            
            # Should fail open (allow request)
            assert is_allowed is True
            assert remaining == rate_limiter.calls_per_minute


class TestIPRateLimitingMiddleware:
    """Test IP-based rate limiting middleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        async def app(scope, receive, send):
            response = JSONResponse({"message": "success"})
            await response(scope, receive, send)
        return app
    
    @pytest.fixture
    def ip_rate_limiter(self, mock_app):
        """Create IP rate limiting middleware instance"""
        return IPRateLimitingMiddleware(mock_app, calls_per_minute=10)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request without user authentication"""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.client.host = "192.168.1.100"
        request.headers = {}
        request.state = MagicMock()
        # No user_id attribute to simulate unauthenticated request
        return request
    
    @pytest_asyncio.async_test
    async def test_skip_authenticated_requests(self, ip_rate_limiter, mock_request):
        """Test that authenticated requests are skipped"""
        mock_request.state.user_id = "test_user"
        
        async def mock_call_next(request):
            return JSONResponse({"message": "success"})
        
        response = await ip_rate_limiter.dispatch(mock_request, mock_call_next)
        assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_ip_rate_limit_allowed(self, ip_rate_limiter, mock_request):
        """Test IP rate limit when within limits"""
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "5"  # Current count
            mock_redis.incr = AsyncMock()
            mock_redis.expire = AsyncMock()
            mock_get_client.return_value = mock_redis
            
            async def mock_call_next(request):
                return JSONResponse({"message": "success"})
            
            response = await ip_rate_limiter.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200
    
    @pytest_asyncio.async_test
    async def test_ip_rate_limit_exceeded(self, ip_rate_limiter, mock_request):
        """Test IP rate limit when exceeded"""
        with patch.object(redis_manager, 'get_client') as mock_get_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "10"  # At limit
            mock_get_client.return_value = mock_redis
            
            async def mock_call_next(request):
                return JSONResponse({"message": "success"})
            
            response = await ip_rate_limiter.dispatch(mock_request, mock_call_next)
            assert response.status_code == 429
            assert "Too many requests from this IP" in response.body.decode()


@pytest_asyncio.async_test
async def test_get_rate_limit_status():
    """Test get_rate_limit_status function"""
    client_id = "user:test_123"
    
    with patch.object(redis_manager, 'get_client') as mock_get_client:
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.execute.return_value = ["5", "50", "1", 45, 3500, 8]
        mock_get_client.return_value = mock_redis
        
        status = await get_rate_limit_status(client_id)
        
        assert status["minute_count"] == 5
        assert status["hour_count"] == 50
        assert status["burst_count"] == 1
        assert "limits" in status
        assert status["limits"]["per_minute"] > 0


@pytest_asyncio.async_test
async def test_get_rate_limit_status_error():
    """Test get_rate_limit_status with Redis error"""
    client_id = "user:test_123"
    
    with patch.object(redis_manager, 'get_client') as mock_get_client:
        mock_get_client.side_effect = Exception("Redis error")
        
        status = await get_rate_limit_status(client_id)
        
        assert "error" in status
        assert "limits" in status
