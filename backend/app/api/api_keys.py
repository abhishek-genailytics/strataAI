"""
API endpoints for API key management with organization context.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.api_key import APIKeyCreate, APIKeyUpdate, APIKeyDisplay, APIKeyValidationResult
from ..models.organization import Organization
from ..services.api_key_service import api_key_service

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=APIKeyDisplay, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    *,
    api_key_in: APIKeyCreate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    validate: bool = True
):
    """Create a new API key with validation and encryption for an organization + provider."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"create_api_key called with organization: {organization}")
    logger.info(f"Current user: {current_user.user_id}")

    if not organization:
        logger.error("No organization context found for API key creation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required for API key creation"
        )
    
    logger.info(f"Creating API key for organization {organization.id}")
    logger.info(f"Organization: {organization}")
    logger.info(f"API key data: {api_key_in}")
    
    try:
        api_key, validation_result = await api_key_service.validate_and_create(
            obj_in=api_key_in, 
            organization_id=organization.id,
            validate_key=validate
        )
        
        # Return display version with masked key
        display_keys = await api_key_service.get_organization_keys(
            organization_id=organization.id
        )
        
        # Find the newly created key
        for display_key in display_keys:
            if display_key.id == api_key["id"]:
                return display_key
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created API key"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_str = str(e)
        # Check for unique constraint violation (duplicate API key)
        if "duplicate key value violates unique constraint" in error_str and "api_keys_org_provider_unique" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An API key for this provider already exists in your organization. Please update the existing key instead."
            )
        # Check for other constraint violations
        elif "violates" in error_str and "constraint" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data provided. Please check your input and try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create API key: {error_str}"
            )


@router.get("/", response_model=List[APIKeyDisplay])
async def list_api_keys(
    *,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """List organization's API keys with masked values."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        display_keys = await api_key_service.get_organization_keys(
            organization_id=organization.id
        )
        return display_keys
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.get("/{api_key_id}", response_model=APIKeyDisplay)
async def get_api_key(
    *,
    api_key_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get a specific API key by ID in organization context."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        display_keys = await api_key_service.get_organization_keys(
            organization_id=organization.id
        )
        
        for display_key in display_keys:
            if display_key.id == api_key_id:
                return display_key
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API key: {str(e)}"
        )


@router.put("/{api_key_id}", response_model=APIKeyDisplay)
async def update_api_key(
    *,
    api_key_id: UUID,
    api_key_in: APIKeyUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Update an API key in organization context."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Check if key exists and belongs to organization
        api_key = await api_key_service.get_with_provider(
            api_key_id=api_key_id, 
            organization_id=organization.id
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update the key
        updated_key = await api_key_service.update_api_key(
            api_key_id=api_key_id,
            update_data=api_key_in,
            organization_id=organization.id
        )
        
        # Return display version
        display_keys = await api_key_service.get_organization_keys(
            organization_id=organization.id
        )
        
        for display_key in display_keys:
            if display_key.id == api_key_id:
                return display_key
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated API key"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    *,
    api_key_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Delete (deactivate) an API key in organization context."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        api_key = await api_key_service.deactivate(
            api_key_id=api_key_id, 
            organization_id=organization.id
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )


@router.post("/{api_key_id}/validate", response_model=APIKeyValidationResult)
async def validate_api_key(
    *,
    api_key_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Validate an existing API key against its provider in organization context."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Get the decrypted key
        decrypted_key = await api_key_service.get_decrypted_key(
            api_key_id=api_key_id, 
            organization_id=organization.id
        )
        if not decrypted_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or inactive"
            )
        
        # Get provider info
        api_key = await api_key_service.get_with_provider(
            api_key_id=api_key_id, 
            organization_id=organization.id
        )
        
        # Get provider name from provider_id
        from supabase import Client
        from ..core.database import get_supabase_client
        supabase: Client = get_supabase_client()
        provider_response = supabase.table("ai_providers").select("name").eq("id", api_key["provider_id"]).execute()
        
        if not provider_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        provider_name = provider_response.data[0]["name"]
        
        # Import here to avoid circular imports
        from ..services.api_key_validator import api_key_validator
        
        # Validate the key
        validation_result = await api_key_validator.validate_api_key(
            decrypted_key, provider_name
        )
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate API key: {str(e)}"
        )


@router.get("/{api_key_id}/reveal")
async def reveal_api_key(
    *,
    api_key_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Reveal the actual API key value (use with caution) in organization context."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        decrypted_key = await api_key_service.get_decrypted_key(
            api_key_id=api_key_id, 
            organization_id=organization.id
        )
        if not decrypted_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or inactive"
            )
        
        return {"api_key": decrypted_key}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reveal API key: {str(e)}"
        )
