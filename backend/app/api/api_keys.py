"""
API endpoints for API key management.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models.api_key import APIKeyCreate, APIKeyUpdate, APIKeyDisplay, APIKeyValidationResult
from ..models.user import User
from ..services.api_key_service import api_key_service
from ..api.auth import get_current_user

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=APIKeyDisplay, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    *,
    db: AsyncSession = Depends(get_db),
    api_key_in: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    validate: bool = True
):
    """Create a new API key with validation and encryption."""
    try:
        api_key, validation_result = await api_key_service.validate_and_create(
            db, obj_in=api_key_in, user_id=current_user.id, validate_key=validate
        )
        
        # Return display version with masked key
        display_keys = await api_key_service.get_user_keys_with_providers(
            db, user_id=current_user.id
        )
        
        # Find the newly created key
        for display_key in display_keys:
            if display_key.id == api_key.id:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/", response_model=List[APIKeyDisplay])
async def list_api_keys(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: UUID = None
):
    """List user's API keys with masked values."""
    try:
        display_keys = await api_key_service.get_user_keys_with_providers(
            db, user_id=current_user.id, project_id=project_id
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
    db: AsyncSession = Depends(get_db),
    api_key_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get a specific API key by ID."""
    try:
        display_keys = await api_key_service.get_user_keys_with_providers(
            db, user_id=current_user.id
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
    db: AsyncSession = Depends(get_db),
    api_key_id: UUID,
    api_key_in: APIKeyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an API key."""
    try:
        # Check if key exists and belongs to user
        api_key = await api_key_service.get_with_provider(
            db, api_key_id=api_key_id, user_id=current_user.id
        )
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update the key
        updated_key = await api_key_service.update(db, db_obj=api_key, obj_in=api_key_in)
        
        # Return display version
        display_keys = await api_key_service.get_user_keys_with_providers(
            db, user_id=current_user.id
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
    db: AsyncSession = Depends(get_db),
    api_key_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete (deactivate) an API key."""
    try:
        api_key = await api_key_service.deactivate(
            db, api_key_id=api_key_id, user_id=current_user.id
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
    db: AsyncSession = Depends(get_db),
    api_key_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Validate an existing API key against its provider."""
    try:
        # Get the decrypted key
        decrypted_key = await api_key_service.get_decrypted_key(
            db, api_key_id=api_key_id, user_id=current_user.id
        )
        if not decrypted_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or inactive"
            )
        
        # Get provider info
        api_key = await api_key_service.get_with_provider(
            db, api_key_id=api_key_id, user_id=current_user.id
        )
        
        # Import here to avoid circular imports
        from ..services.api_key_validator import api_key_validator
        
        # Validate the key
        validation_result = await api_key_validator.validate_api_key(
            decrypted_key, api_key.provider.name
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
    db: AsyncSession = Depends(get_db),
    api_key_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Reveal the actual API key value (use with caution)."""
    try:
        decrypted_key = await api_key_service.get_decrypted_key(
            db, api_key_id=api_key_id, user_id=current_user.id
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
