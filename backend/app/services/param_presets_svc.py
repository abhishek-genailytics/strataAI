"""
Service for managing parameter presets and applying them to sessions or user defaults.
"""

from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID

from app.config.presets import PRESETS, STOP_SNIPPETS, ParamPreset
from app.models.model_params import ModelParams
from app.utils.supabase_client import get_supabase_service_client
from app.errors.openai_envelope import not_found_error, invalid_request_error


def list_presets() -> Tuple[List[ParamPreset], List[ParamPreset]]:
    """Return all available presets and stop snippets."""
    return PRESETS, STOP_SNIPPETS


def find_preset_by_id(preset_id: str) -> Optional[ParamPreset]:
    """Find a preset by ID in either PRESETS or STOP_SNIPPETS."""
    for preset in PRESETS + STOP_SNIPPETS:
        if preset.id == preset_id:
            return preset
    return None


async def apply_preset_to_session(
    session_id: UUID,
    user_id: UUID,
    org_id: UUID,
    preset_id: str,
    merge: bool = True
) -> ModelParams:
    """
    Apply a preset to session metadata.default_params.
    
    Args:
        session_id: Session UUID
        user_id: User UUID (for ownership validation)
        org_id: Organization UUID (for RLS)
        preset_id: Preset ID to apply
        merge: If True, merge with existing params; if False, replace
        
    Returns:
        Updated ModelParams after applying preset
        
    Raises:
        ValueError: If preset not found or session not owned by user
    """
    # Find the preset
    preset = find_preset_by_id(preset_id)
    if not preset:
        raise ValueError(f"Preset '{preset_id}' not found")
    
    supabase = get_supabase_service_client()
    
    # Get current session and validate ownership
    session_result = supabase.table("chat_sessions").select(
        "id, user_id, metadata"
    ).eq("id", str(session_id)).eq("user_id", str(user_id)).single().execute()
    
    if not session_result.data:
        raise ValueError("Session not found or not owned by user")
    
    session_data = session_result.data
    current_metadata = session_data.get("metadata", {})
    current_default_params = current_metadata.get("default_params", {})
    
    # Convert current params to ModelParams object
    current_params = ModelParams.from_dict(current_default_params)
    
    # Create preset params
    preset_params = ModelParams.from_dict(preset.params)
    
    # Merge or replace
    if merge:
        updated_params = current_params.merge_with(preset_params)
    else:
        # For replace, start with system defaults and apply preset
        system_defaults = ModelParams.get_system_defaults()
        updated_params = system_defaults.merge_with(preset_params)
    
    # Update session metadata
    updated_metadata = {
        **current_metadata,
        "default_params": updated_params.to_dict(exclude_none=False)
    }
    
    supabase.table("chat_sessions").update({
        "metadata": updated_metadata
    }).eq("id", str(session_id)).execute()
    
    return updated_params


async def apply_preset_to_user_defaults(
    user_id: UUID,
    org_id: UUID,
    model_id: str,
    preset_id: str,
    merge: bool = True
) -> ModelParams:
    """
    Apply a preset to user model configuration defaults.
    
    Args:
        user_id: User UUID
        org_id: Organization UUID
        model_id: Model ID (e.g., "openai/gpt-4o-mini")
        preset_id: Preset ID to apply
        merge: If True, merge with existing config; if False, replace
        
    Returns:
        Updated ModelParams after applying preset
        
    Raises:
        ValueError: If preset not found
    """
    # Find the preset
    preset = find_preset_by_id(preset_id)
    if not preset:
        raise ValueError(f"Preset '{preset_id}' not found")
    
    supabase = get_supabase_service_client()
    
    # Get current user model configuration
    config_result = supabase.table("user_model_configurations").select(
        "configuration"
    ).eq("user_id", str(user_id)).eq("organization_id", str(org_id)).eq(
        "model_id", model_id
    ).single().execute()
    
    current_config = {}
    if config_result.data:
        current_config = config_result.data.get("configuration", {})
    
    # Convert current config to ModelParams
    current_params = ModelParams.from_dict(current_config)
    
    # Create preset params
    preset_params = ModelParams.from_dict(preset.params)
    
    # Merge or replace
    if merge:
        updated_params = current_params.merge_with(preset_params)
    else:
        # For replace, start with system defaults and apply preset
        system_defaults = ModelParams.get_system_defaults()
        updated_params = system_defaults.merge_with(preset_params)
    
    # Upsert user model configuration
    config_data = {
        "user_id": str(user_id),
        "organization_id": str(org_id),
        "model_id": model_id,
        "configuration": updated_params.to_dict(exclude_none=False),
        "is_default_for_user": False  # Preserve existing default status
    }
    
    supabase.table("user_model_configurations").upsert(
        config_data,
        on_conflict="user_id,organization_id,model_id"
    ).execute()
    
    return updated_params


