"""
Playground provider keys API endpoints for preflight validation.
Provides status information about organization's configured provider keys.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models.organization import Organization
from ..services.key_preflight import get_provider_status
from ..utils.supabase_client import get_supabase_user_client
from ..errors.openai_envelope import openai_error

router = APIRouter(prefix="/playground", tags=["playground-keys"])


class ProviderStatusResponse(BaseModel):
    """Provider key status for UI display."""
    provider: str
    provider_id: str
    has_org_api_key: bool
    is_active: bool
    key_prefix: Optional[str] = None
    last_used_at: Optional[str] = None


class ProvidersStatusResponse(BaseModel):
    """Response containing provider status list."""
    data: List[ProviderStatusResponse]


@router.get("/providers/status", response_model=ProvidersStatusResponse)
async def get_providers_status(
    provider: Optional[str] = Query(None, description="Comma-separated provider slugs (e.g., 'openai,anthropic')"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """
    Get provider key status for UI banner/CTA display.
    
    Query Parameters:
        provider: Optional comma-separated list of provider slugs.
                 If not provided, returns all known providers.
    
    Returns:
        ProvidersStatusResponse with provider status data
    """
    if not organization:
        openai_error(400, "Organization context is required")
    
    try:
        # Get user's JWT token for RLS-safe queries
        if not current_user.jwt_token:
            openai_error(401, "User authentication token required")
        
        # Use user-scoped Supabase client
        supabase = get_supabase_user_client(current_user.jwt_token)
        
        # Build provider filter
        provider_filter = None
        if provider:
            provider_names = [p.strip().lower() for p in provider.split(',')]
            provider_filter = provider_names
        
        # Get all providers (or filtered list)
        providers_query = supabase.table("ai_providers").select("id, name, display_name")
        if provider_filter:
            providers_query = providers_query.in_("name", provider_filter)
        
        providers_result = providers_query.execute()
        
        if not providers_result.data:
            return ProvidersStatusResponse(data=[])
        
        # Extract provider IDs and create mapping
        provider_ids = []
        provider_map = {}
        for provider_data in providers_result.data:
            provider_id = UUID(provider_data["id"])
            provider_ids.append(provider_id)
            provider_map[provider_id] = {
                "name": provider_data["name"],
                "display_name": provider_data["display_name"]
            }
        
        # Get key status for all providers
        status_map = await get_provider_status(
            org_id=organization.id,
            provider_ids=provider_ids,
            user_jwt=current_user.jwt_token
        )
        
        # Build response data
        response_data = []
        for provider_id, status in status_map.items():
            provider_info = provider_map[provider_id]
            
            # Format last_used_at as ISO string
            last_used_str = None
            if status.last_used_at:
                last_used_str = status.last_used_at.isoformat().replace('+00:00', 'Z')
            
            response_data.append(ProviderStatusResponse(
                provider=provider_info["name"],
                provider_id=str(provider_id),
                has_org_api_key=status.has_org_api_key,
                is_active=status.is_active,
                key_prefix=status.key_prefix,
                last_used_at=last_used_str
            ))
        
        # Sort by provider name for consistent ordering
        response_data.sort(key=lambda x: x.provider)
        
        return ProvidersStatusResponse(data=response_data)
        
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise e  # Already an OpenAI-formatted error
        else:
            openai_error(500, f"Failed to get provider status: {str(e)}")
