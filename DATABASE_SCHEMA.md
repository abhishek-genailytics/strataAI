# StrataAI Database Schema Design Document

## Overview

This document provides a comprehensive overview of the StrataAI database schema, extracted from the live Supabase project. The database is designed to support a unified AI API gateway that provides OpenAI-compatible interfaces for multiple AI providers.

**Project Information:**
- **Project ID:** pucvturagllxmkvmwoqv
- **Project Name:** strataAI
- **Database Version:** PostgreSQL 17.4.1.074
- **Region:** ap-south-1
- **Status:** ACTIVE_HEALTHY

## Architecture Overview

The StrataAI database follows a multi-tenant architecture with the following key components:

1. **User Management & Authentication** - Built on Supabase Auth
2. **Organization Management** - Multi-tenant organization structure
3. **AI Provider Integration** - Support for multiple AI providers (OpenAI, Anthropic, etc.)
4. **API Key Management** - Secure storage and management of provider API keys
5. **Model Configuration** - AI model definitions and pricing
6. **Chat Session Management** - Conversation history and token tracking
7. **Access Control** - Personal Access Tokens (PATs) and rate limiting

## Database Tables

### Core User & Organization Tables

#### `user_profiles`
Extends Supabase Auth users with additional profile information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | References auth.users.id |
| `organization_name` | text | nullable | Legacy field for organization name |
| `subscription_tier` | text | CHECK: free/pro/enterprise | User's subscription level |
| `full_name` | varchar | nullable | User's full name |
| `avatar_url` | text | nullable | Profile picture URL |
| `bio` | text | nullable | User biography |
| `website` | varchar | nullable | User's website |
| `location` | varchar | nullable | User's location |
| `timezone` | varchar | nullable | User's timezone |
| `preferences` | jsonb | default: {} | User preferences |
| `metadata` | jsonb | default: {} | Additional metadata |
| `is_active` | boolean | default: true | Account status |
| `organization_id` | uuid | nullable, FK | Current organization |
| `role` | varchar | default: member | User role in organization |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

#### `organizations`
Multi-tenant organization structure for team management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Organization identifier |
| `name` | text | NOT NULL | Organization name |
| `display_name` | text | nullable | Display name |
| `description` | text | nullable | Organization description |
| `website` | text | nullable | Organization website |
| `logo_url` | text | nullable | Organization logo |
| `settings` | jsonb | default: {} | Organization settings |
| `metadata` | jsonb | default: {} | Additional metadata |
| `is_active` | boolean | default: true | Organization status |
| `owner_id` | uuid | FK to auth.users | Organization owner |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

#### `user_organizations`
Junction table for user-organization relationships.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Relationship identifier |
| `user_id` | uuid | FK to auth.users | User reference |
| `organization_id` | uuid | FK to organizations | Organization reference |
| `role` | varchar | CHECK: admin/member | User role in organization |
| `is_active` | boolean | default: true | Membership status |
| `is_owner` | boolean | default: false | Owner flag |
| `is_admin` | boolean | default: false | Admin flag |
| `joined_at` | timestamptz | default: now() | Join timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

#### `user_invitations`
Manages organization invitations for new users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Invitation identifier |
| `organization_id` | uuid | FK to organizations | Target organization |
| `invited_by_user_id` | uuid | FK to auth.users | Inviting user |
| `email` | text | NOT NULL | Invitee email |
| `role` | text | CHECK: admin/member | Invited role |
| `invitation_token` | text | UNIQUE | Secure invitation token |
| `status` | text | CHECK: pending/accepted/expired/cancelled | Invitation status |
| `expires_at` | timestamptz | default: now() + 7 days | Expiration time |
| `accepted_at` | timestamptz | nullable | Acceptance timestamp |
| `accepted_by_user_id` | uuid | nullable, FK | Accepting user |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

### AI Provider & Model Management

#### `ai_providers`
Defines supported AI providers (OpenAI, Anthropic, etc.).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Provider identifier |
| `name` | text | UNIQUE | Provider internal name |
| `display_name` | text | NOT NULL | Human-readable name |
| `base_url` | text | NOT NULL | Provider API base URL |
| `logo_url` | text | nullable | Provider logo |
| `website_url` | text | nullable | Provider website |
| `description` | text | nullable | Provider description |
| `is_active` | boolean | default: true | Provider status |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** No (public reference data)
**Current Rows:** 7 (OpenAI, Anthropic, Perplexity, xAI Grok, Qwen, Mistral, Cohere)

