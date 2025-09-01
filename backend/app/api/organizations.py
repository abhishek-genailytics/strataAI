from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrganizationCreate
from app.services.organization_service import OrganizationService
from app.utils.supabase_client import get_supabase_client

router = APIRouter()

# Pydantic models for API
class OrganizationResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str]
    domain: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

class CreateOrganizationRequest(BaseModel):
    name: str
    display_name: Optional[str] = None
    domain: Optional[str] = None

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new organization and add the current user as admin"""
    supabase = get_supabase_client()
    
    # Check if user already has an organization
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.id)
    
    if user_orgs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already belongs to an organization"
        )
    
    # Create organization
    org_create_data = OrganizationCreate(
        name=org_data.name,
        display_name=org_data.display_name or org_data.name,
        domain=org_data.domain,
        is_active=True
    )
    
    org = await org_service.create_organization(org_create_data, current_user.id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        display_name=org.display_name,
        domain=org.domain,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat()
    )

@router.get("/", response_model=List[OrganizationResponse])
async def get_user_organizations(
    current_user: User = Depends(get_current_user)
):
    """Get all organizations the current user belongs to"""
    org_service = OrganizationService()
    user_orgs = await org_service.get_user_organizations(current_user.id)
    
    organizations = []
    for user_org in user_orgs:
        org = await org_service.get_organization(user_org.organization_id)
        if org:
            organizations.append(OrganizationResponse(
                id=str(org.id),
                name=org.name,
                display_name=org.display_name,
                domain=org.domain,
                is_active=org.is_active,
                created_at=org.created_at.isoformat(),
                updated_at=org.updated_at.isoformat()
            ))
    
    return organizations

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific organization by ID"""
    org_service = OrganizationService()
    
    # Check if user belongs to organization
    if not await org_service.user_belongs_to_organization(current_user.id, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )
    
    org = await org_service.get_organization(org_id)
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        display_name=org.display_name,
        domain=org.domain,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat()
    )
