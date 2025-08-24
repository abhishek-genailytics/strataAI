#!/usr/bin/env python3
"""
Validation script for Redis-based rate limiting and caching implementation
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.redis import redis_manager
from app.middleware.caching import cache_service
from app.middleware.rate_limiting import get_rate_limit_status
from app.core.config import settings

async def test_redis_connection():
    """Test Redis connection"""
    print("🔗 Testing Redis connection...")
    try:
        await redis_manager.connect()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_basic_redis_operations():
    """Test basic Redis operations"""
    print("\n📝 Testing basic Redis operations...")
    try:
        # Test set and get
        await redis_manager.set("test_key", "test_value", ttl=60)
        value = await redis_manager.get("test_key")
        assert value == "test_value", f"Expected 'test_value', got '{value}'"
        
        # Test JSON operations
        test_data = {"message": "hello", "count": 42}
        await redis_manager.set_json("test_json", test_data, ttl=60)
        retrieved_data = await redis_manager.get_json("test_json")
        assert retrieved_data == test_data, f"JSON data mismatch"
        
        # Test increment
        await redis_manager.incr("test_counter", 5)
        counter_value = await redis_manager.get("test_counter")
        assert int(counter_value) == 5, f"Expected 5, got {counter_value}"
        
        # Cleanup
        await redis_manager.delete("test_key")
        await redis_manager.delete("test_json")
        await redis_manager.delete("test_counter")
        
        print("✅ Basic Redis operations working correctly")
        return True
    except Exception as e:
        print(f"❌ Basic Redis operations failed: {e}")
        return False

async def test_rate_limiting_logic():
    """Test rate limiting logic"""
    print("\n⏱️  Testing rate limiting logic...")
    try:
        client_id = "test_user_validation"
        
        # Get initial status
        status = await get_rate_limit_status(client_id)
        print(f"   Rate limit status: {status}")
        
        # Test that we have the expected structure
        assert "limits" in status, "Rate limit status missing 'limits'"
        assert "per_minute" in status["limits"], "Missing per_minute limit"
        assert "per_hour" in status["limits"], "Missing per_hour limit"
        assert "burst" in status["limits"], "Missing burst limit"
        
        print("✅ Rate limiting logic structure correct")
        return True
    except Exception as e:
        print(f"❌ Rate limiting logic test failed: {e}")
        return False

async def test_cache_service():
    """Test cache service functionality"""
    print("\n🗄️  Testing cache service...")
    try:
        # Test cache stats
        stats = await cache_service.get_cache_stats()
        print(f"   Cache stats: {stats}")
        
        # Test cache operations
        test_pattern = "validation_test"
        deleted_count = await cache_service.invalidate_cache_pattern(test_pattern)
        print(f"   Invalidated {deleted_count} cache entries for pattern '{test_pattern}'")
        
        print("✅ Cache service working correctly")
        return True
    except Exception as e:
        print(f"❌ Cache service test failed: {e}")
        return False

async def test_configuration():
    """Test configuration settings"""
    print("\n⚙️  Testing configuration...")
    try:
        print(f"   Redis URL: {settings.REDIS_URL}")
        print(f"   Rate limit per minute: {settings.RATE_LIMIT_PER_MINUTE}")
        print(f"   Rate limit per hour: {settings.RATE_LIMIT_PER_HOUR}")
        print(f"   Rate limit burst: {settings.RATE_LIMIT_BURST}")
        print(f"   Cache enabled: {settings.CACHE_ENABLED}")
        print(f"   Default cache TTL: {settings.CACHE_TTL_DEFAULT}")
        print(f"   Models cache TTL: {settings.CACHE_TTL_MODELS}")
        print(f"   Analytics cache TTL: {settings.CACHE_TTL_ANALYTICS}")
        
        # Validate configuration values
        assert settings.RATE_LIMIT_PER_MINUTE > 0, "Rate limit per minute must be positive"
        assert settings.RATE_LIMIT_PER_HOUR > 0, "Rate limit per hour must be positive"
        assert settings.RATE_LIMIT_BURST > 0, "Rate limit burst must be positive"
        assert settings.CACHE_TTL_DEFAULT > 0, "Cache TTL must be positive"
        
        print("✅ Configuration validation passed")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

async def main():
    """Main validation function"""
    print("🚀 Starting Redis Implementation Validation")
    print("=" * 50)
    
    tests = [
        test_redis_connection,
        test_basic_redis_operations,
        test_rate_limiting_logic,
        test_cache_service,
        test_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Cleanup
    try:
        await redis_manager.disconnect()
        print("\n🔌 Redis connection closed")
    except Exception as e:
        print(f"⚠️  Warning: Error closing Redis connection: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed! Redis implementation is working correctly.")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed. Some issues need to be addressed.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with unexpected error: {e}")
        sys.exit(1)
