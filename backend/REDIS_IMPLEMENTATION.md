# Redis-based Rate Limiting and Caching Implementation

## Overview

This document describes the Redis-based rate limiting and caching system implemented for StrataAI. The implementation provides distributed rate limiting, response caching, and comprehensive cache management capabilities.

## Architecture

### Components

1. **Redis Connection Manager** (`app/core/redis.py`)
   - Manages Redis connections with connection pooling
   - Provides high-level Redis operations (get, set, incr, delete, etc.)
   - Handles JSON serialization/deserialization
   - Includes error handling and logging

2. **Rate Limiting Middleware** (`app/middleware/rate_limiting.py`)
   - `RateLimitingMiddleware`: User-based rate limiting with sliding window
   - `IPRateLimitingMiddleware`: IP-based rate limiting for unauthenticated requests
   - Supports per-minute, per-hour, and burst limits
   - Redis-backed for distributed rate limiting

3. **Response Caching Middleware** (`app/middleware/caching.py`)
   - `ResponseCachingMiddleware`: Caches GET responses with configurable TTL
   - `CacheService`: Provides cache management operations
   - Supports pattern-based cache invalidation
   - User-specific and endpoint-specific caching

4. **Cache Management API** (`app/api/cache_management.py`)
   - REST endpoints for cache statistics and management
   - Rate limit status monitoring
   - Cache invalidation controls

## Features

### Rate Limiting

- **Multi-tier Rate Limiting**:
  - Per-minute limits (default: 60 requests)
  - Per-hour limits (default: 1000 requests)
  - Burst protection (default: 10 requests in 10 seconds)

- **Client Identification**:
  - Authenticated users: `user:{user_id}`
  - Unauthenticated users: `ip:{hashed_ip}`

- **Sliding Window Algorithm**:
  - Uses Redis counters with TTL for efficient sliding window
  - Atomic operations with Redis pipelines
  - Graceful degradation (fail-open) on Redis errors

### Response Caching

- **Intelligent Caching**:
  - Only caches successful GET responses (200, 201)
  - Respects `Cache-Control: no-cache` headers
  - Configurable TTL per endpoint type

- **Cache Key Generation**:
  - Includes HTTP method, path, query parameters
  - User-specific caching for personalized responses
  - SHA256 hashing for privacy and uniqueness

- **TTL Configuration**:
  - Models endpoint: 1 hour (3600s)
  - Analytics endpoints: 1 minute (60s)
  - Default: 5 minutes (300s)

### Cache Management

- **Invalidation Strategies**:
  - Pattern-based invalidation
  - User-specific cache clearing
  - Endpoint-specific cache clearing
  - Full cache clearing

- **Monitoring**:
  - Cache hit/miss statistics
  - Memory usage tracking
  - TTL information for cache entries

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Rate Limiting Configuration
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_BURST=10

# Cache Configuration
CACHE_TTL_DEFAULT=300
CACHE_TTL_MODELS=3600
CACHE_TTL_ANALYTICS=60
CACHE_ENABLED=true
```

### Middleware Order

Middleware is added in reverse order of execution:

1. **ResponseCachingMiddleware** - First to execute, caches responses
2. **RateLimitingMiddleware** - Rate limiting for authenticated users
3. **IPRateLimitingMiddleware** - Rate limiting for unauthenticated users
4. **UsageLoggingMiddleware** - Last to execute, logs all requests

## API Endpoints

### Cache Management

- `GET /api/v1/system/cache/stats` - Get cache statistics
- `DELETE /api/v1/system/cache/clear` - Clear all cache (admin)
- `DELETE /api/v1/system/cache/user/{user_id}` - Clear user-specific cache
- `DELETE /api/v1/system/cache/endpoint?endpoint_pattern={pattern}` - Clear endpoint cache
- `POST /api/v1/system/cache/invalidate?pattern={pattern}` - Invalidate cache pattern

### Rate Limiting

- `GET /api/v1/system/rate-limit/status` - Get current rate limit status

## Usage Examples

### Rate Limiting Headers

Successful requests include rate limiting headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

Rate limited requests return:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "reset_time": 1640995200,
  "retry_after": 30
}
```

