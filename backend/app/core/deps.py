from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.supabase_client import supabase, supabase_service
from app.utils.auth import get_user_from_token, get_user_by_id
from app.models.organization import Organization
from app.models.auth import CurrentCaller
from app.core.auth import require_pat
from app.core.supabase import get_supabase_service
from app.core.exceptions import InvalidRequestError, PermissionError_
from app.utils.model_id import parse_model_id
from app.services.model_catalog import get_provider_by_name, get_model_by_provider_and_name
from app.models.catalog import ResolvedModel
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class CurrentUser:
    def __init__(self, user_id: UUID, email: str, organizations: list = None, is_active: bool = True, jwt_token: str = None):
        self.user_id = user_id
        self.email = email
        self.organizations = organizations or []
        self._is_active = is_active
        self.jwt_token = jwt_token
    
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
    logger.info("Received authentication token")
    
    try:
        # Validate token with Supabase
        user_data = get_user_from_token(token)
        logger.info("Token validation successful")
        
        if not user_data:
            logger.error("No user data returned from token validation")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_uuid = UUID(user_data["id"])
        email = user_data["email"]
        
        # Load user organizations from user_organizations table
        try:
            # Get user profile for basic info
            profile_response = supabase_service.table("user_profiles").select("is_active").eq("id", str(user_uuid)).execute()
            is_active = True
            if profile_response.data:
                is_active = profile_response.data[0].get('is_active', True)
            
            # Get user organizations from user_organizations table
            org_response = supabase_service.table("user_organizations").select("""
                organization_id,
                role,
                is_active,
                is_owner,
                is_admin,
                joined_at,
                organizations!inner(
                    id,
                    name,
                    display_name
                )
            """).eq("user_id", str(user_uuid)).eq("is_active", True).execute()
            
            organizations = []
            if org_response.data:
                for org_membership in org_response.data:
                    org_data = org_membership['organizations']
                    organizations.append({
                        'id': org_data['id'],
                        'name': org_data['name'],
                        'display_name': org_data.get('display_name', ''),
                        'role': org_membership['role'],
                        'is_owner': org_membership.get('is_owner', False),
                        'is_admin': org_membership.get('is_admin', False),
                        'joined_at': org_membership.get('joined_at')
                    })
                    logger.info(f"Added organization to user: {organizations[-1]}")
            
            logger.info(f"Loaded {len(organizations)} organizations for user {user_uuid}: {organizations}")
            return CurrentUser(user_uuid, email, organizations, is_active, token)
            
        except Exception as org_error:
            logger.warning(f"Could not load organizations for user {user_uuid}: {org_error}")
            # Return user without organizations if loading fails
            return CurrentUser(user_uuid, email, [], True, token)
        
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
        from datetime import datetime
        org_data = {
            'id': UUID(first_org.get('id')),
            'name': first_org.get('name', ''),
            'display_name': first_org.get('display_name'),
            'domain': None,
            'external_id': None,
            'metadata': {},
            'settings': {},
            'is_active': True,
            'created_at': datetime.now(),  # Use current time as fallback
            'updated_at': datetime.now()   # Use current time as fallback
        }
        logger.info(f"Returning organization: {org_data}")
        return Organization(**org_data)
    
    logger.warning("No organization ID provided and user has no organizations")
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


async def resolve_organization(
    request: Request,
    caller: CurrentCaller = Depends(require_pat),
    x_org_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> UUID:
    """
    Resolve organization ID from X-Organization-ID header or PAT default.
    
    Validates that:
    1. Header is valid UUID (if provided)
    2. Organization exists and is active
    3. User has active membership in the organization
    
    Args:
        request: FastAPI request object
        caller: Current authenticated caller from PAT
        x_org_id: Optional organization ID from X-Organization-ID header
        
    Returns:
        UUID of the resolved organization
        
    Raises:
        InvalidRequestError: If X-Organization-ID is not a valid UUID
        PermissionError_: If user doesn't have access to the organization
    """
    sb = get_supabase_service()

    # 1) No header → fallback to PAT org
    if not x_org_id:
        request.state.organization_id = caller.organization_id
        logger.info(f"Organization resolved: {caller.organization_id} (from PAT default)")
        return caller.organization_id

    # 2) Validate UUID
    try:
        requested_org = UUID(x_org_id)
    except ValueError:
        raise InvalidRequestError("X-Organization-ID must be a valid UUID", param="X-Organization-ID")

    # 3) Check org exists and is_active (403 if not - don't leak existence)
    org_resp = sb.table("organizations")\
        .select("id,is_active")\
        .eq("id", str(requested_org))\
        .limit(1)\
        .execute()
    
    if not org_resp.data or not org_resp.data[0].get("is_active", True):
        # Don't reveal whether it exists or not
        raise PermissionError_("You do not have access to this organization")

    # 4) Check user has active membership (403 if not)
    membership_resp = sb.table("user_organizations")\
        .select("id,is_active,role,is_admin")\
        .eq("user_id", str(caller.user_id))\
        .eq("organization_id", str(requested_org))\
        .eq("is_active", True)\
        .limit(1)\
        .execute()
    
    if not membership_resp.data:
        raise PermissionError_("You do not have access to this organization")

    # 5) Store in request state and return
    request.state.organization_id = requested_org
    logger.info(f"Organization resolved: {requested_org} (from X-Organization-ID header)")
    return requested_org


async def validate_model(model_id: str) -> ResolvedModel:
    """
    Validate model against catalog and return resolved model information.
    
    Validates that:
    1. Model follows 'provider/model' format
    2. Provider exists and is active in ai_providers
    3. Model exists under that provider and is active in ai_models
    4. Model type is 'chat' or 'multimodal' (MVP constraint)
    
    Special case: When FORCE_ECHO_ADAPTER is enabled, bypass validation for echo models.
    
    Args:
        model_id: Model identifier in 'provider/model' format
        
    Returns:
        ResolvedModel with provider and model information
        
    Raises:
        InvalidRequestError: If model format is invalid
        NotFoundError: If provider or model not found
        PermissionError_: If provider or model is disabled
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    try:
        # 1) Parse and normalize provider/model
        provider_slug, native_model = parse_model_id(model_id)
    except ValueError as e:
        # Convert ValueError to proper OpenAI-compatible error
        raise InvalidRequestError(str(e), param="model")
    
    # Special case: FORCE_ECHO_ADAPTER bypasses catalog validation
    if settings.FORCE_ECHO_ADAPTER and provider_slug == "echo":
        from uuid import uuid4
        return ResolvedModel(
            id=uuid4(),
            provider_id=uuid4(),
            provider_name="echo",
            model_name=native_model,
            display_name=f"Echo {native_model}",
            model_type="chat",
            supports_streaming=False,
            supports_function_calling=False,
            supports_vision=False,
            supports_audio=False,
            max_tokens=1000,
            max_input_tokens=1000,
            is_active=True
        )
    
    # 2) Validate provider exists and is active
    provider = get_provider_by_name(provider_slug)
    
    # 3) Validate model exists under provider and is active
    model = get_model_by_provider_and_name(str(provider.id), native_model)
    model.provider_name = provider.name
    
    return model
