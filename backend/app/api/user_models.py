"""
API endpoints for user model configurations.
Uses regular Supabase authentication instead of PAT for playground usage.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..utils.supabase_client import supabase_service

router = APIRouter(prefix="/user-models", tags=["user-models"])


class UserModelConfig(BaseModel):
    id: UUID
    model_id: UUID
    model_name: str
    display_name: str
    provider_name: str
    provider_id: UUID
    is_enabled: bool
    max_tokens: Optional[int] = None
    supports_streaming: bool = False
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None
    configuration: dict = {}


class EnableModelRequest(BaseModel):
    model_id: UUID
    configuration: dict = {}


@router.get("/configured", response_model=List[UserModelConfig])
async def get_user_configured_models(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get models that the user has configured and enabled for their organization."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Get user's configured models with provider and model details
        query = """
        SELECT 
            umc.id,
            umc.model_id,
            umc.is_enabled,
            umc.configuration,
            am.model_name,
            am.display_name,
            am.max_tokens,
            am.supports_streaming,
            ap.name as provider_name,
            ap.id as provider_id,
            mp_input.price_per_unit as cost_per_1k_input_tokens,
            mp_output.price_per_unit as cost_per_1k_output_tokens
        FROM user_model_configurations umc
        JOIN ai_models am ON umc.model_id = am.id
        JOIN ai_providers ap ON am.provider_id = ap.id
        LEFT JOIN model_pricing mp_input ON am.id = mp_input.model_id 
            AND mp_input.pricing_type = 'input' 
            AND mp_input.is_active = true
        LEFT JOIN model_pricing mp_output ON am.id = mp_output.model_id 
            AND mp_output.pricing_type = 'output' 
            AND mp_output.is_active = true
        WHERE umc.user_id = %s 
            AND umc.organization_id = %s 
            AND umc.is_enabled = true
            AND am.is_active = true
            AND ap.is_active = true
        ORDER BY ap.name, am.display_name
        """
        
        result = supabase_service.rpc(
            'execute_sql',
            {
                'query': query,
                'params': [str(current_user.user_id), str(organization.id)]
            }
        ).execute()
        
        if result.data:
            configured_models = []
            for row in result.data:
                configured_models.append(UserModelConfig(
                    id=row['id'],
                    model_id=row['model_id'],
                    model_name=row['model_name'],
                    display_name=row['display_name'],
                    provider_name=row['provider_name'],
                    provider_id=row['provider_id'],
                    is_enabled=row['is_enabled'],
                    max_tokens=row['max_tokens'],
                    supports_streaming=row['supports_streaming'],
                    cost_per_1k_input_tokens=row['cost_per_1k_input_tokens'],
                    cost_per_1k_output_tokens=row['cost_per_1k_output_tokens'],
                    configuration=row['configuration'] or {}
                ))
            return configured_models
        
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configured models: {str(e)}"
        )


@router.get("/available", response_model=List[UserModelConfig])
async def get_available_models_for_user(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get models available to user based on their configured API keys."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Get models for providers where user has active API keys
        query = """
        SELECT DISTINCT
            am.id as model_id,
            am.model_name,
            am.display_name,
            am.max_tokens,
            am.supports_streaming,
            ap.name as provider_name,
            ap.id as provider_id,
            mp_input.price_per_unit as cost_per_1k_input_tokens,
            mp_output.price_per_unit as cost_per_1k_output_tokens,
            COALESCE(umc.is_enabled, false) as is_enabled,
            COALESCE(umc.id, gen_random_uuid()) as id,
            COALESCE(umc.configuration, '{}') as configuration
        FROM ai_models am
        JOIN ai_providers ap ON am.provider_id = ap.id
        JOIN api_keys ak ON ap.id = ak.provider_id
        LEFT JOIN user_model_configurations umc ON am.id = umc.model_id 
            AND umc.user_id = %s 
            AND umc.organization_id = %s
        LEFT JOIN model_pricing mp_input ON am.id = mp_input.model_id 
            AND mp_input.pricing_type = 'input' 
            AND mp_input.is_active = true
        LEFT JOIN model_pricing mp_output ON am.id = mp_output.model_id 
            AND mp_output.pricing_type = 'output' 
            AND mp_output.is_active = true
        WHERE ak.organization_id = %s 
            AND ak.is_active = true
            AND am.is_active = true
            AND ap.is_active = true
        ORDER BY ap.name, am.display_name
        """
        
        result = supabase_service.rpc(
            'execute_sql',
            {
                'query': query,
                'params': [str(current_user.user_id), str(organization.id), str(organization.id)]
            }
        ).execute()
        
        if result.data:
            available_models = []
            for row in result.data:
                available_models.append(UserModelConfig(
                    id=row['id'],
                    model_id=row['model_id'],
                    model_name=row['model_name'],
                    display_name=row['display_name'],
                    provider_name=row['provider_name'],
                    provider_id=row['provider_id'],
                    is_enabled=row['is_enabled'],
                    max_tokens=row['max_tokens'],
                    supports_streaming=row['supports_streaming'],
                    cost_per_1k_input_tokens=row['cost_per_1k_input_tokens'],
                    cost_per_1k_output_tokens=row['cost_per_1k_output_tokens'],
                    configuration=row['configuration'] or {}
                ))
            return available_models
        
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available models: {str(e)}"
        )


@router.post("/enable", response_model=UserModelConfig)
async def enable_model_for_user(
    request: EnableModelRequest,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Enable a model for the user with optional configuration."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Insert or update user model configuration
        result = supabase_service.table("user_model_configurations").upsert({
            "user_id": str(current_user.user_id),
            "organization_id": str(organization.id),
            "model_id": str(request.model_id),
            "is_enabled": True,
            "configuration": request.configuration,
            "updated_at": "now()"
        }).execute()
        
        if result.data:
            # Return the configured model details
            return await get_model_config_details(
                result.data[0]['id'], 
                current_user, 
                organization
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable model"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable model: {str(e)}"
        )


@router.delete("/{config_id}")
async def disable_model_for_user(
    config_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Disable a model for the user."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        result = supabase_service.table("user_model_configurations").update({
            "is_enabled": False,
            "updated_at": "now()"
        }).eq("id", str(config_id)).eq("user_id", str(current_user.user_id)).eq(
            "organization_id", str(organization.id)
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model configuration not found"
            )
        
        return {"message": "Model disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable model: {str(e)}"
        )


async def get_model_config_details(
    config_id: UUID, 
    current_user: CurrentUser, 
    organization: Organization
) -> UserModelConfig:
    """Helper function to get detailed model configuration."""
    query = """
    SELECT 
        umc.id,
        umc.model_id,
        umc.is_enabled,
        umc.configuration,
        am.model_name,
        am.display_name,
        am.max_tokens,
        am.supports_streaming,
        ap.name as provider_name,
        ap.id as provider_id,
        mp_input.price_per_unit as cost_per_1k_input_tokens,
        mp_output.price_per_unit as cost_per_1k_output_tokens
    FROM user_model_configurations umc
    JOIN ai_models am ON umc.model_id = am.id
    JOIN ai_providers ap ON am.provider_id = ap.id
    LEFT JOIN model_pricing mp_input ON am.id = mp_input.model_id 
        AND mp_input.pricing_type = 'input' 
        AND mp_input.is_active = true
    LEFT JOIN model_pricing mp_output ON am.id = mp_output.model_id 
        AND mp_output.pricing_type = 'output' 
        AND mp_output.is_active = true
    WHERE umc.id = %s 
        AND umc.user_id = %s 
        AND umc.organization_id = %s
    """
    
    result = supabase_service.rpc(
        'execute_sql',
        {
            'query': query,
            'params': [str(config_id), str(current_user.user_id), str(organization.id)]
        }
    ).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found"
        )
    
    row = result.data[0]
    return UserModelConfig(
        id=row['id'],
        model_id=row['model_id'],
        model_name=row['model_name'],
        display_name=row['display_name'],
        provider_name=row['provider_name'],
        provider_id=row['provider_id'],
        is_enabled=row['is_enabled'],
        max_tokens=row['max_tokens'],
        supports_streaming=row['supports_streaming'],
        cost_per_1k_input_tokens=row['cost_per_1k_input_tokens'],
        cost_per_1k_output_tokens=row['cost_per_1k_output_tokens'],
        configuration=row['configuration'] or {}
    )