### Cache Headers

Cache hits include cache status:

```http
HTTP/1.1 200 OK
X-Cache-Status: HIT
Content-Type: application/json
```

### Programmatic Usage

```python
from app.core.redis import redis_manager
from app.middleware.caching import cache_service

# Basic Redis operations
await redis_manager.set("key", "value", ttl=300)
value = await redis_manager.get("key")

# JSON operations
await redis_manager.set_json("data", {"key": "value"}, ttl=300)
data = await redis_manager.get_json("data")

# Cache management
stats = await cache_service.get_cache_stats()
deleted = await cache_service.invalidate_cache_pattern("models")
```

## Error Handling

### Redis Connection Failures

- Rate limiting fails open (allows requests)
- Caching is bypassed
- Errors are logged but don't block requests
- Automatic reconnection attempts

### Graceful Degradation

- System continues to function without Redis
- Performance monitoring alerts on Redis failures
- Fallback to in-memory rate limiting (if implemented)

## Performance Considerations

### Redis Operations

- Uses Redis pipelines for atomic operations
- Connection pooling for efficient connection management
- Minimal Redis calls per request
- Efficient key expiration using TTL

### Memory Usage

- Cache keys use SHA256 hashes to limit key size
- Configurable TTL prevents unbounded memory growth
- Pattern-based cleanup for bulk operations
- Memory usage monitoring and alerting

## Security Considerations

### Rate Limiting

- IP address hashing for privacy
- User-based limits prevent abuse
- Burst protection against rapid-fire attacks
- Distributed rate limiting across instances

### Caching

- User-specific cache isolation
- No caching of sensitive endpoints
- Cache key hashing prevents enumeration
- Secure cache invalidation controls

## Monitoring and Observability

### Metrics

- Rate limit hit rates
- Cache hit/miss ratios
- Redis connection health
- Memory usage trends

### Logging

- Rate limit violations
- Cache operations
- Redis connection events
- Error conditions

## Testing

### Test Coverage

- Redis connection management
- Rate limiting logic and edge cases
- Cache middleware functionality
- API endpoint behavior
- Error handling scenarios

### Validation Script

Run the validation script to verify implementation:

```bash
cd backend
python validate_redis_implementation.py
```

## Deployment Considerations

### Redis Setup

- Use Redis Cluster for high availability
- Configure appropriate memory limits
- Set up monitoring and alerting
- Regular backup and recovery procedures

### Scaling

- Redis supports horizontal scaling
- Rate limits are distributed across instances
- Cache invalidation works across all nodes
- Consider Redis Sentinel for failover

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Check Redis server status
   - Verify connection string
   - Check network connectivity

2. **Rate Limiting Not Working**
   - Verify Redis connectivity
   - Check middleware order
   - Review rate limit configuration

3. **Cache Not Working**
   - Verify `CACHE_ENABLED=true`
   - Check endpoint patterns
   - Review TTL configuration

### Debug Commands

```bash
# Check Redis connectivity
redis-cli ping

# Monitor Redis operations
redis-cli monitor

# Check cache keys
redis-cli keys "cache:response:*"

# Check rate limit keys
redis-cli keys "rate_limit:*"
```

## Future Enhancements

### Planned Features

- Advanced rate limiting algorithms (token bucket, leaky bucket)
- Cache warming strategies
- Distributed cache invalidation events
- Rate limiting by API key or subscription tier
- Cache compression for large responses
- Redis Streams for real-time monitoring

### Performance Optimizations

- Lua scripts for atomic operations
- Connection multiplexing
- Cache preloading
- Intelligent cache eviction policies
