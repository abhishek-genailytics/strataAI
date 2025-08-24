from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse

from ..core.deps import (
    get_current_user, 
    get_organization_context,
    require_admin_role,
    require_member_role,
    CurrentUser
)
from ..models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationWithRole, OrganizationMember, OrganizationInvite,
    OrganizationStats, ScaleKitAuthResult
)
from ..services.organization_service import organization_service
from ..services.scalekit_service import scalekit_service

router = APIRouter()

@router.get("/", response_model=List[OrganizationWithRole])
async def get_user_organizations(
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all organizations for the current user"""
    return current_user.organizations

@router.post("/", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new organization"""
    try:
        # Create organization in ScaleKit first
        scalekit_org = scalekit_service.create_organization(
            name=org_data.name,
            display_name=org_data.display_name,
            domain=org_data.domain,
            external_id=org_data.external_id
        )
        
        # Update org_data with ScaleKit organization ID
        org_data.scalekit_organization_id = scalekit_org["id"]
        
        # Create organization in database
        organization = await organization_service.create_organization(
            org_data=org_data,
            creator_user_id=current_user.id
        )
        
        return organization
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create organization: {str(e)}"
        )

@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get organization details"""
    # Check if user belongs to organization
    org_with_role = current_user.get_organization_by_id(organization_id)
    if not org_with_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    organization = await organization_service.get_organization(organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization

@router.put("/{organization_id}", response_model=Organization)
async def update_organization(
    organization_id: UUID,
    org_data: OrganizationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Update organization (admin only)"""
    try:
        # Update in ScaleKit if needed
        if any([org_data.name, org_data.display_name, org_data.domain]):
            scalekit_service.update_organization(
                organization_id=organization.scalekit_organization_id,
                name=org_data.name,
                display_name=org_data.display_name,
                domain=org_data.domain
            )
        
        # Update in database
        updated_org = await organization_service.update_organization(
            organization_id=organization_id,
            org_data=org_data
        )
        
        if not updated_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return updated_org
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update organization: {str(e)}"
        )

@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Delete organization (admin only)"""
    success = await organization_service.delete_organization(organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return {"message": "Organization deleted successfully"}

@router.get("/{organization_id}/members", response_model=List[OrganizationMember])
async def get_organization_members(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_member_role)
):
    """Get organization members"""
    members = await organization_service.get_organization_members(organization_id)
    return members

@router.post("/{organization_id}/members")
async def add_organization_member(
    organization_id: UUID,
    user_id: UUID,
    role: str = "member",
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Add member to organization (admin only)"""
    member = await organization_service.add_user_to_organization(
        user_id=user_id,
        organization_id=organization_id,
        role=role
    )
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member to organization"
        )
    
    return {"message": "Member added successfully"}

@router.put("/{organization_id}/members/{user_id}")
async def update_member_role(
    organization_id: UUID,
    user_id: UUID,
    role: str,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Update member role (admin only)"""
    member = await organization_service.update_user_organization_role(
        user_id=user_id,
        organization_id=organization_id,
        role=role
    )
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return {"message": "Member role updated successfully"}

@router.delete("/{organization_id}/members/{user_id}")
async def remove_organization_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Remove member from organization (admin only)"""
    success = await organization_service.remove_user_from_organization(
        user_id=user_id,
        organization_id=organization_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    return {"message": "Member removed successfully"}

@router.get("/{organization_id}/stats", response_model=OrganizationStats)
async def get_organization_stats(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_member_role)
):
    """Get organization statistics"""
    stats = await organization_service.get_organization_stats(organization_id)
    return stats

@router.post("/{organization_id}/sync")
async def sync_with_scalekit(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Sync organization with ScaleKit (admin only)"""
    success = await organization_service.sync_with_scalekit(organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sync with ScaleKit"
        )
    
    return {"message": "Organization synced successfully"}

@router.get("/{organization_id}/admin-portal")
async def get_admin_portal_link(
    organization_id: UUID,
    features: Optional[List[str]] = None,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(require_admin_role)
):
    """Generate admin portal link for organization (admin only)"""
    try:
        portal_link = scalekit_service.generate_admin_portal_link(
            organization_id=organization.scalekit_organization_id,
            features=features or ['sso', 'dir_sync']
        )
        
        return {"portal_url": portal_link}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate admin portal link: {str(e)}"
        )

# ScaleKit SSO endpoints
@router.get("/sso/login")
async def sso_login(
    request: Request,
    organization_id: Optional[str] = None,
    connection_id: Optional[str] = None,
    login_hint: Optional[str] = None
):
    """Initiate SSO login flow"""
    try:
        # Get redirect URI from request
        redirect_uri = str(request.url_for("sso_callback"))
        
        # Generate authorization URL
        auth_url = scalekit_service.get_authorization_url(
            redirect_uri=redirect_uri,
            state="sso_login",
            organization_id=organization_id,
            connection_id=connection_id,
            login_hint=login_hint
        )
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initiate SSO login: {str(e)}"
        )

@router.get("/sso/callback")
async def sso_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """Handle SSO callback"""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSO error: {error} - {error_description}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Get redirect URI
        redirect_uri = str(request.url_for("sso_callback"))
        
        # Exchange code for user profile and tokens
        auth_result = scalekit_service.authenticate_with_code(
            code=code,
            redirect_uri=redirect_uri
        )
        
        # Return auth result (frontend should handle token storage)
        return auth_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSO authentication failed: {str(e)}"
        )
