"""
Playground actions API endpoints for regenerate functionality.
"""

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..core.deps import get_current_user
from ..models.model_params import RegenerateRequest, ModelParams
from ..core.deps import CurrentUser
from ..services.send_pipeline import SendPipeline
from ..services.user_model_prefs import user_model_prefs_service
from ..utils.supabase_client import get_supabase_user_client
from ..errors.openai_envelope import invalid_request_error, not_found_error


router = APIRouter()


@router.post("/playground/sessions/{session_id}/regenerate")
async def regenerate_message(
    session_id: UUID,
    request: RegenerateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Regenerate the last assistant message or a specific assistant message.
    
    Flow:
    1. Load session and validate ownership
    2. Find target assistant message and preceding user message
    3. Build OpenAI-style request with conversation history up to that point
    4. Merge parameters with proper precedence
    5. Call SendPipeline.run() with new idempotency key
    6. Optionally save parameters as user defaults
    7. Return OpenAI-compatible response
    """
    try:
        # Get user-scoped Supabase client for RLS
        supabase_client = get_supabase_user_client(current_user.jwt_token)
        
        # 1. Load session and validate ownership
        session_response = supabase_client.table("chat_sessions").select(
            "id, user_id, organization_id, provider_id, model_id, metadata"
        ).eq("id", str(session_id)).limit(1).execute()
        
        if not session_response.data:
            raise HTTPException(
                status_code=404,
                detail=not_found_error("Session not found")
            )
        
        session = session_response.data[0]
        
        # Validate ownership (RLS should handle this, but double-check)
        if session["user_id"] != str(current_user.user_id):
            raise HTTPException(
                status_code=404,
                detail=not_found_error("Session not found")
            )
        
        # Extract model information
        model_id = session["model_id"]  # Format: "provider/model"
        if not model_id or "/" not in model_id:
            raise HTTPException(
                status_code=400,
                detail=invalid_request_error("Session has invalid model_id format")
            )
        
        # 2. Find target assistant message and preceding conversation
        if request.target == "last":
            # Find the last assistant message
            messages_response = supabase_client.table("chat_messages").select(
                "id, message_index, role, content, created_at"
            ).eq(
                "session_id", str(session_id)
            ).order(
                "message_index", desc=True
            ).limit(1).execute()
            
            if not messages_response.data:
                raise HTTPException(
                    status_code=400,
                    detail=invalid_request_error("Nothing to regenerate - no messages in session")
                )
            
            last_message = messages_response.data[0]
            if last_message["role"] != "assistant":
                raise HTTPException(
                    status_code=400,
                    detail=invalid_request_error("Nothing to regenerate - last message is not from assistant")
                )
            
            target_message_index = last_message["message_index"]
        else:
            # Find specific assistant message by ID
            target_response = supabase_client.table("chat_messages").select(
                "id, message_index, role, session_id"
            ).eq("id", request.target).limit(1).execute()
            
            if not target_response.data:
                raise HTTPException(
                    status_code=404,
                    detail=not_found_error("Target message not found")
                )
            
            target_message = target_response.data[0]
            
            # Validate it belongs to this session
            if target_message["session_id"] != str(session_id):
                raise HTTPException(
                    status_code=404,
                    detail=not_found_error("Target message not found")
                )
            
            # Validate it's an assistant message
            if target_message["role"] != "assistant":
                raise HTTPException(
                    status_code=400,
                    detail=invalid_request_error("Target message is not from assistant")
                )
            
            target_message_index = target_message["message_index"]
        
        # Get all messages up to (but not including) the target assistant message
        history_response = supabase_client.table("chat_messages").select(
            "id, message_index, role, content"
        ).eq(
            "session_id", str(session_id)
        ).lt(
            "message_index", target_message_index
        ).order("message_index").execute()
        
        if not history_response.data:
            raise HTTPException(
                status_code=400,
                detail=invalid_request_error("Nothing to regenerate - no conversation history")
            )
        
        # Find the last user message in the history
        user_messages = [msg for msg in history_response.data if msg["role"] == "user"]
        if not user_messages:
            raise HTTPException(
                status_code=400,
                detail=invalid_request_error("Nothing to regenerate - no user message found")
            )
        
        # 3. Build OpenAI-style messages array
        openai_messages = []
        for msg in history_response.data:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # 4. Merge parameters with proper precedence
        merged_params = await user_model_prefs_service.merge_all_defaults(
            user_id=current_user.user_id,
            org_id=current_user.organization_id,
            model_id=model_id,
            session_id=session_id,
            request_params=request.params,
            supabase_client=supabase_client
        )
        
        # Ensure Anthropic requirements
        if model_id.startswith("anthropic/"):
            merged_params = merged_params.ensure_anthropic_requirements()
        
        # 5. Build OpenAI-style request body
        openai_request = {
            "model": model_id,
            "messages": openai_messages,
            "stream": False,  # MVP: no streaming for regenerate
            **merged_params.to_dict(exclude_none=True)
        }
        
        # Generate new idempotency key for regeneration
        idempotency_key = str(uuid.uuid4())
        
        # 6. Call SendPipeline with regeneration context
        send_pipeline = SendPipeline()
        response = await send_pipeline.run_regenerate(
            session_id=session_id,
            request_body=openai_request,
            idempotency_key=idempotency_key,
            user_id=current_user.user_id,
            org_id=current_user.organization_id,
            supabase_client=supabase_client
        )
        
        # 7. Optionally save parameters as user defaults
        if request.save_params and request.params:
            await user_model_prefs_service.upsert_user_defaults(
                user_id=current_user.user_id,
                org_id=current_user.organization_id,
                model_id=model_id,
                params=request.params
            )
        
        # Return OpenAI-compatible response with headers
        return JSONResponse(
            content=response["body"],
            headers=response.get("headers", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in regenerate_message: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": "Internal server error", "type": "internal_error"}}
        )
