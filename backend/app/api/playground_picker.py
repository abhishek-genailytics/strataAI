"""
Playground picker aggregator endpoint for single round-trip configuration data.
Combines models, provider status, and session data for efficient frontend loading.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..models.playground_models import PlaygroundModelsResponse
from ..api.playground_keys import ProvidersStatusResponse
from ..models.playground_session import PlaygroundSessionRead
from ..services.models_service import ModelsService
from ..services.key_preflight import get_provider_status
from ..services.playground_session_svc import PlaygroundSessionService
from ..utils.supabase_client import get_supabase_user_client
from ..errors.openai_envelope import openai_error

router = APIRouter(prefix="/playground/picker", tags=["playground-picker"])


class PickerConfigResponse(BaseModel):
    """Aggregated configuration data for playground picker."""
    models: PlaygroundModelsResponse
    provider_status: ProvidersStatusResponse
    session: Optional[PlaygroundSessionRead] = None


@router.get("/config", response_model=PickerConfigResponse)
async def get_picker_config(
    session_id: Optional[UUID] = Query(None, description="Optional session ID to include session data"),
    provider: Optional[str] = Query(None, description="Comma-separated provider slugs filter for models/status"),
    include_pricing: bool = Query(True, description="Include pricing information in models"),
    include_capabilities: bool = Query(True, description="Include capabilities information in models"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    Get aggregated picker configuration data in a single request.
    
    This endpoint combines:
    1. GET /playground/models - Available models with branding and availability
    2. GET /playground/providers/status - Provider key status with branding
    3. GET /playground/sessions/{id} - Optional session data if session_id provided
    
    Query Parameters:
        session_id: Optional session ID to include current session data
        provider: Optional comma-separated provider filter (e.g., 'openai,anthropic')
        include_pricing: Include pricing data in models response
        include_capabilities: Include capabilities data in models response
    
    Returns:
        PickerConfigResponse with models, provider_status, and optional session data
    """
    if not organization:
        openai_error(400, "Organization context is required")
    
    try:
        # Get user's JWT token for RLS-safe queries
        if not current_user.jwt_token:
            openai_error(401, "User authentication token required")
        
        supabase = get_supabase_user_client(current_user.jwt_token)
        
        # 1. Get models data
        models_service = ModelsService()
        models_response = await models_service.list_models(
            current_user=current_user,
            current_org_id=organization.id,
            model_type="chat",
            provider=provider,
            include_pricing=include_pricing,
            include_capabilities=include_capabilities
        )
        
        # 2. Get provider status data
        # Build provider filter
        provider_filter = None
        if provider:
            provider_names = [p.strip().lower() for p in provider.split(',')]
            provider_filter = provider_names
        
        # Get all providers (or filtered list)
        providers_query = supabase.table("ai_providers").select("id, name, display_name, logo_url")
        if provider_filter:
            providers_query = providers_query.in_("name", provider_filter)
        
        providers_result = providers_query.execute()
        
        provider_status_data = []
        if providers_result.data:
            # Extract provider IDs and create mapping
            provider_ids = []
            provider_map = {}
            for provider_data in providers_result.data:
                provider_id = UUID(provider_data["id"])
                provider_ids.append(provider_id)
                provider_map[provider_id] = {
                    "name": provider_data["name"],
                    "display_name": provider_data["display_name"],
                    "logo_url": provider_data.get("logo_url")
                }
            
            # Get key status for all providers
            status_map = await get_provider_status(
                org_id=organization.id,
                provider_ids=provider_ids,
                user_jwt=current_user.jwt_token
            )
            
            # Build provider status response data
            for provider_id, status in status_map.items():
                provider_info = provider_map[provider_id]
                
                # Format last_used_at as ISO string
                last_used_str = None
                if status.last_used_at:
                    last_used_str = status.last_used_at.isoformat().replace('+00:00', 'Z')
                
                provider_status_data.append({
                    "provider": provider_info["name"],
                    "provider_id": str(provider_id),
                    "display_name": provider_info["display_name"],
                    "logo_url": provider_info["logo_url"],
                    "has_org_api_key": status.has_org_api_key,
                    "is_active": status.is_active,
                    "key_prefix": status.key_prefix,
                    "last_used_at": last_used_str
                })
            
            # Sort by provider name for consistent ordering
            provider_status_data.sort(key=lambda x: x["provider"])
        
        provider_status_response = ProvidersStatusResponse(data=provider_status_data)
        
        # 3. Get session data if requested
        session_data = None
        if session_id:
            session_service = PlaygroundSessionService()
            session_data = await session_service.get_session(
                session_id=session_id,
                user_id=current_user.id,
                organization_id=organization.id
            )
        
        return PickerConfigResponse(
            models=models_response,
            provider_status=provider_status_response,
            session=session_data
        )
        
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise e  # Already an OpenAI-formatted error
        else:
            openai_error(500, f"Failed to get picker configuration: {str(e)}")
