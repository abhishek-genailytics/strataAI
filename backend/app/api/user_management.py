from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import hashlib
import logging
from pydantic import BaseModel, EmailStr
from app.core.deps import get_current_user, CurrentUser
from app.models.user import User
from app.models.organization import Organization
from app.services.organization_service import OrganizationService
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class UserInvitationRequest(BaseModel):
    email: EmailStr
    role: str = "member"
    organization_id: Optional[str] = None

class UserInvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    invited_by: str
    created_at: datetime
    expires_at: datetime

class PersonalAccessTokenRequest(BaseModel):
    name: str
    scopes: List[str] = ["api:read", "api:write"]
    expires_at: Optional[datetime] = None

class PersonalAccessTokenResponse(BaseModel):
    id: str
    name: str
    token_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]

class PersonalAccessTokenCreateResponse(BaseModel):
    id: str
    name: str
    token: str  # Only returned once during creation
    token_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    role: str
    status: str
    created_at: datetime
    last_activity: Optional[datetime]

@router.post("/invite", response_model=UserInvitationResponse)
async def invite_user(
    invitation: UserInvitationRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Invite a user to the organization (admin only)"""
    supabase = get_supabase_client()
    
    # Get user's organization and role
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.user_id)
    
    if not user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of an organization to invite users"
        )
    
    # Use the first organization if not specified
    org_id = invitation.organization_id or user_orgs[0]["organization_id"]
    
    # Check if user is admin in the organization
    user_org = next((uo for uo in user_orgs if uo["organization_id"] == org_id), None)
    if not user_org or user_org["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can invite users to the organization"
        )
    
    # Check if user already exists in organization
    existing_user = await org_service.get_organization_user_by_email(org_id, invitation.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )
    
    # Generate invitation token
    invitation_token = f"inv_{secrets.token_urlsafe(24)}"
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Create invitation in database
    invitation_data = {
        "organization_id": org_id,
        "invited_by_user_id": current_user.user_id,
        "email": invitation.email,
        "role": invitation.role,
        "invitation_token": invitation_token,
        "expires_at": expires_at.isoformat()
    }
    
    result = supabase.table("user_invitations").insert(invitation_data).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )
    
    # TODO: Send invitation email via Supabase Auth or email service
    # For now, we'll just return the invitation data
    
    return UserInvitationResponse(
        id=result.data[0]["id"],
        email=invitation.email,
        role=invitation.role,
        status="pending",
        invited_by=current_user.email,
        created_at=datetime.fromisoformat(result.data[0]["created_at"]),
        expires_at=expires_at
    )

@router.get("/users", response_model=List[UserResponse])
async def get_organization_users(
    organization_id: Optional[str] = Query(None, description="Organization ID (optional)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all users in the organization or all users if admin"""
    supabase = get_supabase_client()
    
    # Get user's organization and role
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.user_id)
    
    # If user has organizations, use the first one or specified one
    if user_orgs:
        org_id = organization_id or user_orgs[0]["organization_id"]
        
        # Check if user is member of the organization
        user_org = next((uo for uo in user_orgs if uo["organization_id"] == org_id), None)
        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Get organization users
        users = await org_service.get_organization_users(org_id)
        
        return [
            UserResponse(
                id=user["id"],
                email=user["email"],
                display_name=user["display_name"],
                role=user["role"],
                status="active",
                created_at=user["joined_at"],
                last_activity=user["updated_at"]
            )
            for user in users
        ]
    else:
        # If user has no organization, show all users (for system admins)
        # This allows users without organizations to still see other users
        try:
            result = supabase.rpc("get_all_users_with_organizations").execute()
            
            if not result.data:
                return []
            
            return [
                UserResponse(
                    id=user["user_id"],
                    email=user["email"],
                    display_name=user["full_name"],
                    role=user["role"] or "no_org",
                    status="active",
                    created_at=user["created_at"],
                    last_activity=user["joined_at"] or user["created_at"]
                )
                for user in result.data
            ]
        except Exception as e:
            # If the function doesn't exist, return empty list
            return []

