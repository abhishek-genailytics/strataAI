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
    def __init__(self, user_id: UUID, email: str, organizations: list = None, is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.organizations = organizations or []
        self._is_active = is_active
    
    @property
    def id(self) -> UUID:
        """Alias for user_id to maintain compatibility."""
        return self.user_id
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self._is_active
    
    def get_organization_by_id(self, org_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get organization by ID from user's organizations.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Organization dict with role information or None if not found
        """
        for org in self.organizations:
            if org.get('id') == str(org_id):
                return org
        return None
    
    def has_role_in_organization(self, org_id: UUID, required_roles: List[str]) -> bool:
        """
        Check if user has any of the required roles in the organization.
        
        Args:
            org_id: Organization UUID
            required_roles: List of required roles
            
        Returns:
            True if user has any of the required roles, False otherwise
        """
        org = self.get_organization_by_id(org_id)
        if not org:
            return False
        
        user_role = org.get('role', '').lower()
        return user_role in [role.lower() for role in required_roles]

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
    logger.info(f"Received token: {token[:20]}...")
    
    try:
        # Validate token with Supabase
        user_data = get_user_from_token(token)
        logger.info(f"User data from token: {user_data}")
        
        if not user_data:
            logger.error("No user data returned from token validation")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_uuid = UUID(user_data["id"])
        email = user_data["email"]
        
        # Load user profile with organizations using direct queries
        try:
            # Get user profile
            profile_response = supabase.table("user_profiles").select("*").eq("id", str(user_uuid)).execute()
            
            # Get user organizations
            orgs_response = supabase.table("user_organizations").select(
                "organization_id, role, joined_at, organizations(name, display_name)"
            ).eq("user_id", str(user_uuid)).eq("is_active", True).execute()
            
            organizations = []
            is_active = True
            
            if profile_response.data:
                user_profile = profile_response.data[0]
                is_active = user_profile.get('is_active', True)
                logger.info(f"Loaded user profile: {user_profile}")
            else:
                logger.warning(f"No user profile data found for user {user_uuid}")
            
            if orgs_response.data:
                logger.info(f"Raw organizations response: {orgs_response.data}")
                for org_data in orgs_response.data:
                    org_info = org_data.get('organizations', {})
                    logger.info(f"Processing org_data: {org_data}, org_info: {org_info}")
                    if org_info:
                        organizations.append({
                            'id': org_data['organization_id'],
                            'name': org_info.get('name', ''),
                            'display_name': org_info.get('display_name', ''),
                            'role': org_data.get('role', 'member'),
                            'joined_at': org_data.get('joined_at')
                        })
                logger.info(f"Loaded {len(organizations)} organizations: {organizations}")
            else:
                logger.warning(f"No organizations found for user {user_uuid}")
                logger.warning(f"Organizations response: {orgs_response}")
            
            return CurrentUser(user_uuid, email, organizations, is_active)
            
        except Exception as org_error:
            logger.warning(f"Could not load organizations for user {user_uuid}: {org_error}")
            # Return user without organizations if loading fails
            return CurrentUser(user_uuid, email, [], True)
        
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
    logger.info(f"Getting organization context for user {current_user.user_id}")
    logger.info(f"User organizations: {current_user.organizations}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request query params: {dict(request.query_params)}")
    
    # Always try to return the first organization if user has any
    if current_user.organizations:
        first_org = current_user.organizations[0]
        logger.info(f"Using first organization: {first_org}")
        # Create Organization object from the first organization data
        org_data = {
            'id': UUID(first_org.get('id')),
            'name': first_org.get('name', ''),
            'display_name': first_org.get('display_name'),
            'domain': None,
            'external_id': None,
            'metadata': {},
            'settings': {},
            'is_active': True,
            'created_at': first_org.get('joined_at'),  # Use joined_at as created_at
            'updated_at': first_org.get('joined_at')   # Use joined_at as updated_at
        }
        logger.info(f"Returning organization: {org_data}")
        return Organization(**org_data)
    
    # Try to get organization ID from X-Organization-ID header
    org_id_str = request.headers.get("X-Organization-ID")
    logger.info(f"Organization ID from header: {org_id_str}")
    
    # If not in headers, try query parameter
    if not org_id_str:
        org_id_str = request.query_params.get("organization_id")
        logger.info(f"Organization ID from query: {org_id_str}")
    
    if not org_id_str:
        logger.warning("No organization ID provided and user has no organizations")
        return None
    
    try:
        org_id = UUID(org_id_str)
        org_with_role = current_user.get_organization_by_id(org_id)
        if org_with_role:
            # Create Organization object from the organization data
            # The org_with_role contains: id, name, display_name, role, joined_at
            org_data = {
                'id': org_id,
                'name': org_with_role.get('name', ''),
                'display_name': org_with_role.get('display_name'),
                'domain': None,
                'external_id': None,
                'metadata': {},
                'settings': {},
                'is_active': True,
                'created_at': org_with_role.get('joined_at'),  # Use joined_at as created_at
                'updated_at': org_with_role.get('joined_at')   # Use joined_at as updated_at
            }
            return Organization(**org_data)
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