#### `ai_models`
Catalog of available AI models from all providers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Model identifier |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `model_name` | text | NOT NULL | Model internal name |
| `display_name` | text | NOT NULL | Human-readable name |
| `description` | text | nullable | Model description |
| `model_type` | text | CHECK: chat/completion/embedding/image/audio/multimodal | Model type |
| `max_tokens` | integer | nullable | Maximum output tokens |
| `max_input_tokens` | integer | nullable | Maximum input tokens |
| `supports_streaming` | boolean | default: false | Streaming support |
| `supports_function_calling` | boolean | default: false | Function calling support |
| `supports_vision` | boolean | default: false | Vision capabilities |
| `supports_audio` | boolean | default: false | Audio capabilities |
| `capabilities` | jsonb | default: {} | Additional capabilities |
| `metadata` | jsonb | default: {} | Model metadata |
| `is_active` | boolean | default: true | Model availability |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** No (public reference data)
**Current Rows:** 25

#### `model_pricing`
Pricing information for AI models.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Pricing record identifier |
| `model_id` | uuid | FK to ai_models | Model reference |
| `pricing_type` | text | CHECK: input/output/per_request/per_second | Pricing type |
| `price_per_unit` | numeric | NOT NULL | Price per unit |
| `unit` | text | CHECK: token/request/second/minute | Pricing unit |
| `currency` | text | default: USD | Currency code |
| `region` | text | default: global | Pricing region |
| `effective_from` | timestamptz | default: now() | Effective start date |
| `effective_until` | timestamptz | nullable | Effective end date |
| `is_active` | boolean | default: true | Pricing status |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** No (public reference data)
**Current Rows:** 48

#### `provider_capabilities`
Extended capabilities for AI providers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Capability identifier |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `capability_name` | text | NOT NULL | Capability name |
| `capability_value` | jsonb | nullable | Capability configuration |
| `description` | text | nullable | Capability description |
| `is_active` | boolean | default: true | Capability status |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** No

### API Key & Access Management

#### `api_keys`
Secure storage of provider API keys per organization.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | API key identifier |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `organization_id` | uuid | FK to organizations | Organization reference |
| `name` | text | NOT NULL | Key name/description |
| `encrypted_key_value` | text | NOT NULL | Encrypted API key |
| `key_prefix` | text | nullable | Key prefix for identification |
| `is_active` | boolean | default: true | Key status |
| `last_used_at` | timestamptz | nullable | Last usage timestamp |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes
**Current Rows:** 2
**Note:** Each organization can have one API key per provider

#### `personal_access_tokens`
Personal Access Tokens for API authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | PAT identifier |
| `user_id` | uuid | FK to auth.users | Token owner |
| `organization_id` | uuid | FK to organizations | Organization context |
| `name` | text | NOT NULL | Token name |
| `token_hash` | text | UNIQUE | Hashed token value |
| `token_prefix` | text | NOT NULL | Token prefix |
| `scopes` | text[] | default: {} | Token permissions |
| `last_used_at` | timestamptz | nullable | Last usage timestamp |
| `expires_at` | timestamptz | nullable | Expiration timestamp |
| `is_active` | boolean | default: true | Token status |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes
**Current Rows:** 2

### User Configuration

#### `user_model_configurations`
User-specific model configurations and preferences.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Configuration identifier |
| `user_id` | uuid | FK to auth.users | User reference |
| `organization_id` | uuid | FK to organizations | Organization context |
| `model_id` | uuid | FK to ai_models | Model reference |
| `is_enabled` | boolean | default: true | Model availability for user |
| `configuration` | jsonb | default: {} | Model-specific settings |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

#### `org_model_enablement`
Organization-level model visibility and access control.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Enablement identifier |
| `organization_id` | uuid | FK to organizations | Organization reference |
| `model_id` | uuid | FK to ai_models | Model reference |
| `is_enabled` | boolean | default: true | Model visibility for organization |
| `created_at` | timestamptz | default: now() | Creation timestamp |

**RLS Enabled:** Yes
**Unique Constraint:** (organization_id, model_id)

### Chat & Session Management

#### `chat_sessions`
Manages chat conversation sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Session identifier |
| `user_id` | uuid | nullable, FK to auth.users | Session owner |
| `provider` | text | NOT NULL | AI provider used |
| `model` | text | NOT NULL | AI model used |
| `session_name` | text | nullable | Human-readable session name |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes
**Current Rows:** 16