@router.post("/tokens", response_model=PersonalAccessTokenCreateResponse)
async def create_personal_access_token(
    token_request: PersonalAccessTokenRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new personal access token"""
    supabase = get_supabase_client()
    
    # Get user's organization
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.user_id)
    
    # Use the first organization if available, otherwise create token without organization
    org_id = user_orgs[0]["organization_id"] if user_orgs else None
    
    # Generate token
    token_value = f"pat_{secrets.token_urlsafe(32)}"
    token_prefix = f"{token_value[:8]}...{token_value[-4:]}"
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()
    
    # Create token in database
    token_data = {
        "user_id": current_user.user_id,
        "organization_id": org_id,
        "name": token_request.name,
        "token_hash": token_hash,
        "token_prefix": token_prefix,
        "scopes": token_request.scopes,
        "expires_at": token_request.expires_at.isoformat() if token_request.expires_at else None
    }
    
    result = supabase.table("personal_access_tokens").insert(token_data).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create token"
        )
    
    return PersonalAccessTokenCreateResponse(
        id=result.data[0]["id"],
        name=token_request.name,
        token=token_value,  # Only returned once
        token_prefix=token_prefix,
        scopes=token_request.scopes,
        created_at=datetime.fromisoformat(result.data[0]["created_at"]),
        expires_at=token_request.expires_at
    )

@router.get("/tokens", response_model=List[PersonalAccessTokenResponse])
async def get_personal_access_tokens(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all personal access tokens for the current user"""
    print("DEBUG: PAT endpoint called!")
    supabase = get_supabase_client()
    
    # Debug: Log the user ID being used
    print(f"Getting PATs for user ID: {current_user.user_id}")
    logger.info(f"Getting PATs for user ID: {current_user.user_id}")
    
    # Use RPC function to bypass RLS
    try:
        result = supabase.rpc(
            "get_user_personal_access_tokens",
            {"user_uuid": str(current_user.user_id)}
        ).execute()
        print(f"DEBUG: RPC result: {result.data}")
    except Exception as e:
        print(f"DEBUG: RPC failed: {e}, trying direct query...")
        # Fallback to direct table query
        result = supabase.table("personal_access_tokens").select("*").eq("user_id", current_user.user_id).execute()
    
    # Debug: Log the result
    print(f"PAT query result: {result.data}")
    logger.info(f"PAT query result: {result.data}")
    
    tokens = []
    for token in result.data:
        try:
            # Parse datetime fields, handling both ISO format and PostgreSQL format
            def parse_datetime(dt_str):
                if not dt_str:
                    return None
                try:
                    # Try ISO format first
                    return datetime.fromisoformat(dt_str)
                except ValueError:
                    try:
                        # Try PostgreSQL format (space instead of T)
                        return datetime.fromisoformat(dt_str.replace(' ', 'T'))
                    except ValueError:
                        # Fallback to simple parsing
                        logger.warning(f"Could not parse datetime: {dt_str}")
                        return datetime.utcnow()  # Fallback to current time
            
            tokens.append(PersonalAccessTokenResponse(
                id=token["id"],
                name=token["name"],
                token_prefix=token["token_prefix"],
                scopes=token["scopes"],
                created_at=parse_datetime(token["created_at"]),
                expires_at=parse_datetime(token["expires_at"]),
                last_used_at=parse_datetime(token["last_used_at"])
            ))
        except Exception as e:
            logger.error(f"Error parsing token {token['id']}: {e}")
            # Skip this token if there's an error
            continue
    
    return tokens

@router.delete("/tokens/{token_id}")
async def delete_personal_access_token(
    token_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a personal access token"""
    supabase = get_supabase_client()
    
    # Check if token belongs to user
    result = supabase.table("personal_access_tokens").select("id").eq("id", token_id).eq("user_id", current_user.user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Delete token
    supabase.table("personal_access_tokens").delete().eq("id", token_id).execute()
    
    return {"message": "Token deleted successfully"}

@router.delete("/users/{user_id}")
async def remove_organization_user(
    user_id: str,
    organization_id: Optional[str] = Query(None, description="Organization ID (optional)"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove a user from the organization (admin only)"""
    supabase = get_supabase_client()
    
    # Get user's organization and role
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.user_id)
    
    if not user_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of an organization to remove users"
        )
    
    # Use the first organization if not specified
    org_id = organization_id or user_orgs[0]["organization_id"]
    
    # Check if user is admin in the organization
    user_org = next((uo for uo in user_orgs if uo["organization_id"] == org_id), None)
    if not user_org or user_org["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can remove users from the organization"
        )
    
    # Check if trying to remove self
    if user_id == str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the organization"
        )
    
    # Remove user from organization
    result = supabase.table("user_organizations").delete().eq("user_id", user_id).eq("organization_id", org_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in organization"
        )
    
    return {"message": "User removed from organization successfully"}
