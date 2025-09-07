"""
Key preflight service for provider API key validation.
Provides centralized lookup and validation for organization provider keys.
"""
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from ..utils.supabase_client import get_supabase_user_client
from ..errors.openai_envelope import openai_error


class ProviderKeyStatus(BaseModel):
    """Status of a provider's API key for an organization."""
    has_org_api_key: bool
    is_active: bool
    key_prefix: Optional[str] = None
    last_used_at: Optional[datetime] = None


async def get_provider_status(
    org_id: UUID, 
    provider_ids: List[UUID],
    user_jwt: str
) -> Dict[UUID, ProviderKeyStatus]:
    """
    Get provider key status for multiple providers.
    
    Args:
        org_id: Organization UUID
        provider_ids: List of provider UUIDs to check
        user_jwt: User JWT token for RLS-safe queries
        
    Returns:
        Dict mapping provider_id to ProviderKeyStatus
    """
    # Use user-scoped Supabase client for RLS
    supabase = get_supabase_user_client(user_jwt)
    
    # Query api_keys with provider info
    result = supabase.table("api_keys").select(
        "provider_id, is_active, key_prefix, last_used_at"
    ).eq("organization_id", str(org_id)).in_("provider_id", [str(pid) for pid in provider_ids]).execute()
    
    # Build status map
    status_map = {}
    
    # Initialize all providers as missing
    for provider_id in provider_ids:
        status_map[provider_id] = ProviderKeyStatus(
            has_org_api_key=False,
            is_active=False,
            key_prefix=None,
            last_used_at=None
        )
    
    # Update with actual data
    if result.data:
        for key_data in result.data:
            provider_id = UUID(key_data["provider_id"])
            last_used_str = key_data.get("last_used_at")
            last_used_dt = None
            if last_used_str:
                try:
                    last_used_dt = datetime.fromisoformat(last_used_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            status_map[provider_id] = ProviderKeyStatus(
                has_org_api_key=True,
                is_active=key_data["is_active"],
                key_prefix=key_data.get("key_prefix"),
                last_used_at=last_used_dt
            )
    
    return status_map


async def require_active_key(
    org_id: UUID, 
    provider_id: UUID,
    user_jwt: str
) -> None:
    """
    Require that an organization has an active API key for a provider.
    
    Args:
        org_id: Organization UUID
        provider_id: Provider UUID
        user_jwt: User JWT token for RLS-safe queries
        
    Raises:
        HTTPException: OpenAI-style error if key is missing or inactive
    """
    # Use user-scoped Supabase client for RLS
    supabase = get_supabase_user_client(user_jwt)
    
    # Query for the specific provider key
    result = supabase.table("api_keys").select(
        "is_active"
    ).eq("organization_id", str(org_id)).eq("provider_id", str(provider_id)).execute()
    
    if not result.data:
        # No key found
        openai_error(
            400,
            "Provider key not found for organization",
            code="missing_org_api_key"
        )
    
    key_data = result.data[0]
    if not key_data["is_active"]:
        # Key exists but is inactive
        openai_error(
            400,
            "Provider key is disabled",
            code="disabled_org_api_key"
        )
    
    # Key exists and is active - return None (success)
    return None


async def get_provider_id_by_name(provider_name: str, user_jwt: str) -> Optional[UUID]:
    """
    Get provider ID by name.
    
    Args:
        provider_name: Provider name (e.g., "openai", "anthropic")
        user_jwt: User JWT token for RLS-safe queries
        
    Returns:
        Provider UUID or None if not found
    """
    # Use user-scoped Supabase client for RLS
    supabase = get_supabase_user_client(user_jwt)
    
    result = supabase.table("ai_providers").select(
        "id"
    ).eq("name", provider_name.lower()).execute()
    
    if result.data:
        return UUID(result.data[0]["id"])
    
    return None