async def update_session_params_direct(
    session_id: UUID,
    user_id: UUID,
    org_id: UUID,
    params: ModelParams
) -> ModelParams:
    """
    Directly update session default parameters (no preset).
    
    Args:
        session_id: Session UUID
        user_id: User UUID (for ownership validation)
        org_id: Organization UUID (for RLS)
        params: New parameters to set
        
    Returns:
        Updated ModelParams
        
    Raises:
        ValueError: If session not found or not owned by user
    """
    supabase = get_supabase_service_client()
    
    # Get current session and validate ownership
    session_result = supabase.table("chat_sessions").select(
        "id, user_id, metadata"
    ).eq("id", str(session_id)).eq("user_id", str(user_id)).single().execute()
    
    if not session_result.data:
        raise ValueError("Session not found or not owned by user")
    
    session_data = session_result.data
    current_metadata = session_data.get("metadata", {})
    
    # Update session metadata with new params
    updated_metadata = {
        **current_metadata,
        "default_params": params.to_dict(exclude_none=False)
    }
    
    supabase.table("chat_sessions").update({
        "metadata": updated_metadata
    }).eq("id", str(session_id)).execute()
    
    return params


async def reset_session_params(
    session_id: UUID,
    user_id: UUID,
    org_id: UUID
) -> ModelParams:
    """
    Reset session parameters to system defaults.
    
    Args:
        session_id: Session UUID
        user_id: User UUID (for ownership validation)
        org_id: Organization UUID (for RLS)
        
    Returns:
        System default ModelParams
        
    Raises:
        ValueError: If session not found or not owned by user
    """
    supabase = get_supabase_service_client()
    
    # Get current session and validate ownership
    session_result = supabase.table("chat_sessions").select(
        "id, user_id, metadata"
    ).eq("id", str(session_id)).eq("user_id", str(user_id)).single().execute()
    
    if not session_result.data:
        raise ValueError("Session not found or not owned by user")
    
    session_data = session_result.data
    current_metadata = session_data.get("metadata", {})
    
    # Remove default_params from metadata
    updated_metadata = {k: v for k, v in current_metadata.items() if k != "default_params"}
    
    supabase.table("chat_sessions").update({
        "metadata": updated_metadata
    }).eq("id", str(session_id)).execute()
    
    return ModelParams.get_system_defaults()


def validate_params_for_model(params: ModelParams, model_id: str) -> ModelParams:
    """
    Validate and adjust parameters for specific model requirements.
    
    Args:
        params: Parameters to validate
        model_id: Model ID (e.g., "openai/gpt-4o-mini")
        
    Returns:
        Validated and potentially adjusted parameters
    """
    # Extract provider from model_id
    if "/" not in model_id:
        return params
    
    provider, _ = model_id.split("/", 1)
    
    # Apply provider-specific requirements
    if provider == "anthropic":
        return params.ensure_anthropic_requirements()
    
    return params
