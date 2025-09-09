from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from app.core.deps import get_current_user, CurrentUser
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.services.organization_service import OrganizationService
import logging
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for API
class CreateOrganizationRequest(BaseModel):
    name: str
    display_name: Optional[str] = None
    domain: Optional[str] = None

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: CreateOrganizationRequest,
    current_user: CurrentUser = Depends(get_current_user)
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all organizations the current user belongs to"""
    # Use the organizations already loaded in the current user object
    organizations = []
    for org in current_user.organizations:
        try:
            organizations.append(OrganizationResponse(
                id=org["id"],
                name=org["name"],
                display_name=org.get("display_name", org["name"]),
                domain=None,  # Not available in current structure
                is_active=True,  # Assume active if user has access
                created_at=org.get("joined_at", "2025-01-01T00:00:00Z"),
                updated_at=org.get("joined_at", "2025-01-01T00:00:00Z")
            ))
        except (ValueError, KeyError) as e:
            logger.error(f"Error processing organization data: {e}")
            continue
    
    return organizations

@router.get("/organization/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific organization by ID"""
    org_service = OrganizationService()
    
    # Check if user belongs to organization
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    if not await org_service.user_belongs_to_organization(current_user.id, org_uuid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )
    
    org = await org_service.get_organization(org_uuid)
    
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
