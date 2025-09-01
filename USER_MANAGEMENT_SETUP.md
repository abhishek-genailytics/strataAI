# User Management System Setup

This document describes the user management system for StrataAI, which includes user roles (admin/member), Personal Access Tokens (PATs), and user invitations.

## Overview

The user management system provides:

1. **Role-based Access Control**: Users can be either `admin` or `member`
2. **Personal Access Tokens**: Users can create multiple PATs for API access
3. **User Invitations**: Admins can invite new users to the organization
4. **Supabase Auth Integration**: Seamless authentication and user management

## Database Schema

### Tables Created

#### 1. `personal_access_tokens`

Stores user-created API tokens with the following fields:

- `id`: Unique identifier
- `user_id`: Reference to auth.users
- `organization_id`: Reference to organizations
- `name`: Token name (user-defined)
- `token_hash`: Hashed token value (for security)
- `token_prefix`: Display prefix (e.g., "pat_abc123...xyz789")
- `scopes`: JSON array of permissions
- `expires_at`: Optional expiration date
- `last_used_at`: Last usage timestamp
- `is_active`: Whether the token is active

#### 2. `user_invitations`

Stores pending user invitations:

- `id`: Unique identifier
- `organization_id`: Reference to organizations
- `invited_by_user_id`: Reference to auth.users (who sent the invitation)
- `email`: Email address of the invited user
- `role`: Role to assign (admin/member)
- `invitation_token`: Secure token for invitation link
- `status`: Invitation status (pending/accepted/expired/cancelled)
- `expires_at`: Invitation expiration date
- `accepted_at`: When the invitation was accepted
- `accepted_by_user_id`: Reference to auth.users (who accepted)

### Updated Tables

#### `user_organizations`

- Added role constraint: `role IN ('admin', 'member')`
- Updated existing roles to lowercase

## API Endpoints

### User Management (`/api/user-management/`)

#### POST `/invite`

Invite a new user to the organization (admin only)

```json
{
  "email": "user@example.com",
  "role": "member",
  "organization_id": "optional-org-id"
}
```

#### GET `/users`

Get all users in the organization

```json
[
  {
    "id": "user-id",
    "email": "user@example.com",
    "display_name": "User Name",
    "role": "admin",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T00:00:00Z"
  }
]
```

#### DELETE `/users/{user_id}`

Remove a user from the organization (admin only)

### Personal Access Tokens (`/api/user-management/`)

#### POST `/tokens`

Create a new personal access token

```json
{
  "name": "my-api-token",
  "scopes": ["api:read", "api:write"],
  "expires_at": "2025-01-01T00:00:00Z"
}
```

#### GET `/tokens`

Get all personal access tokens for the current user

```json
[
  {
    "id": "token-id",
    "name": "my-api-token",
    "token_prefix": "pat_abc123...xyz789",
    "scopes": ["api:read", "api:write"],
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": "2024-01-01T00:00:00Z"
  }
]
```

#### DELETE `/tokens/{token_id}`

Delete a personal access token

### Organizations (`/api/organizations/`)

#### POST `/`

Create a new organization

```json
{
  "name": "my-org",
  "display_name": "My Organization",
  "domain": "mycompany.com"
}
```

#### GET `/`

Get all organizations the user belongs to

#### GET `/{org_id}`

Get a specific organization by ID

## Frontend Integration

### Components Updated

1. **Access.tsx**: Main access management page with tabs for Users and Personal Access Tokens
2. **userManagementService.ts**: Service for API communication
3. **OrganizationContext.tsx**: Shows user role in the current organization

### Features

#### User Management Tab

- View all users in the organization
- Invite new users (admin only)
- Remove users (admin only)
- Search and filter users
- Role-based UI (only admins see invite/remove buttons)

#### Personal Access Tokens Tab

- View all user's PATs
- Create new PATs
- Delete PATs
- Copy token to clipboard (only shown once during creation)
- Search and filter tokens

### Key Features

1. **Role-based Permissions**: Only admins can invite/remove users
2. **Secure Token Generation**: Tokens are hashed and only shown once
3. **Real-time Updates**: UI updates after API operations
4. **Error Handling**: Comprehensive error messages and toast notifications
5. **Responsive Design**: Works on all screen sizes

## Security Features

### Row Level Security (RLS)

All tables have RLS policies that ensure:

- Users can only see their own tokens
- Users can only see users in their organization
- Only admins can manage user invitations
- Only admins can remove users

### Token Security

- Tokens are hashed using SHA-256
- Only token prefixes are stored in the database
- Full tokens are only returned once during creation
- Tokens can have expiration dates
- Tokens can have specific scopes

### Invitation Security

- Invitation tokens are cryptographically secure
- Invitations expire after 7 days
- Invitation status is tracked
- Only admins can create invitations

## Setup Instructions

### 1. Database Setup

The database tables and functions have been created via Supabase migrations. No additional setup is required.

### 2. Backend Setup

The backend API endpoints are ready to use. Make sure your backend server is running:

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Frontend Setup

The frontend components are ready to use. Start your frontend:

```bash
cd frontend
npm start
```

### 4. Testing

Run the test script to verify everything works:

```bash
python test_user_management.py
```

## Usage Flow

### For Admins

1. **Invite Users**:

   - Navigate to Access Management → Users tab
   - Click "Invite User"
   - Enter email and select role
   - Invitation is sent (email integration needed)

2. **Manage Users**:

   - View all users in the organization
   - Remove users if needed
   - See user roles and activity

3. **Create PATs**:
   - Navigate to Access Management → Personal Access Tokens tab
   - Click "New Personal Access Token"
   - Enter name and optional expiration
   - Copy the token (shown only once)

### For Members

1. **View Organization**:

   - See other members in the organization
   - View their own role and permissions

2. **Manage PATs**:
   - Create multiple personal access tokens
   - Delete tokens when no longer needed
   - View token usage and expiration

## Integration with Supabase Auth

The system integrates with Supabase Auth for:

- User authentication
- User profile management
- Session management
- Email verification

### Next Steps for Full Integration

1. **Email Integration**: Set up email service for user invitations
2. **Supabase Auth Hooks**: Implement auth state management
3. **Email Templates**: Create professional invitation emails
4. **Audit Logging**: Track user management actions
5. **Advanced Permissions**: Add more granular role permissions

## Troubleshooting

### Common Issues

1. **"User already belongs to an organization"**: Users can only belong to one organization at a time
2. **"Only admins can invite users"**: Check user role in the organization
3. **"Token not found"**: Token may have been deleted or expired
4. **"Organization not found"**: User may not have access to the organization

### Debug Steps

1. Check browser console for API errors
2. Verify user authentication status
3. Check user role in the organization
4. Verify database connections
5. Check RLS policies

## API Documentation

For detailed API documentation, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Check the browser console for errors
4. Verify database permissions and RLS policies
