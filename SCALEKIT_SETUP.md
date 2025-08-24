# ScaleKit Integration Setup Guide

This document provides comprehensive instructions for setting up ScaleKit multi-tenant authentication with the StrataAI platform.

## Overview

ScaleKit provides enterprise-grade SSO (Single Sign-On) and multi-tenant authentication capabilities. This integration allows organizations to:

- Use their existing identity providers (Google Workspace, Microsoft 365, Okta, etc.)
- Manage users and permissions at the organization level
- Provide seamless SSO experience for enterprise customers
- Maintain data isolation between organizations

## Prerequisites

1. **ScaleKit Account**: Sign up at [scalekit.com](https://scalekit.com)
2. **Domain Verification**: Verify ownership of your application domain
3. **SSL Certificate**: Ensure your application runs over HTTPS
4. **Database Access**: Admin access to your Supabase/PostgreSQL database

## ScaleKit Dashboard Configuration

### 1. Create a New Application

1. Log into your ScaleKit dashboard
2. Navigate to **Applications** → **Create Application**
3. Fill in the application details:
   - **Application Name**: StrataAI
   - **Application Type**: Web Application
   - **Description**: Unified AI API Gateway Platform

### 2. Configure OAuth Settings

#### Redirect URIs
Add the following redirect URIs for your environments:

**Production:**
```
https://your-domain.com/auth/callback
```

**Development:**
```
http://localhost:3000/auth/callback
```

#### Allowed Origins
Configure CORS origins:

**Production:**
```
https://your-domain.com
```

**Development:**
```
http://localhost:3000
```

### 3. Obtain Credentials

After creating the application, note down:
- **Client ID**: Used for API authentication
- **Client Secret**: Keep this secure and never expose in frontend
- **Environment URL**: ScaleKit environment endpoint

### 4. Configure Scopes

Enable the following OAuth scopes:
- `openid` - Required for OpenID Connect
- `profile` - Access to user profile information
- `email` - Access to user email address
- `organizations` - Access to user's organizations

### 5. Organization Setup

#### Create Organizations
For each customer organization:

1. Go to **Organizations** → **Create Organization**
2. Fill in organization details:
   - **Organization Name**: Customer's company name
   - **Display Name**: Friendly display name
   - **Domain**: Customer's email domain (e.g., acme.com)

#### Configure Identity Providers
For each organization, set up their identity provider:

1. Select the organization
2. Go to **Connections** → **Add Connection**
3. Choose the appropriate provider:
   - **Google Workspace**
   - **Microsoft 365**
   - **Okta**
   - **SAML 2.0**
   - **OIDC**

#### Example: Google Workspace Setup
1. Select **Google Workspace**
2. Enter the customer's Google Workspace domain
3. Configure the following settings:
   - **Domain**: customer-domain.com
   - **Auto-assign users**: Enable if you want automatic user provisioning
   - **Default role**: Set default role for new users (member/admin)

## Environment Configuration

### Backend Environment Variables

Add the following to your `.env` file:

```bash
# ScaleKit Configuration
SCALEKIT_ENVIRONMENT_URL=https://your-environment.scalekit.com
SCALEKIT_CLIENT_ID=your_client_id_here
SCALEKIT_CLIENT_SECRET=your_client_secret_here

# Optional: ScaleKit API Configuration
SCALEKIT_API_TIMEOUT=30
SCALEKIT_RETRY_ATTEMPTS=3
```

### Frontend Environment Variables

Add to your frontend `.env` file:

```bash
# ScaleKit Public Configuration
REACT_APP_SCALEKIT_CLIENT_ID=your_client_id_here
REACT_APP_SCALEKIT_ENVIRONMENT_URL=https://your-environment.scalekit.com
```

## Database Migration

Run the organization migration to create required tables:

```bash
# Backend directory
cd backend
python -m alembic upgrade head
```

Or manually run the SQL migration:

```sql
-- Run the contents of backend/migrations/20241224_add_organizations.sql
```

## Testing the Integration

### 1. Test SSO Flow

1. Start your application
2. Navigate to the organization selector
3. Click "Join Organization" or "Join Another Organization"
4. You should be redirected to ScaleKit's authorization page
5. Complete the SSO flow with a test user
6. Verify you're redirected back with proper authentication

### 2. Test Organization Context

1. After SSO login, verify the organization selector shows your organization
2. Switch between "Personal" and organization workspaces
3. Verify API calls include the correct organization context headers
4. Test that data is properly isolated between contexts

### 3. Test API Key Management

1. Create API keys in both personal and organization contexts
2. Verify keys are scoped to the correct context
3. Test that organization members can only see organization keys
4. Verify admin vs member permissions work correctly

## Security Considerations

### 1. Client Secret Protection

- **Never** expose the client secret in frontend code
- Store client secret in secure environment variables
- Use different credentials for development and production
- Rotate secrets regularly

### 2. Token Validation

- Always validate ScaleKit tokens on the backend
- Implement proper token expiration handling
- Use HTTPS for all ScaleKit communication
- Validate organization membership for protected resources

### 3. Data Isolation

- Ensure all API endpoints respect organization context
- Validate user permissions for organization operations
- Implement proper access controls for admin operations
- Audit organization membership changes

## Troubleshooting

### Common Issues

#### 1. Redirect URI Mismatch
**Error**: `redirect_uri_mismatch`
**Solution**: Ensure the redirect URI in your request exactly matches what's configured in ScaleKit dashboard

#### 2. Invalid Client Credentials
**Error**: `invalid_client`
**Solution**: Verify your client ID and secret are correct and properly configured

#### 3. Organization Not Found
**Error**: `organization_not_found`
**Solution**: Ensure the organization exists in ScaleKit and the user has access

#### 4. Token Validation Failed
**Error**: `invalid_token`
**Solution**: Check token expiration and ensure proper token validation

### Debug Mode

Enable debug logging in development:

```bash
# Backend
SCALEKIT_DEBUG=true
LOG_LEVEL=DEBUG

# Frontend
REACT_APP_DEBUG=true
```

### Testing with Curl

Test the SSO endpoints directly:

```bash
# Get authorization URL
curl -X GET "http://localhost:8000/organizations/sso/login?redirect_uri=http://localhost:3000/auth/callback" \
  -H "Authorization: Bearer your_jwt_token"

# Handle callback (replace with actual code)
curl -X POST "http://localhost:8000/organizations/sso/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "authorization_code_from_scalekit",
    "redirect_uri": "http://localhost:3000/auth/callback"
  }'
```

## Production Deployment

### 1. Environment Setup

- Use production ScaleKit environment
- Configure production redirect URIs
- Set up proper SSL certificates
- Use secure environment variable management

### 2. Monitoring

- Monitor SSO success/failure rates
- Track organization membership changes
- Set up alerts for authentication failures
- Monitor API usage by organization

### 3. Backup and Recovery

- Backup organization configuration
- Document identity provider settings
- Maintain emergency access procedures
- Test disaster recovery procedures

## Support and Resources

- **ScaleKit Documentation**: [docs.scalekit.com](https://docs.scalekit.com)
- **ScaleKit Support**: support@scalekit.com
- **Community Forum**: [community.scalekit.com](https://community.scalekit.com)
- **Status Page**: [status.scalekit.com](https://status.scalekit.com)

## Integration Checklist

- [ ] ScaleKit application created and configured
- [ ] OAuth redirect URIs configured
- [ ] Client credentials obtained and secured
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Organizations created in ScaleKit dashboard
- [ ] Identity providers configured for organizations
- [ ] SSO flow tested end-to-end
- [ ] Organization context switching tested
- [ ] API key management tested in multi-tenant context
- [ ] Security review completed
- [ ] Production deployment configured
- [ ] Monitoring and alerting set up
- [ ] Documentation updated for team

## Next Steps

After completing the ScaleKit integration:

1. **User Training**: Train your team on managing organizations and SSO
2. **Customer Onboarding**: Create documentation for customers setting up SSO
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Optimization**: Monitor performance and optimize as needed
5. **Scaling**: Plan for scaling as you add more organizations

For additional support or questions about this integration, please refer to the ScaleKit documentation or contact their support team.
