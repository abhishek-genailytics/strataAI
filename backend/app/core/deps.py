from typing import Generator, Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from supabase import Client

from .config import settings
from .database import get_supabase_client
from ..models.organization import Organization, OrganizationWithRole
from ..services.scalekit_service import scalekit_service
from ..services.organization_service import organization_service


security = HTTPBearer()


class CurrentUser:
    """Current authenticated user with organization context"""
    def __init__(self, user_id: UUID, email: str, organizations: List[OrganizationWithRole]):
        self.id = user_id
        self.email = email
        self.organizations = organizations
        self.is_active = True

    def get_organization_by_id(self, org_id: UUID) -> Optional[OrganizationWithRole]:
        """Get organization by ID if user belongs to it"""
        return next((org for org in self.organizations if org.id == org_id), None)

    def has_role_in_organization(self, org_id: UUID, required_roles: List[str]) -> bool:
        """Check if user has required role in organization"""
        org = self.get_organization_by_id(org_id)
        return org is not None and org.user_role in required_roles


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """Get current authenticated user from JWT token (Supabase or ScaleKit)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    supabase = get_supabase_client()
    
    try:
        # First try to validate as Supabase JWT token
        try:
            # Use Supabase client to validate the token directly
            user_response = supabase.auth.get_user(token)
            if user_response.user:
                user_id = user_response.user.id
                email = user_response.user.email
                
                if user_id and email:
                    user_uuid = UUID(user_id)
                    # Get user's organizations
                    organizations = await organization_service.get_user_organizations(user_uuid)
                    return CurrentUser(user_uuid, email, organizations)
                
        except Exception:
            # Fallback to JWT decode
            try:
                payload = jwt.decode(
                    token, 
                    settings.SUPABASE_JWT_SECRET, 
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                user_id = payload.get("sub")
                email = payload.get("email")
                
                if user_id and email:
                    user_uuid = UUID(user_id)
                    # Get user's organizations
                    organizations = await organization_service.get_user_organizations(user_uuid)
                    return CurrentUser(user_uuid, email, organizations)
                    
            except (JWTError, ValueError):
                pass
        
        # Try ScaleKit token validation
        try:
            if scalekit_service.validate_token(token):
                user_profile = scalekit_service.get_user_profile(token)
                
                # Find or create user in Supabase
                user_result = supabase.auth.get_user(token)
                if user_result.user:
                    user_uuid = UUID(user_result.user.id)
                    email = user_result.user.email
                    
                    # Get or create organization
                    org = await organization_service.get_organization_by_scalekit_id(
                        user_profile.organization_id
                    )
                    
                    if not org:
                        # Create organization if it doesn't exist
                        from ..models.organization import OrganizationCreate
                        org_data = OrganizationCreate(
                            scalekit_organization_id=user_profile.organization_id,
                            name=user_profile.organization_id,
                            display_name=user_profile.organization_id
                        )
                        org = await organization_service.create_organization(org_data, user_uuid)
                    
                    # Ensure user is member of organization
                    if not await organization_service.user_belongs_to_organization(user_uuid, org.id):
                        await organization_service.add_user_to_organization(
                            user_id=user_uuid,
                            organization_id=org.id,
                            role="member",
                            scalekit_user_id=user_profile.id
                        )
                    
                    # Get user's organizations
                    organizations = await organization_service.get_user_organizations(user_uuid)
                    return CurrentUser(user_uuid, email, organizations)
                    
        except Exception:
            pass
            
    except Exception:
        pass
    
    raise credentials_exception


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


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[CurrentUser]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


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
