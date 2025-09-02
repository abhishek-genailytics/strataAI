"""
API endpoints for AI model management with organization context.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..core.database import get_db
from ..models.ai_model import AIModel, AIModelCreate, AIModelUpdate
from ..models.model_pricing import ModelPricing, ModelPricingCreate, ModelPricingUpdate
from ..models.organization import Organization
from ..services.ai_model_service import ai_model_service
from ..services.model_pricing_service import model_pricing_service
from ..services.api_key_service import api_key_service

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_models_with_pricing(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    connected_only: bool = Query(False, description="Show only models from connected providers")
):
    """List all models with their pricing information, optionally filtered by organization's connected providers."""
    try:
        from ..utils.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        
        # Query models from Supabase
        query = supabase.table("ai_models").select("""
            *,
            ai_providers!inner(
                id,
                name,
                display_name,
                logo_url,
                description
            ),
            model_pricing(*)
        """)
        
        # Filter by provider if specified
        if provider_id:
            query = query.eq("provider_id", str(provider_id))
        
        # Filter by model type if specified
        if model_type:
            query = query.eq("model_type", model_type)
        
        # Only active models
        query = query.eq("is_active", True)
        
        response = query.execute()
        
        # Convert to the expected format
        models_with_pricing = []
        for model_data in response.data or []:
            model_dict = {
                "id": model_data["id"],
                "provider_id": model_data["provider_id"],
                "model_name": model_data["model_name"],
                "display_name": model_data["display_name"],
                "description": model_data.get("description"),
                "model_type": model_data["model_type"],
                "max_tokens": model_data.get("max_tokens"),
                "max_input_tokens": model_data.get("max_input_tokens"),
                "supports_streaming": model_data.get("supports_streaming", False),
                "supports_function_calling": model_data.get("supports_function_calling", False),
                "supports_vision": model_data.get("supports_vision", False),
                "supports_audio": model_data.get("supports_audio", False),
                "capabilities": model_data.get("capabilities", {}),
                "pricing": []
            }
            
            # Add pricing information
            if model_data.get("model_pricing"):
                for pricing in model_data["model_pricing"]:
                    if pricing.get("is_active", True):
                        model_dict["pricing"].append({
                            "id": pricing["id"],
                            "pricing_type": pricing["pricing_type"],
                            "price_per_unit": float(pricing["price_per_unit"]),
                            "unit": pricing["unit"],
                            "currency": pricing["currency"],
                            "region": pricing.get("region", "us-east-1")
                        })
            
            models_with_pricing.append(model_dict)
        
        # If connected_only is True, filter by organization's connected providers
        if connected_only and organization:
            # Get API keys for the organization
            api_keys_response = supabase.table("api_keys").select("provider_id").eq("organization_id", str(organization.id)).eq("is_active", True).execute()
            
            # Get unique provider IDs from API keys
            connected_provider_ids = list(set([key["provider_id"] for key in api_keys_response.data or []]))
            
            # Filter models to only show those from connected providers
            models_with_pricing = [
                model for model in models_with_pricing 
                if model["provider_id"] in connected_provider_ids
            ]
        
        return models_with_pricing
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models with pricing: {str(e)}"
        )


@router.get("/{model_id}", response_model=AIModel)
async def get_model(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific AI model."""
    try:
        async with get_db() as db:
            model = await ai_model_service.get_by_id(db, model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model: {str(e)}"
        )


@router.get("/{model_id}/pricing", response_model=List[ModelPricing])
async def list_model_pricing(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all pricing for a specific model."""
    try:
        async with get_db() as db:
            return await model_pricing_service.get_by_model(db, model_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model pricing: {str(e)}"
        )


@router.get("/{model_id}/pricing/current", response_model=List[ModelPricing])
async def get_current_model_pricing(
    model_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get current active pricing for a model."""
    try:
        async with get_db() as db:
            return await model_pricing_service.get_current_pricing(db, model_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve current model pricing: {str(e)}"
        )


@router.get("/organization/connected", response_model=List[dict])
async def get_organization_connected_models(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """Get models from providers that have API keys configured for the current organization."""
    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Organization context required"
        )
    
    try:
        from ..utils.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        
        # Get API keys for the organization
        api_keys_response = supabase.table("api_keys").select("provider_id").eq("organization_id", str(organization.id)).eq("is_active", True).execute()
        
        # Get unique provider IDs from API keys
        connected_provider_ids = list(set([key["provider_id"] for key in api_keys_response.data or []]))
        
        if not connected_provider_ids:
            return []
        
        # Query models from connected providers
        query = supabase.table("ai_models").select("""
            *,
            ai_providers!inner(
                id,
                name,
                display_name,
                logo_url,
                description
            ),
            model_pricing(*)
        """).in_("provider_id", connected_provider_ids)
        
        # Filter by model type if specified
        if model_type:
            query = query.eq("model_type", model_type)
        
        # Only active models
        query = query.eq("is_active", True)
        
        response = query.execute()
        
        # Convert to the expected format
        connected_models = []
        for model_data in response.data or []:
            model_dict = {
                "id": model_data["id"],
                "provider_id": model_data["provider_id"],
                "model_name": model_data["model_name"],
                "display_name": model_data["display_name"],
                "description": model_data.get("description"),
                "model_type": model_data["model_type"],
                "max_tokens": model_data.get("max_tokens"),
                "max_input_tokens": model_data.get("max_input_tokens"),
                "supports_streaming": model_data.get("supports_streaming", False),
                "supports_function_calling": model_data.get("supports_function_calling", False),
                "supports_vision": model_data.get("supports_vision", False),
                "supports_audio": model_data.get("supports_audio", False),
                "capabilities": model_data.get("capabilities", {}),
                "pricing": []
            }
            
            # Add pricing information
            if model_data.get("model_pricing"):
                for pricing in model_data["model_pricing"]:
                    if pricing.get("is_active", True):
                        model_dict["pricing"].append({
                            "id": pricing["id"],
                            "pricing_type": pricing["pricing_type"],
                            "price_per_unit": float(pricing["price_per_unit"]),
                            "unit": pricing["unit"],
                            "currency": pricing["currency"],
                            "region": pricing.get("region", "us-east-1")
                        })
            
            connected_models.append(model_dict)
        
        return connected_models
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve connected models: {str(e)}"
        )
