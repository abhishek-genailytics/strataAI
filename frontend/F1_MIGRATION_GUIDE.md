# F1 Frontend API Client Migration Guide

## Overview

The F1 infrastructure provides a unified OpenAI-compatible API client for StrataAI with proper authentication, organization context, and error handling. This guide explains how to migrate from the existing API service to the new F1 system.

## What's Been Implemented

### Core Infrastructure
- ✅ **Environment Configuration** (`src/config/env.ts`, `.env.local`)
- ✅ **Organization Context** (`src/contexts/OrgContext.tsx`)
- ✅ **HTTP Client with Interceptors** (`src/utils/http.ts`)
- ✅ **Error Normalization** (`src/utils/errors.ts`, `src/types/api.ts`)
- ✅ **OpenAI-Compatible Service** (`src/services/openai.ts`)
- ✅ **Unified API Service** (`src/services/unified-api.ts`)
- ✅ **Hook Wrapper** (`src/hooks/useApiClient.ts`)
- ✅ **Basic Tests** (`src/__tests__/services/openai.test.ts`)

### Key Features
- **Single HTTP Client**: One axios instance with automatic auth and org header injection
- **OpenAI Error Contract**: All errors return `{ error: { message, type, param, code } }` format
- **Provider-Agnostic Models**: Frontend uses `openai/gpt-4`, `anthropic/claude-3` format
- **Zero Secret Leakage**: Only user session tokens in browser, API keys stay server-side
- **Request Correlation**: Automatic `X-Client-Request-ID` for log correlation
- **Multi-tenant Support**: `X-Organization-ID` header for organization routing

## Migration Strategies

### Option 1: Gradual Migration (Recommended)

Keep existing `apiService` for current functionality, gradually migrate to F1:

```typescript
// For new features - use F1 unified API
import { useApiClient } from '../hooks/useApiClient';
import { useAuth } from '../contexts/AuthContext';

function MyNewComponent() {
  const { user } = useAuth();
  const { openai } = useApiClient(user?.access_token);
  
  const handleChatCompletion = async () => {
    const result = await openai.createChatCompletion({
      model: 'openai/gpt-4',
      messages: [{ role: 'user', content: 'Hello' }]
    });
    
    if (result.ok) {
      console.log(result.data);
    } else {
      console.error(result.error);
    }
  };
}
```

### Option 2: Direct Unified Service

Use the unified service that provides both legacy and F1 methods:

```typescript
// Import the unified service instead of old apiService
import { useUnifiedApiService } from '../services/unified-api';
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { user } = useAuth();
  const api = useUnifiedApiService(user?.access_token);
  
  // Use F1 method for new OpenAI-compatible calls
  const newChatCompletion = async () => {
    const result = await api.createChatCompletion({
      model: 'openai/gpt-4',
      messages: [{ role: 'user', content: 'Hello' }]
    });
  };
  
  // Use legacy method for existing playground functionality
  const legacyPlayground = async () => {
    const result = await api.playgroundChatCompletion({
      model: 'openai/gpt-4',
      messages: [{ role: 'user', content: 'Hello' }],
      stream: true
    });
  };
}
```

## Organization Context Usage

The new `OrgProvider` enables multi-tenant API calls:

```typescript
import { useOrg } from '../contexts/OrgContext';

function OrganizationSwitcher() {
  const { orgId, setOrgId } = useOrg();
  
  const switchOrganization = (newOrgId: string) => {
    setOrgId(newOrgId);
    // All subsequent API calls will include X-Organization-ID header
  };
}
```

## Error Handling

All F1 methods return consistent error format:

```typescript
const result = await api.createChatCompletion(request);

if (result.ok) {
  // Success case
  console.log(result.data);
} else {
  // Error case - always has OpenAI-style error
  const { message, type, code } = result.error;
  
  switch (type) {
    case 'timeout_error':
      showToast('Request timed out, please try again');
      break;
    case 'network_error':
      showToast('Network error, check your connection');
      break;
    case 'api_error':
      showToast(`API Error: ${message}`);
      break;
    default:
      showToast('An unexpected error occurred');
  }
}
```