#### `chat_messages`
Individual messages within chat sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Message identifier |
| `session_id` | uuid | nullable, FK to chat_sessions | Session reference |
| `role` | text | CHECK: user/assistant/system | Message role |
| `content` | text | NOT NULL | Message content |
| `created_at` | timestamptz | default: now() | Creation timestamp |

**RLS Enabled:** Yes
**Current Rows:** 32

#### `token_usage`
Tracks token consumption for cost analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Usage record identifier |
| `message_id` | uuid | FK to chat_messages | Message reference |
| `input_tokens` | integer | default: 0 | Input tokens consumed |
| `output_tokens` | integer | default: 0 | Output tokens consumed |
| `total_tokens` | integer | default: 0 | Total tokens consumed |
| `created_at` | timestamptz | default: now() | Creation timestamp |

**RLS Enabled:** Yes
**Current Rows:** 32

### Observability & Analytics

#### `api_requests`
Logs all API requests for monitoring and analytics with first-class accounting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Request identifier |
| `api_key_id` | uuid | nullable, FK to api_keys | API key used |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `endpoint` | text | NOT NULL | API endpoint called |
| `method` | text | NOT NULL | HTTP method |
| `status_code` | integer | NOT NULL | Response status code |
| `request_size` | integer | nullable | Request size in bytes |
| `response_size` | integer | nullable | Response size in bytes |
| `duration_ms` | integer | nullable | Request duration |
| `error_message` | text | nullable | Error details if failed |
| `metadata` | jsonb | default: {} | Additional request metadata |
| `organization_id` | uuid | nullable, FK to organizations | Organization reference |
| `model_id` | uuid | nullable, FK to ai_models | Model reference |
| `provider_request_id` | text | nullable | Upstream provider request ID |
| `prompt_tokens` | integer | default: 0 | Input tokens consumed |
| `completion_tokens` | integer | default: 0 | Output tokens consumed |
| `total_tokens` | integer | default: 0 | Total tokens consumed |
| `cost` | numeric(18,6) | default: 0 | Request cost in USD |
| `currency` | text | default: 'USD' | Currency code |
| `created_at` | timestamptz | default: now() | Request timestamp |

**RLS Enabled:** Yes
**Indexes:** `idx_api_requests_org_time` on (organization_id, created_at DESC)

#### `usage_metrics`
Aggregated usage metrics for reporting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Metric identifier |
| `user_id` | uuid | FK to auth.users | User reference |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `metric_type` | text | CHECK: requests/tokens/cost/errors | Metric type |
| `metric_value` | numeric | NOT NULL | Metric value |
| `time_period` | text | CHECK: hour/day/week/month | Aggregation period |
| `period_start` | timestamptz | NOT NULL | Period start time |
| `period_end` | timestamptz | NOT NULL | Period end time |
| `metadata` | jsonb | default: {} | Additional metric data |
| `created_at` | timestamptz | default: now() | Creation timestamp |

**RLS Enabled:** Yes

#### `rate_limits`
Configurable rate limiting per user and provider.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | uuid | PRIMARY KEY | Rate limit identifier |
| `user_id` | uuid | FK to auth.users | User reference |
| `provider_id` | uuid | FK to ai_providers | Provider reference |
| `limit_type` | text | CHECK: requests_per_minute/hour/day, tokens_per_day, cost_per_day | Limit type |
| `limit_value` | integer | NOT NULL | Limit threshold |
| `current_usage` | integer | default: 0 | Current usage count |
| `reset_at` | timestamptz | NOT NULL | Usage reset time |
| `is_active` | boolean | default: true | Limit status |
| `created_at` | timestamptz | default: now() | Creation timestamp |
| `updated_at` | timestamptz | default: now() | Last update timestamp |

**RLS Enabled:** Yes

## Database Extensions

The following PostgreSQL extensions are installed and available:

### Core Extensions (Installed)
- **uuid-ossp** (1.1) - UUID generation functions
- **pgcrypto** (1.3) - Cryptographic functions for secure data handling
- **pg_stat_statements** (1.11) - Query performance monitoring
- **pg_graphql** (1.5.11) - GraphQL support for Supabase
- **supabase_vault** (0.3.1) - Secure secrets management
- **plpgsql** (1.0) - PostgreSQL procedural language

### Available Extensions (Not Installed)
- **postgis** (3.3.7) - Geospatial data support
- **vector** (0.8.0) - Vector embeddings support
- **pg_cron** (1.6) - Job scheduling
- **http** (1.6) - HTTP client functionality
- **pgjwt** (0.2.0) - JWT token handling
- And many others for specialized functionality

