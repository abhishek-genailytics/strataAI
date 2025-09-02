from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.supabase_client import supabase
from app.utils.auth import get_user_from_token, get_user_by_id
from app.models.organization import Organization
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class CurrentUser:
    def __init__(self, user_id: UUID, email: str, organizations: list = None):
        self.user_id = user_id
        self.email = email
        self.organizations = organizations or []
    
    @property
    def id(self) -> UUID:
        """Alias for user_id to maintain compatibility."""
        return self.user_id

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials containing JWT token
        
    Returns:
        CurrentUser object with user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Validate token with Supabase
        user_data = get_user_from_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_uuid = UUID(user_data["id"])
        email = user_data["email"]
        
        # Don't load organizations during authentication to avoid circular imports
        # Organizations will be loaded separately when needed
        
        return CurrentUser(user_uuid, email, [])
        
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """
    Get current authenticated user if token is provided, otherwise return None.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        CurrentUser object or None if no valid token
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Get current active user (not disabled)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_organization_context(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
) -> Optional[Organization]:
    """Get organization context from request headers or query params."""
    # Try to get organization ID from X-Organization-ID header
    org_id_str = request.headers.get("X-Organization-ID")
    
    # If not in headers, try query parameter
    if not org_id_str:
        org_id_str = request.query_params.get("organization_id")
    
    if not org_id_str:
        # Return first organization if user has any
        if current_user.organizations:
            return current_user.organizations[0]
        return None
    
    try:
        org_id = UUID(org_id_str)
        org_with_role = current_user.get_organization_by_id(org_id)
        if org_with_role:
            return Organization(**org_with_role.dict())
        return None
    except ValueError:
        return None


def require_organization_role(required_roles: List[str]):
    """Dependency factory to require specific roles in organization context."""
    async def _require_role(
        organization: Organization = Depends(get_organization_context),
        current_user: CurrentUser = Depends(get_current_user)
    ) -> Organization:
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization context required"
            )
        
        if not current_user.has_role_in_organization(organization.id, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}"
            )
        
        return organization
    
    return _require_role


# Common role requirements
require_admin_role = require_organization_role(["admin", "owner"])
require_member_role = require_organization_role(["member", "admin", "owner"])
