from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.ai_provider import AIProvider, AIProviderCreate, AIProviderUpdate
from ..models.ai_model import AIModel, AIModelCreate, AIModelUpdate
from ..models.model_pricing import ModelPricing, ModelPricingCreate, ModelPricingUpdate
from ..models.provider_capability import ProviderCapability, ProviderCapabilityCreate, ProviderCapabilityUpdate
from ..models.organization import Organization
from ..services.ai_model_service import ai_model_service
from ..services.model_pricing_service import model_pricing_service
from ..services.provider_capability_service import provider_capability_service
from ..services.api_key_service import api_key_service

router = APIRouter()


# Provider endpoints
@router.get("/", response_model=List[AIProvider])
async def list_providers(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    active_only: bool = Query(True, description="Return only active providers")
):
    """List all AI providers."""
    try:
        from ..utils.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        
        # Query providers from Supabase
        query = supabase.table("ai_providers").select("*")
        if active_only:
            query = query.eq("is_active", True)
        
        response = query.execute()
        
        # Convert to Pydantic models
        provider_list = []
        for provider_data in response.data or []:
            provider_dict = {
                "id": provider_data["id"],
                "name": provider_data["name"],
                "display_name": provider_data["display_name"],
                "base_url": provider_data["base_url"],
                "is_active": provider_data["is_active"],
                "created_at": provider_data["created_at"],
                "updated_at": provider_data["updated_at"],
                "logo_url": provider_data.get("logo_url"),
                "website_url": provider_data.get("website_url"),
                "description": provider_data.get("description")
            }
            provider_list.append(AIProvider(**provider_dict))
        
        return provider_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve providers: {str(e)}"
        )


