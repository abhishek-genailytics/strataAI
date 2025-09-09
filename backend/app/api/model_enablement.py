"""
API endpoints for model enablement functionality.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..models.model_enablement import EnableModelsRequest, EnableModelsResponse
from ..services.model_enablement_service import model_enablement_service

router = APIRouter()


@router.post("/enable", response_model=EnableModelsResponse)
async def enable_models(
    request: EnableModelsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(get_organization_context)
):
    """
    Enable selected models for the current organization.
    
    This endpoint is called when a user configures a provider and selects
    which models should be available for their organization.
    """
    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Organization context required"
        )
    
    try:
        response = await model_enablement_service.enable_models_for_organization(
            organization_id=organization.id,
            request=request
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enable models: {str(e)}"
        )


@router.get("/organization/enabled/{provider_id}")
async def get_organization_enabled_models(
    provider_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(get_organization_context)
):
    """
    Get enabled models for a specific provider in the current organization.
    
    This endpoint is used by the manage provider page to show which models
    are currently enabled for the organization.
    """
    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Organization context required"
        )
    
    try:
        enabled_models = await model_enablement_service.get_enabled_models_for_provider(
            organization_id=organization.id,
            provider_id=str(provider_id)
        )
        return {
            "provider_id": str(provider_id),
            "organization_id": str(organization.id),
            "enabled_models": enabled_models,
            "count": len(enabled_models)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enabled models: {str(e)}"
        )
