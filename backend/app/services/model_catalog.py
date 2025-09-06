from typing import Optional, Tuple
from app.core.supabase import get_supabase_service
from app.models.catalog import ResolvedProvider, ResolvedModel
from app.core.exceptions import InvalidRequestError, NotFoundError, PermissionError_

def get_provider_by_name(name: str) -> ResolvedProvider:
    """Get provider by name/slug and validate it's active."""
    sb = get_supabase_service()
    data = sb.table("ai_providers")\
        .select("id,name,display_name,is_active")\
        .eq("name", name)\
        .limit(1).execute().data
    
    if not data:
        # Provider slug not supported
        raise NotFoundError("Provider not supported", code="provider_not_supported", param="model")
    
    row = data[0]
    if not row.get("is_active", True):
        # Defined but disabled in catalog
        raise PermissionError_("Provider disabled", code="provider_disabled")
    
    return ResolvedProvider(**row)

def get_model_by_provider_and_name(provider_id: str, model_name: str) -> ResolvedModel:
    """Get model by provider ID and model name, validate it's active and chat type."""
    sb = get_supabase_service()
    cols = ",".join([
        "id","provider_id","model_name","display_name","model_type",
        "supports_streaming","supports_function_calling","supports_vision","supports_audio",
        "max_tokens","max_input_tokens","is_active"
    ])
    data = sb.table("ai_models")\
        .select(cols)\
        .eq("provider_id", provider_id)\
        .eq("model_name", model_name)\
        .limit(1).execute().data
    
    if not data:
        raise NotFoundError("Model not found", code="model_not_found", param="model")
    
    row = data[0]
    if not row.get("is_active", True):
        raise PermissionError_("Model disabled", code="model_disabled")
    
    if row.get("model_type") != "chat":  # MVP only chat.completions
        raise InvalidRequestError("Model type not supported for this endpoint", code="model_type_mismatch", param="model")
    
    # provider_name will be set by the caller
    return ResolvedModel(provider_name="", **row)
