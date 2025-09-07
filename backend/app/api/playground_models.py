"""
Playground models listing API endpoint.
Provides filtered, enriched model catalog for playground use.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from uuid import UUID

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..models.playground_models import PlaygroundModelsResponse
from ..services.models_service import ModelsService

router = APIRouter(prefix="/playground", tags=["playground"])


@router.get("/models", response_model=PlaygroundModelsResponse)
async def list_playground_models(
    type: str = Query("chat", description="Model type filter"),
    provider: Optional[str] = Query(None, description="Provider filter (openai, anthropic, etc.)"),
    include_pricing: bool = Query(True, description="Include pricing information"),
    include_capabilities: bool = Query(True, description="Include capabilities information"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Organization = Depends(get_organization_context)
) -> PlaygroundModelsResponse:
    """
    List models available to user in playground.
    
    Returns models filtered by:
    - Model type (default: chat)
    - Optional provider filter
    - Organization enablement
    - Available API keys
    - User preferences
    
    Enriched with:
    - Capabilities (streaming, function calling, vision)
    - Token limits (input/output)
    - Pricing information (input/output rates)
    - Availability status (org enabled, API key present, user enabled)
    - User default flags
    """
    if not organization:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Organization context required")
    
    models_service = ModelsService()
    
    return await models_service.list_models(
        current_user=current_user,
        current_org_id=organization.id,
        model_type=type,
        provider=provider,
        include_pricing=include_pricing,
        include_capabilities=include_capabilities
    )
