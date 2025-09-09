# StrataAI API Endpoints Documentation

This document provides a comprehensive overview of all API endpoints available in the StrataAI backend system. The API is organized into three main categories: Unified API, Management API, and Playground API.

## Table of Contents

1. [Authentication](#authentication)
2. [Unified API (/v1/*)](#unified-api-v1)
3. [Management API (/api/v1/*)](#management-api-apiv1)
4. [Playground API (/api/v1/playground/*)](#playground-api-apiv1playground)
5. [Health & System](#health--system)

---

## Authentication

### Authentication Types

1. **PAT Authentication**: Used for `/v1/*` endpoints (Personal Access Tokens)
   - Header: `Authorization: Bearer <pat_token>`
   - Organization override: `X-Organization-ID: <uuid>`

2. **Supabase JWT Authentication**: Used for `/api/v1/*` endpoints
   - Header: `Authorization: Bearer <supabase_jwt>`
   - Automatic organization resolution from user context

---

## Unified API (/v1/*)

OpenAI-compatible endpoints for external applications using PAT authentication.

### Chat Completions

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/v1/chat/completions` | OpenAI-compatible chat completions with multi-provider support | PAT |

**Features:**
- Supports multiple providers: `openai/gpt-4`, `anthropic/claude-3.5`
- Organization-scoped API key management
- Usage tracking and cost calculation
- Non-streaming responses (MVP constraint)

### Playground Read Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/v1/playground/sessions/{session_id}` | Get session metadata and message count | PAT |
| GET | `/v1/playground/sessions/{session_id}/messages` | Get paginated messages with usage data | PAT |
| GET | `/v1/playground/sessions` | List user's sessions with pagination | PAT |
| GET | `/v1/playground/sessions/by-client-id/{client_session_id}` | Get session by client ID | PAT |

**Features:**
- Session ownership validation
- Token usage and cost data for assistant messages
- Cursor-based pagination
- OpenAI-compatible error responses

---

## Management API (/api/v1/*)

Internal management endpoints for the StrataAI application using Supabase JWT authentication.

### User Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/user-management/users` | List organization members | Supabase JWT |
| POST | `/api/v1/user-management/invite` | Invite new organization member | Supabase JWT |
| PUT | `/api/v1/user-management/members/{user_id}/role` | Update member role | Supabase JWT |
| DELETE | `/api/v1/user-management/users/{user_id}` | Remove organization member | Supabase JWT |

### Personal Access Tokens

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/user-management/tokens` | List user's PATs | Supabase JWT |
| POST | `/api/v1/user-management/tokens` | Create new PAT | Supabase JWT |
| DELETE | `/api/v1/user-management/tokens/{token_id}` | Revoke PAT | Supabase JWT |

### API Keys Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/api-keys` | List organization's API keys | Supabase JWT |
| POST | `/api/v1/api-keys` | Create new API key | Supabase JWT |
| PUT | `/api/v1/api-keys/{key_id}` | Update API key | Supabase JWT |
| DELETE | `/api/v1/api-keys/{key_id}` | Delete API key | Supabase JWT |
| POST | `/api/v1/api-keys/{key_id}/test` | Test API key validity | Supabase JWT |

### Organizations

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/organizations` | List user's organizations | Supabase JWT |
| POST | `/api/v1/organizations` | Create new organization | Supabase JWT |
| GET | `/api/v1/organizations/{org_id}` | Get organization details | Supabase JWT |

### Providers

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/providers` | List all available providers | Supabase JWT |
| GET | `/api/v1/providers/{provider_id}` | Get provider details | Supabase JWT |
| GET | `/api/v1/providers/{provider_id}/models` | List provider's models | Supabase JWT |
| POST | `/api/v1/providers/{provider_id}/configure` | Configure provider settings | Supabase JWT |
| GET | `/api/v1/providers/{provider_id}/status` | Get provider connection status | Supabase JWT |

### Models Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/models` | List available models | Supabase JWT |
| GET | `/api/v1/models/{model_id}` | Get model details | Supabase JWT |
| PUT | `/api/v1/models/{model_id}/enable` | Enable model for organization | Supabase JWT |
| PUT | `/api/v1/models/{model_id}/disable` | Disable model for organization | Supabase JWT |

### Usage Analytics

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/usage/summary` | Get usage summary | Supabase JWT |
| GET | `/api/v1/usage/details` | Get detailed usage data | Supabase JWT |
| GET | `/api/v1/usage/costs` | Get cost breakdown | Supabase JWT |
| GET | `/api/v1/usage/trends` | Get usage trends | Supabase JWT |

### Authentication & Auth

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/v1/auth/login` | User login | None |
| POST | `/api/v1/auth/logout` | User logout | Supabase JWT |
| POST | `/api/v1/auth/refresh` | Refresh authentication token | Supabase JWT |
| GET | `/api/v1/auth/me` | Get current user info | Supabase JWT |

### Cache Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| DELETE | `/api/v1/cache/clear` | Clear application cache | Supabase JWT |
| GET | `/api/v1/cache/stats` | Get cache statistics | Supabase JWT |
| DELETE | `/api/v1/cache/models` | Clear models cache | Supabase JWT |

### Error Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/errors` | List recent errors | Supabase JWT |
| GET | `/api/v1/errors/{error_id}` | Get error details | Supabase JWT |
| POST | `/api/v1/errors/{error_id}/resolve` | Mark error as resolved | Supabase JWT |

---

## Playground API (/api/v1/playground/*)

Playground-specific endpoints for the StrataAI web interface using Supabase JWT authentication.

### Chat & Completions

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/v1/playground/chat/completions` | Playground chat completions | Supabase JWT |
| POST | `/api/v1/playground/sessions/{session_id}/send` | Send message to session | Supabase JWT |

### Session Management

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/sessions` | List playground sessions | Supabase JWT |
| POST | `/api/v1/playground/sessions` | Create new session | Supabase JWT |
| GET | `/api/v1/playground/sessions/{session_id}` | Get session details | Supabase JWT |
| PUT | `/api/v1/playground/sessions/{session_id}` | Update session | Supabase JWT |
| DELETE | `/api/v1/playground/sessions/{session_id}` | Delete session | Supabase JWT |
| POST | `/api/v1/playground/sessions/{session_id}/clear` | Clear session messages | Supabase JWT |

### Messages

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/sessions/{session_id}/messages` | Get session messages | Supabase JWT |

### Models & Configuration

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/models` | List available playground models | Supabase JWT |

### Provider Keys & Status

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/providers/status` | Get provider key status | Supabase JWT |

### Usage & Analytics

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/sessions/{session_id}/usage` | Get session usage data | Supabase JWT |
| GET | `/api/v1/playground/sessions/{session_id}/usage/series` | Get usage time series | Supabase JWT |

### Actions

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| POST | `/api/v1/playground/sessions/{session_id}/regenerate` | Regenerate last response | Supabase JWT |

### System & Presets

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/system-prompts` | List system prompts | Supabase JWT |
| POST | `/api/v1/playground/system-prompts` | Create system prompt | Supabase JWT |
| GET | `/api/v1/playground/presets` | List parameter presets | Supabase JWT |
| POST | `/api/v1/playground/presets` | Create parameter preset | Supabase JWT |

### Export & Utilities

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/v1/playground/sessions/{session_id}/export/curl` | Export session as cURL | Supabase JWT |
| GET | `/api/v1/playground/picker` | Get model picker data | Supabase JWT |
| GET | `/api/v1/playground/hud` | Get HUD analytics data | Supabase JWT |

---

## Health & System

### Health Checks

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/` | Root endpoint with service info | None |
| GET | `/health` | Health check endpoint | None |
| GET | `/api/v1/health` | Detailed health check | None |

---

## Common Response Formats

### Success Response
```json
{
  "data": {...},
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123"
  }
}
```

### Error Response (OpenAI Format)
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "param": "model",
    "code": "invalid_model"
  }
}
```

### Pagination Response
```json
{
  "data": [...],
  "pagination": {
    "cursor": "next_cursor",
    "has_more": true,
    "limit": 20
  }
}
```

---

## Query Parameters

### Common Parameters

- `limit`: Number of items to return (default: 20, max: 200)
- `cursor`: Pagination cursor for next page
- `after_index`: For message pagination (≥-1)
- `provider`: Filter by provider (`openai`, `anthropic`)
- `include_pricing`: Include pricing data (default: true)
- `include_capabilities`: Include model capabilities (default: true)

### Time-based Parameters

- `window`: Time window (`all`, `24h`, `7d`, `30d`)
- `bucket`: Time bucket for series data (`hour`, `day`)
- `start_time`: Start time (RFC3339 format)
- `end_time`: End time (RFC3339 format)

---

## Rate Limits

- **Unified API**: 1000 requests/hour per PAT
- **Management API**: 10000 requests/hour per user
- **Playground API**: 5000 requests/hour per user

---

## Model ID Format

All model references use the format: `{provider}/{model_name}`

Examples:
- `openai/gpt-4o-mini`
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-3.5-turbo`

---

## Organization Context

### PAT Authentication (Unified API)
- Uses PAT's default organization
- Override with `X-Organization-ID` header
- Validates user membership in target organization

### Supabase JWT Authentication (Management/Playground API)
- Automatic organization resolution from user context
- Multi-tenant data isolation via RLS policies
- Session-based organization switching

---

## Error Codes

### Authentication Errors
- `missing_authorization`: No Authorization header
- `invalid_authorization`: Malformed Authorization header
- `invalid_token`: Invalid or expired token
- `missing_org_api_key`: No API key configured for provider
- `disabled_org_api_key`: API key exists but disabled

### Request Errors
- `invalid_request_error`: Invalid request parameters
- `invalid_model`: Unsupported model format
- `session_not_found`: Session doesn't exist or no access
- `provider_not_found`: Unknown provider

### System Errors
- `internal_error`: Internal server error
- `service_unavailable`: External service unavailable
- `rate_limit_exceeded`: Rate limit exceeded

---

*Last updated: September 2024*
*API Version: 1.0.0*
