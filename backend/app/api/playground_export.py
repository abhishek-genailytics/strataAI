"""
Playground export API endpoints for PG-14.
Provides one-click cURL generation and JSON transcript downloads.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..core.deps import get_current_user, CurrentUser
from ..models.playground_export import ExportRequest, ExportResponse, ExportParams
from ..services.export_builder import ExportBuilder
from ..services.send_pipeline import assemble_openai_messages
from ..services.user_model_prefs import merge_all_defaults
from ..utils.supabase_client import get_supabase_user_client
from ..errors.openai_envelope import (
    session_not_found_error,
    invalid_request_error,
    openai_error
)


router = APIRouter()


@router.post("/sessions/{session_id}/export")
async def export_session(
    session_id: UUID,
    request: ExportRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> ExportResponse:
    """
    Export playground session as cURL command or JSON transcript.
    
    Supports:
    - curl_unified: cURL for /v1/chat/completions with PAT auth
    - curl_provider: cURL for native provider API with placeholder keys
    - json_transcript: Complete session export with usage data
    
    All exports use the same message assembly as the send pipeline.
    """
    try:
        # Verify session ownership and get session data
        session_data = await _verify_session_ownership(session_id, current_user)
        
        # Initialize export builder
        export_builder = ExportBuilder(current_user.jwt_token)
        
        # Assemble messages using shared pipeline logic
        assembled_request = await assemble_openai_messages(
            session_id=session_id,
            ui_messages=None,  # Fetch from DB
            override_system=request.options.override_system,
            limit_turns=request.options.limit_turns,
            user_jwt=current_user.jwt_token
        )
        
        # Parse model information
        model_id = f"{session_data['provider_name']}/{session_data['model_name']}"
        provider_name = session_data['provider_name']
        model_suffix = session_data['model_name']
        
        # Merge parameters using same rules as send pipeline
        merged_params = await _merge_export_parameters(
            session_id=session_id,
            user_id=current_user.user_id,
            organization_id=current_user.organization_id,
            session_data=session_data,
            request_params=request.options.params or {},
            jwt_token=current_user.jwt_token
        )
        
        # Generate export based on type
        if request.type == "curl_unified":
            content = export_builder.build_curl_unified(
                api_base="https://api.strataai.com",  # TODO: Make configurable
                pat_placeholder="$STRATA_PAT",
                model_slash_id=model_id,
                messages=assembled_request.messages,
                params=merged_params,
                organization_id=str(current_user.organization_id)
            )
            
            return ExportResponse(
                mime="text/plain",
                filename=None,
                content=content
            )
        
        elif request.type == "curl_provider":
            # Use provider override if specified, otherwise use session provider
            target_provider = request.options.provider or provider_name
            placeholders = export_builder.get_api_key_placeholders()
            
            content = export_builder.build_curl_provider(
                provider=target_provider,
                messages=assembled_request.messages,
                params=merged_params,
                model_suffix=model_suffix,
                placeholders=placeholders
            )
            
            return ExportResponse(
                mime="text/plain",
                filename=None,
                content=content
            )
        
        elif request.type == "json_transcript":
            transcript = await export_builder.build_json_transcript(
                session_id=session_id,
                user_id=current_user.user_id,
                messages=assembled_request.messages,
                limit_turns=request.options.limit_turns,
                include_system=request.options.include_system
            )
            
            # Convert to JSON string
            import json
            content = json.dumps(transcript.dict(), indent=2, default=str)
            
            return ExportResponse(
                mime="application/json",
                filename=f"playground-session-{session_id}.json",
                content=content
            )
        
        else:
            invalid_request_error(f"Unsupported export type: {request.type}")
    
    except HTTPException:
        raise
    except Exception as e:
        openai_error(500, f"Export failed: {str(e)}", code="export_error")


async def _verify_session_ownership(
    session_id: UUID, 
    current_user: CurrentUser
) -> Dict[str, Any]:
    """
    Verify session ownership and return session metadata.
    
    Returns:
        Dict with session data including provider_name and model_name
    """
    sb = get_supabase_user_client(current_user.jwt_token)
    
    # Fetch session with provider and model info
    result = sb.table("chat_sessions").select(
        """
        id, user_id, title, provider_id, model_id, created_at, updated_at, metadata,
        ai_providers!inner(name),
        ai_models!inner(name)
        """
    ).eq("id", str(session_id)).execute()
    
    if not result.data:
        session_not_found_error(str(session_id))
    
    session_row = result.data[0]
    
    # Verify ownership
    if session_row["user_id"] != str(current_user.user_id):
        session_not_found_error(str(session_id))
    
    # Extract provider and model names from joined data
    provider_name = session_row["ai_providers"]["name"]
    model_name = session_row["ai_models"]["name"]
    
    return {
        **session_row,
        "provider_name": provider_name,
        "model_name": model_name
    }


async def _merge_export_parameters(
    session_id: UUID,
    user_id: UUID,
    organization_id: UUID,
    session_data: Dict[str, Any],
    request_params: Dict[str, Any],
    jwt_token: str
) -> ExportParams:
    """
    Merge parameters using same precedence as send pipeline:
    request overrides → session defaults → user defaults → org defaults → system defaults
    """
    try:
        # Get session model info
        provider_name = session_data["provider_name"]
        model_name = session_data["model_name"]
        model_id = f"{provider_name}/{model_name}"
        
        # Use the same parameter merging logic as send pipeline
        merged_defaults = await merge_all_defaults(
            user_id=user_id,
            organization_id=organization_id,
            model_id=model_id,
            session_id=session_id,
            jwt_token=jwt_token
        )
        
        # Apply request-level overrides
        final_params = {**merged_defaults}
        final_params.update(request_params)
        
        # Convert to ExportParams with validation
        return ExportParams(
            temperature=final_params.get("temperature"),
            max_tokens=final_params.get("max_tokens"),
            top_p=final_params.get("top_p"),
            stop=final_params.get("stop"),
            presence_penalty=final_params.get("presence_penalty"),
            frequency_penalty=final_params.get("frequency_penalty")
        )
        
    except Exception as e:
        # Fallback to basic parameters if merging fails
        return ExportParams(
            temperature=request_params.get("temperature", 0.7),
            max_tokens=request_params.get("max_tokens", 512),
            top_p=request_params.get("top_p", 1.0),
            stop=request_params.get("stop"),
            presence_penalty=request_params.get("presence_penalty", 0.0),
            frequency_penalty=request_params.get("frequency_penalty", 0.0)
        )
