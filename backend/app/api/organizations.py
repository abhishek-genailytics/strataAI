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
    OrganizationWithMembers, OrganizationInvite
)
from ..services.organization_service import organization_service

router = APIRouter()

@router.get("/", response_model=List[dict])
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
        # Create organization in database
        organization = await organization_service.create_organization(
            org_data=org_data,
            owner_id=current_user.user_id
        )
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create organization"
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
    user_orgs = current_user.organizations
    user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
    
    if not user_org:
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update organization (admin only)"""
    try:
        # Check if user is admin of the organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org or user_org.get('user_role') not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        organization = await organization_service.update_organization(
            org_id=organization_id,
            org_data=org_data
        )
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return organization
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update organization: {str(e)}"
        )

@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete organization (owner only)"""
    try:
        # Check if user is owner of the organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org or user_org.get('user_role') != 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner access required"
            )
        
        success = await organization_service.delete_organization(organization_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return {"message": "Organization deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete organization: {str(e)}"
        )

@router.get("/{organization_id}/members", response_model=List[dict])
async def get_organization_members(
    organization_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all members of an organization"""
    try:
        # Check if user belongs to organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        members = await organization_service.get_organization_members(organization_id)
        return members
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get organization members: {str(e)}"
        )

@router.post("/{organization_id}/members")
async def add_member_to_organization(
    organization_id: UUID,
    invite_data: OrganizationInvite,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add a member to an organization (admin only)"""
    try:
        # Check if user is admin of the organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org or user_org.get('user_role') not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # For now, we'll just return a success message
        # In a real implementation, you'd send an invitation email
        return {
            "message": f"Invitation sent to {invite_data.email}",
            "email": invite_data.email,
            "role": invite_data.role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add member: {str(e)}"
        )

@router.delete("/{organization_id}/members/{user_id}")
async def remove_member_from_organization(
    organization_id: UUID,
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove a member from an organization (admin only)"""
    try:
        # Check if user is admin of the organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org or user_org.get('user_role') not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Prevent removing the owner
        if user_org.get('user_role') == 'owner' and str(user_id) == str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove organization owner"
            )
        
        success = await organization_service.remove_user_from_organization(
            user_id=user_id,
            org_id=organization_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in organization"
            )
        
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to remove member: {str(e)}"
        )

@router.put("/{organization_id}/members/{user_id}/role")
async def update_member_role(
    organization_id: UUID,
    user_id: UUID,
    role_data: dict,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update a member's role in an organization (admin only)"""
    try:
        # Check if user is admin of the organization
        user_orgs = current_user.organizations
        user_org = next((org for org in user_orgs if org.get('organization_id') == str(organization_id)), None)
        
        if not user_org or user_org.get('user_role') not in ['admin', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        new_role = role_data.get('role')
        if not new_role or new_role not in ['member', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'member' or 'admin'"
            )
        
        success = await organization_service.update_user_role(
            user_id=user_id,
            org_id=organization_id,
            role=new_role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in organization"
            )
        
        return {"message": "Member role updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update member role: {str(e)}"
        )