## Row Level Security (RLS)

RLS is enabled on all user-facing tables to ensure data isolation:

### Enabled Tables
- `user_profiles` - Users can only access their own profile
- `user_organizations` - Users see only their organization memberships
- `user_invitations` - Users see only relevant invitations
- `api_keys` - Organization-scoped access
- `personal_access_tokens` - User-scoped access
- `user_model_configurations` - User and organization scoped
- `org_model_enablement` - Organization-scoped access
- `chat_sessions` - User-scoped access
- `chat_messages` - Session-scoped access via user ownership
- `token_usage` - Inherited from message ownership
- `api_requests` - Organization-scoped access
- `usage_metrics` - User-scoped access
- `rate_limits` - User-scoped access

### Public Tables (No RLS)
- `ai_providers` - Public reference data
- `ai_models` - Public model catalog
- `model_pricing` - Public pricing information
- `provider_capabilities` - Public capability data

## Migration History

The database has been built through 52 migrations, with key milestones:

1. **Core Infrastructure** (Aug 23, 2025)
   - Initial table creation
   - API management setup
   - Observability tables
   - RLS policies

2. **Organization Management** (Aug 24, 2025)
   - Multi-tenant organization structure
   - User-organization relationships

3. **Enhanced AI Provider Support** (Sep 1, 2025)
   - Comprehensive AI provider schema
   - Model catalog and pricing
   - Provider capabilities

4. **Authentication & Access Control** (Sep 1, 2025)
   - Personal Access Tokens
   - User invitations system
   - Enhanced user profiles

5. **Simplified Architecture** (Sep 2, 2025)
   - Removed project-based complexity
   - Organization-centric API keys
   - Streamlined RLS policies

6. **Playground Features** (Sep 6, 2025)
   - User model configurations
   - Chat session management
   - Token usage tracking

7. **Enhanced Accounting & Provider Expansion** (Sep 6, 2025)
   - First-class accounting columns in api_requests
   - Added 5 new AI providers (Perplexity, xAI Grok, Qwen, Mistral, Cohere)
   - Organization-level model enablement controls

## Key Design Principles

### 1. Multi-Tenancy
- Organization-based data isolation
- RLS policies ensure secure data access
- Flexible user-organization relationships

### 2. Provider Abstraction
- Unified interface for multiple AI providers
- Extensible model catalog
- Provider-specific capabilities and pricing

### 3. Security First
- Encrypted API key storage
- PAT-based authentication
- Comprehensive RLS implementation
- Secure invitation system

### 4. Observability
- Complete request logging
- Token usage tracking
- Aggregated metrics
- Rate limiting support

### 5. Flexibility
- JSONB fields for extensible metadata
- Configurable model settings
- Pluggable provider system
- Temporal data with effective dates

## API Integration Patterns

### 1. Unified API Gateway
- Single endpoint for multiple providers
- Model prefix routing (openai/, anthropic/)
- PAT authentication for external apps

### 2. Playground Direct Access
- Simplified authentication for internal use
- Direct provider API calls for performance
- Session-based conversation management

### 3. Token Management
- Automatic PAT creation for new users
- Organization-scoped API keys
- Secure token validation and refresh

## Performance Considerations

### Indexes
- Primary keys on all tables (UUID)
- Foreign key constraints with automatic indexing
- Unique constraints on critical fields (tokens, emails)
- Analytics index on api_requests (organization_id, created_at DESC)

### Data Types
- UUIDs for all identifiers (better distribution)
- JSONB for flexible metadata (indexed queries)
- Timestamptz for all temporal data
- Numeric for precise pricing calculations

### Scalability
- Partitioning ready (time-based on logs/metrics)
- Connection pooling via Supabase
- Read replicas support
- Efficient RLS policies

## Future Enhancements

### Planned Features
1. **Advanced Analytics**
   - Cost optimization recommendations
   - Usage pattern analysis
   - Performance benchmarking

2. **Enhanced Security**
   - API key rotation
   - Advanced rate limiting
   - Audit logging

3. **Provider Expansion**
   - Additional AI providers
   - Custom model support
   - Fine-tuning integration

4. **Enterprise Features**
   - Advanced organization management
   - SSO integration
   - Compliance reporting

---

*This document was generated from live database schema on September 8, 2025. For the most current schema information, refer to the Supabase dashboard or run the schema extraction queries directly.*
