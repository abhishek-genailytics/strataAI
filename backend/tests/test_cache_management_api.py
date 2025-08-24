import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.api.cache_management import router
from app.middleware.caching import cache_service
from app.middleware.rate_limiting import get_rate_limit_status
from app.models.user import User


class TestCacheManagementAPI:
    """Test cache management API endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for authentication"""
        user = MagicMock(spec=User)
        user.id = "test_user_123"
        user.email = "test@example.com"
        return user
    
    @pytest_asyncio.async_test
    async def test_get_cache_statistics_success(self, mock_user):
        """Test successful cache statistics retrieval"""
        mock_stats = {
            "total_cached_responses": 150,
            "memory_usage": "2.5MB",
            "cache_enabled": True,
            "default_ttl": 300
        }
        
        with patch.object(cache_service, 'get_cache_stats') as mock_get_stats:
            mock_get_stats.return_value = mock_stats
            
            from app.api.cache_management import get_cache_statistics
            
            result = await get_cache_statistics(current_user=mock_user)
            
            assert result["success"] is True
            assert result["data"] == mock_stats
            mock_get_stats.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_get_cache_statistics_error(self, mock_user):
        """Test cache statistics retrieval with error"""
        with patch.object(cache_service, 'get_cache_stats') as mock_get_stats:
            mock_get_stats.side_effect = Exception("Redis connection failed")
            
            from app.api.cache_management import get_cache_statistics
            
            with pytest.raises(HTTPException) as exc_info:
                await get_cache_statistics(current_user=mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to get cache statistics" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_clear_all_cache_success(self, mock_user):
        """Test successful cache clearing"""
        with patch.object(cache_service, 'clear_all_cache') as mock_clear:
            mock_clear.return_value = 25
            
            from app.api.cache_management import clear_all_cache
            
            result = await clear_all_cache(current_user=mock_user)
            
            assert result["success"] is True
            assert result["deleted_count"] == 25
            assert "Cleared 25 cache entries" in result["message"]
            mock_clear.assert_called_once()
    
    @pytest_asyncio.async_test
    async def test_clear_all_cache_error(self, mock_user):
        """Test cache clearing with error"""
        with patch.object(cache_service, 'clear_all_cache') as mock_clear:
            mock_clear.side_effect = Exception("Redis error")
            
            from app.api.cache_management import clear_all_cache
            
            with pytest.raises(HTTPException) as exc_info:
                await clear_all_cache(current_user=mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to clear cache" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_clear_user_cache_own_cache(self, mock_user):
        """Test user clearing their own cache"""
        user_id = mock_user.id
        
        with patch.object(cache_service, 'invalidate_user_cache') as mock_invalidate:
            mock_invalidate.return_value = 10
            
            from app.api.cache_management import clear_user_cache
            
            result = await clear_user_cache(user_id=user_id, current_user=mock_user)
            
            assert result["success"] is True
            assert result["deleted_count"] == 10
            mock_invalidate.assert_called_with(user_id)
    
    @pytest_asyncio.async_test
    async def test_clear_user_cache_other_user_forbidden(self, mock_user):
        """Test user trying to clear another user's cache"""
        other_user_id = "other_user_456"
        
        from app.api.cache_management import clear_user_cache
        
        with pytest.raises(HTTPException) as exc_info:
            await clear_user_cache(user_id=other_user_id, current_user=mock_user)
        
        assert exc_info.value.status_code == 403
        assert "Can only clear your own cache" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_clear_user_cache_error(self, mock_user):
        """Test user cache clearing with error"""
        user_id = mock_user.id
        
        with patch.object(cache_service, 'invalidate_user_cache') as mock_invalidate:
            mock_invalidate.side_effect = Exception("Redis error")
            
            from app.api.cache_management import clear_user_cache
            
            with pytest.raises(HTTPException) as exc_info:
                await clear_user_cache(user_id=user_id, current_user=mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to clear user cache" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_clear_endpoint_cache_success(self, mock_user):
        """Test successful endpoint cache clearing"""
        endpoint_pattern = "/api/v1/models"
        
        with patch.object(cache_service, 'invalidate_endpoint_cache') as mock_invalidate:
            mock_invalidate.return_value = 5
            
            from app.api.cache_management import clear_endpoint_cache
            
            result = await clear_endpoint_cache(
                endpoint_pattern=endpoint_pattern, 
                current_user=mock_user
            )
            
            assert result["success"] is True
            assert result["deleted_count"] == 5
            assert result["pattern"] == endpoint_pattern
            mock_invalidate.assert_called_with(endpoint_pattern)
    
    @pytest_asyncio.async_test
    async def test_clear_endpoint_cache_error(self, mock_user):
        """Test endpoint cache clearing with error"""
        endpoint_pattern = "/api/v1/models"
        
        with patch.object(cache_service, 'invalidate_endpoint_cache') as mock_invalidate:
            mock_invalidate.side_effect = Exception("Redis error")
            
            from app.api.cache_management import clear_endpoint_cache
            
            with pytest.raises(HTTPException) as exc_info:
                await clear_endpoint_cache(
                    endpoint_pattern=endpoint_pattern, 
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 500
            assert "Failed to clear endpoint cache" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_get_rate_limit_status_success(self, mock_user):
        """Test successful rate limit status retrieval"""
        mock_status = {
            "minute_count": 5,
            "hour_count": 50,
            "burst_count": 1,
            "limits": {
                "per_minute": 60,
                "per_hour": 1000,
                "burst": 10
            }
        }
        
        with patch('app.api.cache_management.get_rate_limit_status') as mock_get_status:
            mock_get_status.return_value = mock_status
            
            from app.api.cache_management import get_current_rate_limit_status
            
            result = await get_current_rate_limit_status(current_user=mock_user)
            
            assert result["success"] is True
            assert result["data"] == mock_status
            mock_get_status.assert_called_with(f"user:{mock_user.id}")
    
    @pytest_asyncio.async_test
    async def test_get_rate_limit_status_error(self, mock_user):
        """Test rate limit status retrieval with error"""
        with patch('app.api.cache_management.get_rate_limit_status') as mock_get_status:
            mock_get_status.side_effect = Exception("Redis error")
            
            from app.api.cache_management import get_current_rate_limit_status
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_rate_limit_status(current_user=mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to get rate limit status" in str(exc_info.value.detail)
    
    @pytest_asyncio.async_test
    async def test_invalidate_cache_pattern_success(self, mock_user):
        """Test successful cache pattern invalidation"""
        pattern = "analytics"
        
        with patch.object(cache_service, 'invalidate_cache_pattern') as mock_invalidate:
            mock_invalidate.return_value = 8
            
            from app.api.cache_management import invalidate_cache_pattern
            
            result = await invalidate_cache_pattern(pattern=pattern, current_user=mock_user)
            
            assert result["success"] is True
            assert result["deleted_count"] == 8
            assert result["pattern"] == pattern
            mock_invalidate.assert_called_with(pattern)
    
    @pytest_asyncio.async_test
    async def test_invalidate_cache_pattern_error(self, mock_user):
        """Test cache pattern invalidation with error"""
        pattern = "analytics"
        
        with patch.object(cache_service, 'invalidate_cache_pattern') as mock_invalidate:
            mock_invalidate.side_effect = Exception("Redis error")
            
            from app.api.cache_management import invalidate_cache_pattern
            
            with pytest.raises(HTTPException) as exc_info:
                await invalidate_cache_pattern(pattern=pattern, current_user=mock_user)
            
            assert exc_info.value.status_code == 500
            assert "Failed to invalidate cache pattern" in str(exc_info.value.detail)


class TestCacheManagementIntegration:
    """Integration tests for cache management endpoints"""
    
    @pytest.fixture
    def mock_get_current_user(self):
        """Mock the get_current_user dependency"""
        user = MagicMock(spec=User)
        user.id = "test_user_123"
        user.email = "test@example.com"
        return user
    
    def test_cache_stats_endpoint_structure(self):
        """Test that cache stats endpoint has correct structure"""
        from app.api.cache_management import get_cache_statistics
        import inspect
        
        # Check function signature
        sig = inspect.signature(get_cache_statistics)
        assert 'current_user' in sig.parameters
        
        # Check return type annotation if present
        if hasattr(get_cache_statistics, '__annotations__'):
            return_type = get_cache_statistics.__annotations__.get('return')
            # Should return Dict[str, Any] or similar
            assert return_type is not None
    
    def test_rate_limit_status_endpoint_structure(self):
        """Test that rate limit status endpoint has correct structure"""
        from app.api.cache_management import get_current_rate_limit_status
        import inspect
        
        # Check function signature
        sig = inspect.signature(get_current_rate_limit_status)
        assert 'current_user' in sig.parameters
    
    def test_cache_clear_endpoints_require_auth(self):
        """Test that cache clearing endpoints require authentication"""
        from app.api.cache_management import clear_all_cache, clear_user_cache, clear_endpoint_cache
        import inspect
        
        for endpoint in [clear_all_cache, clear_user_cache, clear_endpoint_cache]:
            sig = inspect.signature(endpoint)
            assert 'current_user' in sig.parameters
    
    @pytest_asyncio.async_test
    async def test_cache_service_methods_exist(self):
        """Test that cache service has all required methods"""
        from app.middleware.caching import CacheService
        
        service = CacheService()
        
        # Check that all required methods exist
        required_methods = [
            'get_cache_stats',
            'clear_all_cache',
            'invalidate_user_cache',
            'invalidate_endpoint_cache',
            'invalidate_cache_pattern'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name)
            method = getattr(service, method_name)
            assert callable(method)
    
    def test_router_tags_and_prefix(self):
        """Test that router has correct configuration"""
        from app.api.cache_management import router
        
        # Router should be properly configured
        assert hasattr(router, 'routes')
        assert len(router.routes) > 0
        
        # Check that routes exist
        route_paths = [route.path for route in router.routes]
        expected_paths = [
            '/cache/stats',
            '/cache/clear',
            '/cache/user/{user_id}',
            '/cache/endpoint',
            '/rate-limit/status',
            '/cache/invalidate'
        ]
        
        for expected_path in expected_paths:
            assert any(expected_path in path for path in route_paths)
