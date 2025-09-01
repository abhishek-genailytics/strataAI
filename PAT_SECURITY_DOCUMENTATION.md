# Personal Access Token (PAT) Security Documentation

## Overview

This document describes the Personal Access Token (PAT) system implemented in StrataAI, including security measures, encryption, and automatic token creation.

## 🔐 Security Features

### 1. Token Generation

- **Format**: `pat_` + 32 random bytes (base64 encoded)
- **Example**: `pat_cmiWAeHejjsBOfiRgjlxxXQe1TyGlTxLY1H_imCBYB4`
- **Entropy**: 256 bits of randomness using `secrets.token_urlsafe(32)`

### 2. Token Hashing

- **Algorithm**: SHA-256
- **Storage**: Only hashed tokens are stored in the database
- **Hash Length**: 64 characters (256 bits)
- **Example Hash**: `73dc505c34be5543727dbf4f51f04859809ee99cbef1d6056ad4dda67d43b416`

### 3. Token Display

- **Prefix Format**: First 8 characters + "..." + last 4 characters
- **Example**: `pat_cmiW...BYB4`
- **Security**: Full tokens are never stored or displayed after creation

## 🏗️ Database Schema

### `personal_access_tokens` Table

```sql
CREATE TABLE personal_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash
    token_prefix VARCHAR(20) NOT NULL,       -- Display prefix
    scopes JSONB DEFAULT '["api:read"]',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 Automatic Token Creation

### Default PAT Creation

When a user joins an organization, a default PAT is automatically created:

```sql
-- Trigger function
CREATE OR REPLACE FUNCTION create_default_pat_for_user()
RETURNS TRIGGER AS $$
DECLARE
    token_value TEXT;
    token_prefix TEXT;
    token_hash TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- Generate secure token
        token_value := 'pat_' || encode(gen_random_bytes(32), 'base64');
        token_prefix := substring(token_value from 1 for 8) || '...' || substring(token_value from length(token_value) - 3);
        token_hash := encode(sha256(token_value::bytea), 'hex');

        -- Insert default PAT
        INSERT INTO personal_access_tokens (
            user_id, organization_id, name, token_hash, token_prefix, scopes, is_active
        ) VALUES (
            NEW.user_id, NEW.organization_id, 'Default API Token', token_hash, token_prefix,
            '["api:read", "api:write"]'::jsonb, true
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### Trigger

```sql
CREATE TRIGGER on_user_organization_created
    AFTER INSERT ON user_organizations
    FOR EACH ROW EXECUTE FUNCTION create_default_pat_for_user();
```

## 🛡️ Security Measures

### 1. Row Level Security (RLS)

```sql
-- Users can only see their own tokens
CREATE POLICY "Users can view their own tokens" ON personal_access_tokens
    FOR SELECT USING (user_id = auth.uid());

-- Users can only create their own tokens
CREATE POLICY "Users can create their own tokens" ON personal_access_tokens
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- Users can only update their own tokens
CREATE POLICY "Users can update their own tokens" ON personal_access_tokens
    FOR UPDATE USING (user_id = auth.uid());

-- Users can only delete their own tokens
CREATE POLICY "Users can delete their own tokens" ON personal_access_tokens
    FOR DELETE USING (user_id = auth.uid());
```

### 2. Token Validation

- **Format Validation**: Must start with `pat_`
- **Length Validation**: Must be at least 40 characters
- **Hash Verification**: Stored hash must match provided token
- **Expiration Check**: Tokens are invalidated after expiration

### 3. Rate Limiting

- **Creation Limit**: 10 tokens per user per hour
- **Usage Limit**: 1000 API calls per token per hour
- **Brute Force Protection**: Failed attempts are logged and blocked

## 🔧 API Endpoints

### Create PAT

```http
POST /api/user-management/tokens
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "name": "My API Token",
  "scopes": ["api:read", "api:write"],
  "expires_at": "2025-01-01T00:00:00Z"
}
```

**Response** (Full token only returned once):

```json
{
  "id": "token-uuid",
  "name": "My API Token",
  "token": "pat_cmiWAeHejjsBOfiRgjlxxXQe1TyGlTxLY1H_imCBYB4",
  "token_prefix": "pat_cmiW...BYB4",
  "scopes": ["api:read", "api:write"],
  "created_at": "2024-12-26T10:00:00Z",
  "expires_at": "2025-01-01T00:00:00Z"
}
```

### List PATs

```http
GET /api/user-management/tokens
Authorization: Bearer <user_token>
```

**Response** (No full tokens):

```json
[
  {
    "id": "token-uuid",
    "name": "My API Token",
    "token_prefix": "pat_cmiW...BYB4",
    "scopes": ["api:read", "api:write"],
    "created_at": "2024-12-26T10:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": "2024-12-26T15:30:00Z"
  }
]
```

### Delete PAT

```http
DELETE /api/user-management/tokens/{token_id}
Authorization: Bearer <user_token>
```

## 🔍 Token Validation Process

### 1. Extract Token

```python
def extract_token(authorization_header: str) -> str:
    if not authorization_header.startswith("Bearer "):
        raise ValueError("Invalid authorization header")
    return authorization_header[7:]  # Remove "Bearer "
```

### 2. Validate Token Format

```python
def validate_token_format(token: str) -> bool:
    return token.startswith("pat_") and len(token) >= 40
```

### 3. Hash and Compare

```python
def validate_token(token: str, user_id: str) -> bool:
    # Hash the provided token
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Query database for matching hash
    result = supabase.table("personal_access_tokens").select("*").eq(
        "token_hash", token_hash
    ).eq("user_id", user_id).eq("is_active", True).execute()

    if not result.data:
        return False

    # Check expiration
    token_data = result.data[0]
    if token_data["expires_at"]:
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expires_at:
            return False

    # Update last_used_at
    supabase.table("personal_access_tokens").update({
        "last_used_at": datetime.utcnow().isoformat()
    }).eq("id", token_data["id"]).execute()

    return True
```

## 🚨 Security Best Practices

### 1. Token Storage

- ✅ **Do**: Store tokens in secure environment variables
- ✅ **Do**: Use token prefixes for display
- ❌ **Don't**: Store full tokens in databases
- ❌ **Don't**: Log full tokens

### 2. Token Usage

- ✅ **Do**: Use HTTPS for all API calls
- ✅ **Do**: Rotate tokens regularly
- ✅ **Do**: Set appropriate expiration dates
- ❌ **Don't**: Share tokens between users
- ❌ **Don't**: Use tokens in client-side code

### 3. Token Management

- ✅ **Do**: Monitor token usage
- ✅ **Do**: Implement rate limiting
- ✅ **Do**: Log failed authentication attempts
- ❌ **Don't**: Create tokens with excessive permissions

## 📊 Monitoring and Logging

### Token Usage Metrics

```sql
-- Track token usage
SELECT
    user_id,
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN expires_at < NOW() THEN 1 END) as expired_tokens,
    MAX(last_used_at) as last_activity
FROM personal_access_tokens
GROUP BY user_id;
```

### Security Events

- Failed authentication attempts
- Token creation/deletion
- Expired token access attempts
- Rate limit violations

## 🔄 Migration and Setup

### 1. Apply Migration

```bash
# Run the migration script
python apply_pat_migration.py
```

### 2. Test Security

```bash
# Run security tests
python test_pat_security.py
```

### 3. Verify Implementation

- Check that default PATs are created for new users
- Verify token hashing is working
- Test token validation
- Confirm RLS policies are active

## 🐛 Troubleshooting

### Common Issues

1. **"Token not found"**

   - Check if token is expired
   - Verify user_id matches token owner
   - Ensure token is active

2. **"Invalid token format"**

   - Token must start with `pat_`
   - Token must be at least 40 characters
   - Check for extra whitespace

3. **"Token hash mismatch"**
   - Token may have been corrupted
   - Check if token was copied correctly
   - Verify SHA-256 hashing

### Debug Commands

```sql
-- Check token hashes
SELECT id, name, token_prefix, created_at, expires_at
FROM personal_access_tokens
WHERE user_id = 'user-uuid';

-- Verify RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'personal_access_tokens';
```

## 📈 Performance Considerations

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_pat_user_id ON personal_access_tokens(user_id);
CREATE INDEX idx_pat_token_hash ON personal_access_tokens(token_hash);
CREATE INDEX idx_pat_expires_at ON personal_access_tokens(expires_at);
CREATE INDEX idx_pat_last_used_at ON personal_access_tokens(last_used_at);
```

### Caching

- Token validation results can be cached for 5 minutes
- User permissions can be cached for 1 minute
- Rate limit counters should be cached in Redis

## 🔮 Future Enhancements

### Planned Features

1. **Token Scopes**: Granular permission system
2. **Token Rotation**: Automatic token refresh
3. **Audit Logging**: Comprehensive activity tracking
4. **Token Analytics**: Usage patterns and insights
5. **Multi-factor Authentication**: Additional security layer

### Security Improvements

1. **Argon2 Hashing**: More secure than SHA-256 for storage
2. **Token Encryption**: Encrypt tokens at rest
3. **Hardware Security Modules**: HSM integration for token storage
4. **Zero-knowledge Proofs**: Privacy-preserving authentication

---

**Last Updated**: December 26, 2024  
**Version**: 1.0  
**Security Level**: Production Ready
