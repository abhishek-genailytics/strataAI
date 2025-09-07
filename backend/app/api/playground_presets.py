"""
API endpoints for playground parameter presets and stop sequences.
"""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.deps import get_current_user, get_organization_context, CurrentUser
from app.models.model_params import ModelParams
from app.services import param_presets_svc
from app.config.presets import ParamPreset
from app.errors.openai_envelope import (
    invalid_request_error,
    not_found_error,
    openai_error
)

router = APIRouter(prefix="/playground", tags=["playground-presets"])


class PresetListResponse(BaseModel):
    """Response for listing available presets."""
    param_presets: List[Dict[str, Any]]
    stop_snippets: List[Dict[str, Any]]


class ApplyPresetRequest(BaseModel):
    """Request to apply a preset to session or user defaults."""
    preset_id: str = Field(..., description="ID of preset to apply")
    kind: str = Field("params", description="Type of preset: 'params' or 'stop'")
    scope: str = Field("session", description="Scope: 'session' or 'user'")
    merge: str = Field("merge", description="Mode: 'merge' or 'replace'")
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        if v not in ["params", "stop"]:
            raise ValueError("kind must be 'params' or 'stop'")
        return v
    
    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v):
        if v not in ["session", "user"]:
            raise ValueError("scope must be 'session' or 'user'")
        return v
    
    @field_validator('merge')
    @classmethod
    def validate_merge(cls, v):
        if v not in ["merge", "replace"]:
            raise ValueError("merge must be 'merge' or 'replace'")
        return v


class UpdateParamsRequest(BaseModel):
    """Request to directly update session parameters."""
    temperature: float = Field(None, ge=0.0, le=2.0)
    max_tokens: int = Field(None, ge=1)
    top_p: float = Field(None, ge=0.0, le=1.0)
    presence_penalty: float = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(None, ge=-2.0, le=2.0)
    stop: List[str] = Field(None, max_items=4)


class PresetApplyResponse(BaseModel):
    """Response after applying preset."""
    success: bool
    updated_params: Dict[str, Any]
    message: str


def _preset_to_dict(preset: ParamPreset) -> Dict[str, Any]:
    """Convert ParamPreset to dictionary for API response."""
    return {
        "id": preset.id,
        "label": preset.label,
        "description": preset.description,
        "params": preset.params
    }


@router.get("/presets", response_model=PresetListResponse)
async def list_presets(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all available parameter presets and stop snippets.
    """
    try:
        param_presets, stop_snippets = param_presets_svc.list_presets()
        
        return PresetListResponse(
            param_presets=[_preset_to_dict(p) for p in param_presets],
            stop_snippets=[_preset_to_dict(s) for s in stop_snippets]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/presets/apply", response_model=PresetApplyResponse)
async def apply_preset_to_session(
    session_id: UUID,
    request: ApplyPresetRequest,
    current_user: CurrentUser = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context)
):
    """
    Apply a preset to session defaults or user model configuration.
    """
    try:
        org_id = UUID(org_context["organization_id"])
        merge_mode = request.merge == "merge"
        
        if request.scope == "session":
            # Apply to session metadata.default_params
            updated_params = await param_presets_svc.apply_preset_to_session(
                session_id=session_id,
                user_id=current_user.id,
                org_id=org_id,
                preset_id=request.preset_id,
                merge=merge_mode
            )
            scope_msg = "session defaults"
        else:
            # Apply to user model configuration
            # We need the model_id from the session
            from app.utils.supabase_client import get_supabase_service_client
            supabase = get_supabase_service_client()
            
            session_result = supabase.table("chat_sessions").select(
                "provider_id, model_id"
            ).eq("id", str(session_id)).eq("user_id", str(current_user.id)).single().execute()
            
            if not session_result.data:
                raise HTTPException(
                    status_code=404,
                    detail=not_found_error("Session not found or not owned by user")
                )
            
            model_id = f"{session_result.data['provider_id']}/{session_result.data['model_id']}"
            
            updated_params = await param_presets_svc.apply_preset_to_user_defaults(
                user_id=current_user.id,
                org_id=org_id,
                model_id=model_id,
                preset_id=request.preset_id,
                merge=merge_mode
            )
            scope_msg = f"user defaults for {model_id}"
        
        return PresetApplyResponse(
            success=True,
            updated_params=updated_params.to_dict(),
            message=f"Applied preset '{request.preset_id}' to {scope_msg}"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=invalid_request_error(str(e))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/params", response_model=PresetApplyResponse)
async def update_session_params(
    session_id: UUID,
    request: UpdateParamsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context)
):
    """
    Directly update session parameter defaults (no preset).
    """
    try:
        org_id = UUID(org_context["organization_id"])
        
        # Convert request to ModelParams (only non-None fields)
        params_dict = {k: v for k, v in request.model_dump().items() if v is not None}
        params = ModelParams.from_dict(params_dict)
        
        updated_params = await param_presets_svc.update_session_params_direct(
            session_id=session_id,
            user_id=current_user.id,
            org_id=org_id,
            params=params
        )
        
        return PresetApplyResponse(
            success=True,
            updated_params=updated_params.to_dict(),
            message="Updated session parameter defaults"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=invalid_request_error(str(e))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/params/reset", response_model=PresetApplyResponse)
async def reset_session_params(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    org_context: dict = Depends(get_organization_context)
):
    """
    Reset session parameters to system defaults.
    """
    try:
        org_id = UUID(org_context["organization_id"])
        
        system_defaults = await param_presets_svc.reset_session_params(
            session_id=session_id,
            user_id=current_user.id,
            org_id=org_id
        )
        
        return PresetApplyResponse(
            success=True,
            updated_params=system_defaults.to_dict(),
            message="Reset session parameters to system defaults"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=invalid_request_error(str(e))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
