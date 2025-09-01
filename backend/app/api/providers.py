from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.deps import get_db, get_current_user
from ..models.ai_provider import AIProvider, AIProviderCreate, AIProviderUpdate
from ..models.ai_model import AIModel, AIModelCreate, AIModelUpdate
from ..models.model_pricing import ModelPricing, ModelPricingCreate, ModelPricingUpdate
from ..models.provider_capability import ProviderCapability, ProviderCapabilityCreate, ProviderCapabilityUpdate
from ..services.ai_model_service import ai_model_service
from ..services.model_pricing_service import model_pricing_service
from ..services.provider_capability_service import provider_capability_service
from ..models.user import User

router = APIRouter()


# Provider endpoints
@router.get("/", response_model=List[AIProvider])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Return only active providers")
):
    """List all AI providers."""
    # TODO: Implement provider service
    # For now, return empty list
    return []


@router.get("/{provider_id}", response_model=AIProvider)
async def get_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI provider."""
    # TODO: Implement provider service
    raise HTTPException(status_code=404, detail="Provider not found")


@router.post("/", response_model=AIProvider)
async def create_provider(
    provider_data: AIProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI provider."""
    # TODO: Implement provider service
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{provider_id}", response_model=AIProvider)
async def update_provider(
    provider_id: UUID,
    provider_data: AIProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an AI provider."""
    # TODO: Implement provider service
    raise HTTPException(status_code=501, detail="Not implemented")


# Model endpoints
@router.get("/{provider_id}/models", response_model=List[AIModel])
async def list_provider_models(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """List all models for a specific provider."""
    models = await ai_model_service.get_by_provider(db, provider_id)
    
    if model_type:
        models = [model for model in models if model.model_type == model_type]
    
    return models


@router.get("/models", response_model=List[dict])
async def list_all_models_with_pricing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """List all models with their pricing information."""
    models_with_pricing = await ai_model_service.get_models_with_pricing(db, provider_id)
    
    if model_type:
        models_with_pricing = [model for model in models_with_pricing if model["model_type"] == model_type]
    
    return models_with_pricing


@router.get("/models/{model_id}", response_model=AIModel)
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI model."""
    model = await ai_model_service.get_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/{provider_id}/models", response_model=AIModel)
async def create_model(
    provider_id: UUID,
    model_data: AIModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI model for a provider."""
    model_data.provider_id = provider_id
    model = await ai_model_service.create(db, model_data)
    return model


@router.put("/models/{model_id}", response_model=AIModel)
async def update_model(
    model_id: UUID,
    model_data: AIModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an AI model."""
    model = await ai_model_service.update(db, model_id, model_data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an AI model."""
    success = await ai_model_service.delete(db, model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}


# Pricing endpoints
@router.get("/models/{model_id}/pricing", response_model=List[ModelPricing])
async def list_model_pricing(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all pricing for a specific model."""
    return await model_pricing_service.get_by_model(db, model_id)


@router.get("/models/{model_id}/pricing/current", response_model=List[ModelPricing])
async def get_current_model_pricing(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current active pricing for a model."""
    return await model_pricing_service.get_current_pricing(db, model_id)


@router.post("/models/{model_id}/pricing", response_model=ModelPricing)
async def create_model_pricing(
    model_id: UUID,
    pricing_data: ModelPricingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new pricing for a model."""
    pricing_data.model_id = model_id
    pricing = await model_pricing_service.create(db, pricing_data)
    return pricing


@router.put("/pricing/{pricing_id}", response_model=ModelPricing)
async def update_model_pricing(
    pricing_id: UUID,
    pricing_data: ModelPricingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update model pricing."""
    pricing = await model_pricing_service.update(db, pricing_id, pricing_data)
    if not pricing:
        raise HTTPException(status_code=404, detail="Pricing not found")
    return pricing


@router.delete("/pricing/{pricing_id}")
async def delete_model_pricing(
    pricing_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete model pricing."""
    success = await model_pricing_service.delete(db, pricing_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pricing not found")
    return {"message": "Pricing deleted successfully"}


# Capability endpoints
@router.get("/{provider_id}/capabilities", response_model=List[ProviderCapability])
async def list_provider_capabilities(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all capabilities for a specific provider."""
    return await provider_capability_service.get_by_provider(db, provider_id)


@router.get("/{provider_id}/capabilities/{capability_name}", response_model=ProviderCapability)
async def get_provider_capability(
    provider_id: UUID,
    capability_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific capability for a provider."""
    capability = await provider_capability_service.get_by_name(db, provider_id, capability_name)
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    return capability


@router.post("/{provider_id}/capabilities", response_model=ProviderCapability)
async def create_provider_capability(
    provider_id: UUID,
    capability_data: ProviderCapabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new capability for a provider."""
    capability_data.provider_id = provider_id
    capability = await provider_capability_service.create(db, capability_data)
    return capability


@router.put("/capabilities/{capability_id}", response_model=ProviderCapability)
async def update_provider_capability(
    capability_id: UUID,
    capability_data: ProviderCapabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a provider capability."""
    capability = await provider_capability_service.update(db, capability_id, capability_data)
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    return capability


@router.delete("/capabilities/{capability_id}")
async def delete_provider_capability(
    capability_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a provider capability."""
    success = await provider_capability_service.delete(db, capability_id)
    if not success:
        raise HTTPException(status_code=404, detail="Capability not found")
    return {"message": "Capability deleted successfully"}
