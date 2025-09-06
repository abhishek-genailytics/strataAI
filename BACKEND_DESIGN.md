# StrataAI Backend Design Document

## Overview

The StrataAI backend is a FastAPI-based unified API gateway that provides OpenAI-compatible interfaces for multiple AI providers. It implements a sophisticated multi-tenant architecture with comprehensive authentication, rate limiting, observability, and cost tracking capabilities.

**Technology Stack:**
- **Framework:** FastAPI 0.104.1 with Uvicorn
- **Database:** PostgreSQL via Supabase
- **Caching:** Redis 5.0.1
- **Authentication:** Supabase Auth + Custom PAT system
- **HTTP Client:** HTTPX + AIOHTTP
- **Monitoring:** Structured logging with custom middleware

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   External      │    │   Mobile/CLI    │
│   (React)       │    │   Applications  │    │   Applications  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ Supabase Auth        │ PAT Auth             │ PAT Auth
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    StrataAI API Gateway                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Playground  │  │ Unified API │  │    Management APIs      │  │
│  │   Routes    │  │   Gateway   │  │  (Users/Orgs/Keys)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ OpenAI  │ │Anthropic│ │ Future  │
    │   API   │ │   API   │ │Provider │
    └─────────┘ └─────────┘ └─────────┘
```

### Two-Tier Authentication Architecture

1. **Playground (Simple):** Frontend → Supabase Auth → Direct Provider APIs
2. **External Apps (Complex):** Applications → PAT → Unified API → Provider APIs

## Directory Structure

```
backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── unified_api.py     # OpenAI-compatible gateway
│   │   ├── playground.py      # Playground-specific endpoints
│   │   ├── api_keys.py        # API key management
│   │   ├── organizations.py   # Organization management
│   │   ├── user_management.py # User profile management
│   │   ├── chat_sessions.py   # Chat session management
│   │   ├── providers.py       # AI provider management
│   │   ├── models.py          # AI model catalog
│   │   └── routes.py          # Main router configuration
│   ├── core/                  # Core infrastructure
│   │   ├── config.py          # Application configuration
│   │   ├── deps.py            # Dependency injection
│   │   ├── database.py        # Database connection
│   │   ├── redis.py           # Redis connection
│   │   ├── encryption.py      # Encryption utilities
│   │   └── exceptions.py      # Custom exceptions
│   ├── middleware/            # Custom middleware
│   │   ├── pat_auth.py        # PAT authentication
│   │   ├── rate_limiting.py   # Rate limiting
│   │   ├── caching.py         # Response caching
│   │   ├── usage_logging.py   # Request logging
│   │   └── error_handling.py  # Error handling
│   ├── services/              # Business logic layer
│   │   ├── llm_adapters.py    # Provider adapters
│   │   ├── playground_service.py # Playground logic
│   │   ├── api_key_service.py # API key management
│   │   ├── organization_service.py # Organization logic
│   │   └── [other services]
│   ├── models/                # Pydantic models
│   └── utils/                 # Utility functions
├── migrations/                # Database migrations
├── requirements.txt           # Python dependencies
└── Dockerfile                # Container configuration
```

## API Architecture

### Route Organization

The API is organized into logical modules with clear separation of concerns:

#### Core API Routes (`/api/v1`)

1. **Unified API Gateway** (`/v1/chat/completions`)
   - OpenAI-compatible endpoint
   - PAT authentication required
   - Supports all providers via model prefix routing

2. **Playground Routes** (`/playground/*`)
   - Simplified authentication (Supabase Auth only)
   - Direct provider API calls for performance
   - Session management and model configuration

3. **Management APIs**
   - `/organizations/*` - Organization management
   - `/user-management/*` - User profiles and settings
   - `/providers/*` - AI provider catalog
   - `/models/*` - AI model information

4. **System APIs**
   - `/system/*` - Cache management
   - `/errors/*` - Error reporting
   - `/mock-analytics/*` - Testing endpoints

### Authentication Patterns

#### 1. Supabase JWT Authentication
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """Validates Supabase JWT tokens for frontend access."""
```

#### 2. Personal Access Token (PAT) Authentication
```python
async def require_pat_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Validates PAT tokens for external API access."""
```

#### 3. Organization Context Resolution
```python
async def get_organization_context(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
) -> Optional[Organization]:
    """Resolves organization context from headers or user profile."""
```

## Service Layer Architecture

### Adapter Pattern for AI Providers

The system uses the adapter pattern to normalize different provider APIs:

```python
class LLMAdapter(ABC):
    """Abstract base class for LLM provider adapters."""
    
    @abstractmethod
    async def chat_completion(
        self, 
        request: ChatCompletionRequest, 
        api_key: str
    ) -> ChatCompletionResponse:
        """Execute chat completion request and return normalized response."""
        pass
```

#### Implemented Adapters:
- **OpenAIAdapter** - Direct OpenAI API integration
- **AnthropicAdapter** - Claude API with OpenAI normalization
- **AdapterFactory** - Dynamic adapter selection based on model prefix

### Key Services

#### 1. Playground Service (`playground_service.py`)
- **Purpose:** Direct provider API calls for playground interface
- **Features:** 
  - Model configuration management
  - Session-based chat completions
  - Token usage tracking
  - Provider-specific optimizations

#### 2. API Key Service (`api_key_service.py`)
- **Purpose:** Secure API key management per organization
- **Features:**
  - Encrypted key storage
  - Key validation and rotation
  - Provider-specific key handling
  - Usage tracking

#### 3. Organization Service (`organization_service.py`)
- **Purpose:** Multi-tenant organization management
- **Features:**
  - Organization CRUD operations
  - User invitation system
  - Role-based access control
  - Settings management

#### 4. LLM Adapters (`llm_adapters.py`)
- **Purpose:** Unified interface for multiple AI providers
- **Features:**
  - Request/response normalization
  - Streaming support
  - Error handling and retry logic
  - Cost calculation

## Middleware Stack

The middleware stack is carefully ordered for optimal performance and security:

### 1. Error Handling Middleware (Outermost)
```python
app.add_middleware(ErrorHandlingMiddleware, error_logging_service=error_logging_service)
```
- Catches all unhandled exceptions
- Structured error logging
- User-friendly error responses

### 2. Request Context Middleware
```python
app.add_middleware(RequestContextMiddleware)
```
- Adds request ID and timing
- Context propagation for logging
- Request metadata collection

### 3. Response Caching Middleware
```python
app.add_middleware(ResponseCachingMiddleware)
```
- Redis-based response caching
- Configurable TTL per endpoint
- Cache invalidation strategies

### 4. Rate Limiting Middleware (Disabled for debugging)
```python
# app.add_middleware(RateLimitingMiddleware)
# app.add_middleware(IPRateLimitingMiddleware, calls_per_minute=100)
```
- User-based and IP-based rate limiting
- Redis-backed counters
- Configurable limits per endpoint

### 5. Usage Logging Middleware (Innermost)
```python
app.add_middleware(UsageLoggingMiddleware)
```
- Comprehensive request/response logging
- Performance metrics collection
- Usage analytics data

## Configuration Management

### Environment-Based Configuration
```python
class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "StrataAI"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Cache Configuration
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_MODELS: int = 3600  # 1 hour
```

### Configuration Categories:
- **API Settings** - Versioning, project metadata
- **Database** - Supabase connection and service keys
- **Caching** - Redis configuration and TTL settings
- **Security** - Rate limits and encryption keys
- **CORS** - Allowed origins for frontend integration

## Data Models

### Core Pydantic Models

#### Chat Completion Models
```python
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    
class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage
```

#### Organization Models
```python
class Organization(BaseModel):
    id: UUID
    name: str
    display_name: Optional[str]
    settings: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
```

#### User Models
```python
class CurrentUser:
    def __init__(self, user_id: UUID, email: str, organizations: list = None):
        self.user_id = user_id
        self.email = email
        self.organizations = organizations or []
    
    def has_role_in_organization(self, org_id: UUID, required_roles: List[str]) -> bool:
        """Check if user has required roles in organization."""
```

## Database Integration

### Supabase Integration
- **Primary Client:** User-scoped operations with RLS
- **Service Client:** Admin operations bypassing RLS
- **Connection Management:** Singleton pattern with connection pooling

### Key Integration Patterns:

#### 1. Row Level Security (RLS) Compliance
```python
# User-scoped queries (respects RLS)
response = supabase.table("api_keys").select("*").execute()

# Admin queries (bypasses RLS)
response = supabase_service.table("api_keys").select("*").execute()
```

#### 2. Organization-Scoped Operations
```python
async def get_organization_api_keys(org_id: UUID) -> List[Dict]:
    """Get API keys for specific organization."""
    response = supabase_service.table("api_keys")\
        .select("*")\
        .eq("organization_id", str(org_id))\
        .execute()
    return response.data
```

## Security Architecture

### Multi-Layer Security

#### 1. Authentication Layer
- **Supabase JWT** for frontend authentication
- **PAT tokens** for API access
- **Service keys** for admin operations

#### 2. Authorization Layer
- **Role-based access control** (admin, member, owner)
- **Organization-scoped permissions**
- **Resource-level access control**

#### 3. Data Protection
- **API key encryption** using Fernet symmetric encryption
- **Token hashing** with SHA-256
- **Secure headers** and CORS configuration

#### 4. Rate Limiting
- **User-based limits** (requests per minute/hour)
- **IP-based limits** for DDoS protection
- **Endpoint-specific limits** for resource protection

### Encryption Implementation
```python
class EncryptionService:
    def __init__(self, key: str):
        self.fernet = Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
```

## Observability & Monitoring

### Structured Logging
```python
import structlog

logger = structlog.get_logger(__name__)

# Request logging with context
logger.info(
    "API request processed",
    endpoint=request.url.path,
    method=request.method,
    user_id=str(user.id),
    duration_ms=duration,
    status_code=response.status_code
)
```

### Metrics Collection
- **Request/Response metrics** via middleware
- **Token usage tracking** for cost analysis
- **Error rate monitoring** with categorization
- **Performance metrics** (latency, throughput)

### Error Handling
```python
class ErrorHandlingMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log error with context
            await self.error_logging_service.log_error(e, request)
            # Return user-friendly error
            return self.create_error_response(e)
```

## Performance Optimizations

### Caching Strategy

#### 1. Response Caching
- **Model lists** cached for 1 hour
- **Provider capabilities** cached for 1 hour
- **User profiles** cached for 5 minutes
- **Analytics data** cached for 1 minute

#### 2. Database Optimizations
- **Connection pooling** via Supabase
- **Query optimization** with selective fields
- **Batch operations** for bulk updates
- **Async operations** throughout

#### 3. HTTP Client Optimizations
```python
# Reusable HTTP client with connection pooling
self.client = httpx.AsyncClient(
    timeout=60.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)
```

## Deployment Architecture

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Management
- **Development:** Local PostgreSQL + Redis
- **Staging:** Supabase + Redis Cloud
- **Production:** Supabase + Redis Cloud with clustering

### Health Checks
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": await check_database_health(),
        "redis": await check_redis_health()
    }
```

## API Endpoints Reference

### Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info

### Unified API Gateway
- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `GET /v1/models` - List available models

### Playground Endpoints
- `GET /playground/models` - Get user's available models
- `POST /playground/chat/completions` - Direct chat completions
- `GET /playground/sessions` - List chat sessions
- `POST /playground/sessions` - Create new session

### Management Endpoints
- `GET /api/v1/organizations` - List organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/api-keys` - List API keys
- `POST /api/v1/api-keys` - Create API key
- `GET /api/v1/providers` - List AI providers
- `GET /api/v1/models` - List AI models

### System Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/system/cache/clear` - Clear cache
- `GET /api/v1/errors/recent` - Recent errors

## Error Handling Strategy

### Error Categories
1. **Authentication Errors** (401)
   - Invalid JWT tokens
   - Expired PAT tokens
   - Missing credentials

2. **Authorization Errors** (403)
   - Insufficient permissions
   - Organization access denied
   - Resource access denied

3. **Validation Errors** (422)
   - Invalid request format
   - Missing required fields
   - Type validation failures

4. **Provider Errors** (502/503)
   - OpenAI API failures
   - Anthropic API failures
   - Network timeouts

5. **System Errors** (500)
   - Database connection failures
   - Redis connection failures
   - Unexpected exceptions

### Error Response Format
```json
{
  "error": {
    "type": "authentication_error",
    "code": "invalid_token",
    "message": "The provided authentication token is invalid",
    "details": {
      "timestamp": "2025-09-06T21:27:23Z",
      "request_id": "req_123456789"
    }
  }
}
```

## Future Enhancements

### Planned Features
1. **Advanced Analytics**
   - Real-time usage dashboards
   - Cost optimization recommendations
   - Performance benchmarking

2. **Enhanced Security**
   - API key rotation automation
   - Advanced rate limiting algorithms
   - Comprehensive audit logging

3. **Provider Expansion**
   - Google PaLM integration
   - Cohere API support
   - Custom model hosting

4. **Performance Improvements**
   - Database query optimization
   - Advanced caching strategies
   - Load balancing support

5. **Enterprise Features**
   - SSO integration
   - Advanced organization management
   - Compliance reporting
   - Custom deployment options

### Technical Debt
1. **Rate Limiting** - Currently disabled, needs re-implementation
2. **API Key Validation** - Temporarily disabled, needs provider-specific validation
3. **Error Handling** - Some endpoints need better error categorization
4. **Testing** - Comprehensive test suite needed
5. **Documentation** - API documentation needs OpenAPI spec completion

---

*This document reflects the current state of the StrataAI backend as of September 6, 2025. The architecture continues to evolve based on user feedback and technical requirements.*