@router.get("/organization/configured", response_model=List[dict])
async def get_organization_configured_providers(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get providers that have API keys configured for the current organization."""
    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Organization context required"
        )
    
    try:
        # Get API keys for the organization
        api_keys = await api_key_service.get_organization_keys(organization.id)
        
        # Get unique provider IDs from API keys
        provider_ids = list(set([key["provider_id"] for key in api_keys]))
        
        # Get provider details
        configured_providers = []
        for provider_id in provider_ids:
            provider = await get_provider(provider_id, current_user)
            if provider:
                configured_providers.append({
                    "provider": provider,
                    "api_key_count": len([k for k in api_keys if k["provider_id"] == provider_id])
                })
        
        return configured_providers
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configured providers: {str(e)}"
        )


@router.get("/{provider_id}", response_model=AIProvider)
async def get_provider(
    provider_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific AI provider."""
    try:
        from ..utils.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        
        response = supabase.table("ai_providers").select("*").eq("id", str(provider_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        provider_data = response.data[0]
        provider_dict = {
            "id": provider_data["id"],
            "name": provider_data["name"],
            "display_name": provider_data["display_name"],
            "base_url": provider_data["base_url"],
            "is_active": provider_data["is_active"],
            "created_at": provider_data["created_at"],
            "updated_at": provider_data["updated_at"],
            "logo_url": provider_data.get("logo_url"),
            "website_url": provider_data.get("website_url"),
            "description": provider_data.get("description")
        }
        
        return AIProvider(**provider_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve provider: {str(e)}"
        )


@router.post("/", response_model=AIProvider)
async def create_provider(
    provider_data: AIProviderCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new AI provider."""
    # This endpoint is typically not needed as providers are pre-configured
    raise HTTPException(status_code=501, detail="Provider creation not supported")


@router.put("/{provider_id}", response_model=AIProvider)
async def update_provider(
    provider_id: UUID,
    provider_data: AIProviderUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an AI provider."""
    # This endpoint is typically not needed as providers are pre-configured
    raise HTTPException(status_code=501, detail="Provider updates not supported")


# Model endpoints
@router.get("/{provider_id}/models", response_model=List[AIModel])
async def list_provider_models(
    provider_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """List all models for a specific provider."""
    try:
        # For now, return empty list since we need to implement model service with Supabase
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.get("/models", response_model=List[dict])
async def list_all_models_with_pricing(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """List all models with their pricing information."""
    try:
        # For now, return empty list since we need to implement model service with Supabase
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models with pricing: {str(e)}"
        )


@router.get("/models/{model_id}", response_model=AIModel)
async def get_model(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific AI model."""
    try:
        raise HTTPException(status_code=404, detail="Model not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model: {str(e)}"
        )


@router.post("/{provider_id}/models", response_model=AIModel)
async def create_model(
    provider_id: UUID,
    model_data: AIModelCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new AI model for a provider."""
    # This endpoint is typically not needed as models are pre-configured
    raise HTTPException(status_code=501, detail="Model creation not supported")


@router.put("/models/{model_id}", response_model=AIModel)
async def update_model(
    model_id: UUID,
    model_data: AIModelUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an AI model."""
    # This endpoint is typically not needed as models are pre-configured
    raise HTTPException(status_code=501, detail="Model updates not supported")


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete an AI model."""
    # This endpoint is typically not needed as models are pre-configured
    raise HTTPException(status_code=501, detail="Model deletion not supported")


# Pricing endpoints
@router.get("/models/{model_id}/pricing", response_model=List[ModelPricing])
async def list_model_pricing(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all pricing for a specific model."""
    try:
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model pricing: {str(e)}"
        )


@router.get("/models/{model_id}/pricing/current", response_model=List[ModelPricing])
async def get_current_model_pricing(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current active pricing for a model."""
    try:
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve current model pricing: {str(e)}"
        )


@router.post("/models/{model_id}/pricing", response_model=ModelPricing)
async def create_model_pricing(
    model_id: UUID,
    pricing_data: ModelPricingCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create new pricing for a model."""
    # This endpoint is typically not needed as pricing is pre-configured
    raise HTTPException(status_code=501, detail="Pricing creation not supported")


@router.put("/pricing/{pricing_id}", response_model=ModelPricing)
async def update_model_pricing(
    pricing_id: UUID,
    pricing_data: ModelPricingUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update model pricing."""
    # This endpoint is typically not needed as pricing is pre-configured
    raise HTTPException(status_code=501, detail="Pricing updates not supported")


@router.delete("/pricing/{pricing_id}")
async def delete_model_pricing(
    pricing_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete model pricing."""
    # This endpoint is typically not needed as pricing is pre-configured
    raise HTTPException(status_code=501, detail="Pricing deletion not supported")


# Capability endpoints
@router.get("/{provider_id}/capabilities", response_model=List[ProviderCapability])
async def list_provider_capabilities(
    provider_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all capabilities for a specific provider."""
    try:
        return []
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve provider capabilities: {str(e)}"
        )


@router.get("/{provider_id}/capabilities/{capability_name}", response_model=ProviderCapability)
async def get_provider_capability(
    provider_id: UUID,
    capability_name: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific capability for a provider."""
    try:
        raise HTTPException(status_code=404, detail="Capability not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve provider capability: {str(e)}"
        )


@router.post("/{provider_id}/capabilities", response_model=ProviderCapability)
async def create_provider_capability(
    provider_id: UUID,
    capability_data: ProviderCapabilityCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new capability for a provider."""
    # This endpoint is typically not needed as capabilities are pre-configured
    raise HTTPException(status_code=501, detail="Capability creation not supported")


@router.put("/capabilities/{capability_id}", response_model=ProviderCapability)
async def update_provider_capability(
    capability_id: UUID,
    capability_data: ProviderCapabilityUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update a provider capability."""
    # This endpoint is typically not needed as capabilities are pre-configured
    raise HTTPException(status_code=501, detail="Capability updates not supported")


@router.delete("/capabilities/{capability_id}")
async def delete_provider_capability(
    capability_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a provider capability."""
    # This endpoint is typically not needed as capabilities are pre-configured
    raise HTTPException(status_code=501, detail="Capability deletion not supported")