## Migration Checklist

### Immediate (Required)
- [x] Environment variables configured in `.env.local`
- [x] `OrgProvider` added to `App.tsx` (already done)
- [ ] Update components to use organization context where needed

### Phase 1: New Features
- [ ] Use `useApiClient` hook for all new chat completion features
- [ ] Implement provider-agnostic model selection using `provider/model` format
- [ ] Use F1 error handling for new components

### Phase 2: Legacy Migration
- [ ] Replace `apiService` imports with `useUnifiedApiService` in existing components
- [ ] Update error handling to use consistent OpenAI format
- [ ] Test all existing functionality with new service

### Phase 3: Cleanup
- [ ] Remove old `apiService` singleton once all components migrated
- [ ] Update tests to use new service structure
- [ ] Remove legacy error handling patterns

## File Structure

```
src/
├── config/
│   └── env.ts                    # Environment configuration
├── contexts/
│   └── OrgContext.tsx           # Organization context provider
├── utils/
│   ├── http.ts                  # HTTP client with interceptors
│   └── errors.ts                # Error normalization utilities
├── types/
│   └── api.ts                   # API type definitions
├── services/
│   ├── openai.ts               # Pure OpenAI-compatible service
│   ├── unified-api.ts          # Unified service (legacy + F1)
│   └── api.ts                  # Existing service (keep for now)
├── hooks/
│   └── useApiClient.ts         # Hook wrapper for components
└── __tests__/
    └── services/
        └── openai.test.ts      # Basic smoke tests
```

## Best Practices

### 1. Model ID Format
Always use `provider/model` format:
```typescript
// ✅ Correct
model: 'openai/gpt-4'
model: 'anthropic/claude-3.5-sonnet'

// ❌ Incorrect
model: 'gpt-4'
model: 'openai:gpt-4'
```

### 2. Error Handling
Always check the `ok` field:
```typescript
// ✅ Correct
const result = await api.createChatCompletion(request);
if (result.ok) {
  // Use result.data
} else {
  // Handle result.error
}

// ❌ Incorrect
const data = await api.createChatCompletion(request);
// Assumes success, will break on errors
```

### 3. Organization Context
Set organization context early in user session:
```typescript
// In your auth flow or organization selector
const { setOrgId } = useOrg();
setOrgId(user.selectedOrganizationId);
```

### 4. Request Correlation
The `X-Client-Request-ID` header is automatically added for log correlation. Use it in error reporting:
```typescript
// The request ID is available in network dev tools
// and can be used to correlate frontend errors with backend logs
```

## Troubleshooting

### Common Issues

1. **Missing Organization Header**
   - Ensure `OrgProvider` is wrapped around your components
   - Set `orgId` using `setOrgId()` from `useOrg()`

2. **Authentication Errors**
   - Verify access token is passed to `useApiClient()` or `useUnifiedApiService()`
   - Check token expiration and refresh logic

3. **Network Timeouts**
   - Default timeout is 30 seconds
   - Adjust in `src/utils/http.ts` if needed

4. **CORS Issues**
   - Ensure backend CORS is configured for your frontend domain
   - Check `REACT_APP_API_BASE_URL` in `.env.local`

### Debug Mode

Enable debug logging:
```typescript
// Add to your component for debugging
console.log('API Base URL:', Env.apiBaseUrl);
console.log('Current Org ID:', orgId);
```

## Next Steps

1. **Start with New Features**: Use F1 infrastructure for any new chat completion features
2. **Test Integration**: Verify organization context and error handling work correctly
3. **Gradual Migration**: Move existing components to unified service one by one
4. **Monitor Performance**: Check request correlation IDs in logs
5. **Clean Up**: Remove old API service once migration is complete

This migration enables StrataAI to have a consistent, OpenAI-compatible API interface while maintaining backward compatibility with existing functionality.
