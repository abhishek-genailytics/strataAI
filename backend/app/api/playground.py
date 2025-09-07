"""
Playground-specific API endpoints that use direct Supabase authentication
and user's configured provider API keys without PAT complexity.
"""
from typing import List, Optional, AsyncGenerator, Dict, Any
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status, Response, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..core.config import get_settings
from ..models.organization import Organization
from ..models.playground_mode import PlaygroundRequestSource, PlaygroundSessionMeta
from ..models.playground_chat import PlaygroundChatCompletionRequest, PlaygroundChatCompletionResponse
from ..models.model_params import ModelParams, ChatCompletionWithParams
from ..services.user_model_prefs import user_model_prefs_service
from ..utils.supabase_client import get_supabase_user_client
from ..services.playground_service import PlaygroundProviderService
from ..utils.supabase_client import supabase_service
from ..errors.openai_envelope import openai_error

router = APIRouter(prefix="/playground", tags=["playground"])


# Legacy models removed - now using OpenAI-compatible models from playground_chat.py


class PlaygroundSessionCreate(BaseModel):
    title: Optional[str] = None
    provider: str
    model: str
    metadata: Optional[PlaygroundSessionMeta] = None


class PlaygroundSessionUpdate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[PlaygroundSessionMeta] = None


class PlaygroundSessionResponse(BaseModel):
    id: str
    title: str
    provider: str
    model: str
    metadata: PlaygroundSessionMeta
    created_at: str
    updated_at: str
    message_count: int = 0


class PlaygroundModelInfo(BaseModel):
    id: str  # Format: "provider/model"
    provider: str
    model: str
    display_name: str
    max_tokens: int
    supports_streaming: bool
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None


@router.get("/models", response_model=List[PlaygroundModelInfo])
async def get_playground_models(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get models available in playground based on user's configured API keys."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Get models for providers where user has active API keys
        # First get the API keys for this organization
        api_keys_result = supabase_service.table("api_keys").select(
            "provider_id"
        ).eq("organization_id", str(organization.id)).eq("is_active", True).execute()
        
        if not api_keys_result.data:
            return []
        
        provider_ids = [key['provider_id'] for key in api_keys_result.data]
        
        # Now get models for those providers
        result = supabase_service.table("ai_models").select(
            """
            model_name,
            display_name,
            max_tokens,
            supports_streaming,
            ai_providers(name, id),
            model_pricing(pricing_type, price_per_unit)
            """
        ).eq("is_active", True).in_("provider_id", provider_ids).execute()
        
        models = []
        if result.data:
            for model_data in result.data:
                provider_info = model_data.get('ai_providers')
                if not provider_info:
                    continue
                    
                provider_name = provider_info['name']
                
                # Calculate pricing
                input_cost = None
                output_cost = None
                if model_data.get('model_pricing'):
                    for pricing in model_data['model_pricing']:
                        if pricing['pricing_type'] == 'input':
                            input_cost = float(pricing['price_per_unit'])
                        elif pricing['pricing_type'] == 'output':
                            output_cost = float(pricing['price_per_unit'])
                
                models.append(PlaygroundModelInfo(
                    id=f"{provider_name}/{model_data['model_name']}",
                    provider=provider_name,
                    model=model_data['model_name'],
                    display_name=model_data['display_name'],
                    max_tokens=model_data['max_tokens'] or 4096,
                    supports_streaming=model_data['supports_streaming'] or False,
                    cost_per_1k_input_tokens=input_cost,
                    cost_per_1k_output_tokens=output_cost
                ))
        
        return models
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve playground models: {str(e)}"
        )


@router.post("/chat/completions", response_model=PlaygroundChatCompletionResponse)
async def playground_chat_completion(
    session_id: UUID,
    request: ChatCompletionWithParams,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    x_client_message_id: Optional[str] = Header(None, alias="X-Client-Message-ID"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Single playground chat completion endpoint with OpenAI-compatible interface.
    Routes between Gateway and Direct modes based on session metadata.
    Now supports parameter overrides and user preference persistence.
    
    Args:
        session_id: Required session ID to locate mode & persist messages
        request: Extended chat completion request with parameter overrides
        
    Request Headers:
        X-Session-ID: Session ID (optional, overrides path parameter)
        X-Client-Message-ID: Client-generated UUID for user message (optional)
        X-Idempotency-Key: Idempotency key for safe retries (optional)
        
    Request Body:
        messages: OpenAI-style message array
        model: Model ID in "provider/model" format
        params: Optional ModelParams object for parameter overrides
        save_params: Boolean to persist params as user defaults
        Direct parameter fields (temperature, max_tokens, etc.) also supported
        
    Returns:
        PlaygroundChatCompletionResponse: OpenAI-compatible response
        
    Response Headers:
        X-User-Message-ID: Server UUID for persisted user message
        X-Assistant-Message-ID: Server UUID for persisted assistant message
        X-Message-Index-Start: Starting message index for this exchange
        X-Stream-Disabled: 1 (if request contained stream=true, for parity with /v1)
    """
    if not organization:
        openai_error(400, "Organization context is required")
    
    settings = get_settings()
    
    try:
        # Use X-Session-ID header if provided, otherwise use path parameter
        effective_session_id = UUID(x_session_id) if x_session_id else session_id
        
        # Check if stream was requested (MVP: always disabled)
        stream_requested = request.stream
        
        # Get user-scoped Supabase client for parameter merging
        supabase_client = get_supabase_user_client(current_user.jwt_token)
        
        # Extract and merge parameters from request
        request_params = request.get_merged_params()
        
        # Merge parameters with proper precedence (request > session > user > system)
        merged_params = await user_model_prefs_service.merge_all_defaults(
            user_id=current_user.user_id,
            org_id=organization.id,
            model_id=request.model,
            session_id=effective_session_id,
            request_params=request_params,
            supabase_client=supabase_client
        )
        
        # Ensure Anthropic requirements
        if request.model.startswith("anthropic/"):
            merged_params = merged_params.ensure_anthropic_requirements()
        
        # Prepare headers for send pipeline
        from ..services.send_pipeline import SendHeaders
        headers = SendHeaders(
            session_id=x_session_id,
            client_message_id=x_client_message_id,
            idempotency_key=x_idempotency_key
        )
        
        # Convert to ChatCompletionRequest with merged parameters
        from ..models.openai_chat import ChatCompletionRequest, ChatMessage
        openai_request = ChatCompletionRequest(
            model=request.model,
            messages=[
                ChatMessage(role=msg.role, content=msg.content)
                for msg in request.messages
            ],
            temperature=merged_params.temperature,
            top_p=merged_params.top_p,
            max_tokens=merged_params.max_tokens,
            stop=merged_params.stop,
            presence_penalty=merged_params.presence_penalty,
            frequency_penalty=merged_params.frequency_penalty,
            stream=request.stream
        )
        
        # Call the send pipeline orchestration
        from ..services.send_pipeline import SendPipeline
        pipeline = SendPipeline()
        
        openai_response, send_context = await pipeline.run(
            session_id=effective_session_id,
            request=openai_request,
            user_ctx=current_user,
            organization_id=organization.id,
            headers=headers
        )
        
        # Optionally save parameters as user defaults
        if request.save_params and request_params:
            await user_model_prefs_service.upsert_user_defaults(
                user_id=current_user.user_id,
                org_id=organization.id,
                model_id=request.model,
                params=request_params
            )
        
        # Convert OpenAI response back to PlaygroundChatCompletionResponse
        chat_response = PlaygroundChatCompletionResponse.create(
            model=openai_response.model,
            content=openai_response.choices[0].message.content if openai_response.choices else "",
            prompt_tokens=openai_response.usage.prompt_tokens if openai_response.usage else 0,
            completion_tokens=openai_response.usage.completion_tokens if openai_response.usage else 0,
            finish_reason=openai_response.choices[0].finish_reason if openai_response.choices else "stop",
            response_id=openai_response.id
        )
        
        # Set PG-7 response headers
        response.headers["X-User-Message-ID"] = str(send_context.user_msg_id)
        response.headers["X-Assistant-Message-ID"] = str(send_context.assistant_msg_id)
        response.headers["X-Message-Index-Start"] = str(send_context.start_index)
        
        # Add optional response headers if enabled
        if settings.PLAYGROUND_RESP_HEADERS:
            response.headers["X-Playground-Session-ID"] = str(effective_session_id)
            if stream_requested:
                response.headers["X-Stream-Disabled"] = "1"
        elif stream_requested:
            # Always set X-Stream-Disabled per PG-7 spec
            response.headers["X-Stream-Disabled"] = "1"
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        # Convert any remaining errors to OpenAI format
        openai_error(500, f"Chat completion failed: {str(e)}")


@router.post("/sessions", response_model=PlaygroundSessionResponse)
async def create_playground_session(
    session_data: PlaygroundSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Create a new playground session with request source mode."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # Default metadata if not provided
        metadata = session_data.metadata or PlaygroundSessionMeta()
        
        # Validate that the chosen mode is valid
        if metadata.request_source not in [PlaygroundRequestSource.gateway, PlaygroundRequestSource.direct]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request_source. Must be 'gateway' or 'direct'"
            )
        
        # When mode is "gateway", verify org has an active provider key
        if metadata.request_source == PlaygroundRequestSource.gateway:
            provider_name = session_data.provider
            api_key = await PlaygroundProviderService.get_decrypted_api_key(
                organization.id, provider_name
            )
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No active API key configured for provider: {provider_name}. Gateway mode requires configured provider keys."
                )
        
        # Create session with metadata
        session_insert = {
            "user_id": str(current_user.id),
            "provider": session_data.provider,
            "model": session_data.model,
            "session_name": session_data.title or "New Chat",
            "metadata": metadata.dict()
        }
        
        result = supabase_service.table("chat_sessions").insert(session_insert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playground session"
            )
        
        session = result.data[0]
        return PlaygroundSessionResponse(
            id=session["id"],
            title=session["session_name"],
            provider=session["provider"],
            model=session["model"],
            metadata=PlaygroundSessionMeta(**session.get("metadata", {})),
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create playground session: {str(e)}"
        )


@router.put("/sessions/{session_id}", response_model=PlaygroundSessionResponse)
async def update_playground_session(
    session_id: str,
    session_update: PlaygroundSessionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Update playground session metadata including request source mode."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        # First verify session belongs to user
        session_result = supabase_service.table("chat_sessions").select(
            "*"
        ).eq("id", session_id).eq("user_id", str(current_user.id)).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playground session not found"
            )
        
        current_session = session_result.data[0]
        
        # Prepare update data
        update_data = {"updated_at": "now()"}
        
        if session_update.title is not None:
            update_data["session_name"] = session_update.title
        
        if session_update.metadata is not None:
            # Validate request source if being updated
            if session_update.metadata.request_source not in [PlaygroundRequestSource.gateway, PlaygroundRequestSource.direct]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request_source. Must be 'gateway' or 'direct'"
                )
            
            # When switching to gateway mode, verify org has an active provider key
            if session_update.metadata.request_source == PlaygroundRequestSource.gateway:
                provider_name = current_session["provider"]
                api_key = await PlaygroundProviderService.get_decrypted_api_key(
                    organization.id, provider_name
                )
                if not api_key:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No active API key configured for provider: {provider_name}. Gateway mode requires configured provider keys."
                    )
            
            # Merge with existing metadata
            existing_metadata = current_session.get("metadata", {})
            new_metadata = {**existing_metadata, **session_update.metadata.dict(exclude_unset=True)}
            update_data["metadata"] = new_metadata
        
        # Update session
        result = supabase_service.table("chat_sessions").update(update_data).eq(
            "id", session_id
        ).eq("user_id", str(current_user.id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update playground session"
            )
        
        updated_session = result.data[0]
        
        # Get message count
        message_count_result = supabase_service.table("chat_messages").select(
            "id", count="exact"
        ).eq("session_id", session_id).execute()
        
        message_count = message_count_result.count if message_count_result.count is not None else 0
        
        return PlaygroundSessionResponse(
            id=updated_session["id"],
            title=updated_session["session_name"],
            provider=updated_session["provider"],
            model=updated_session["model"],
            metadata=PlaygroundSessionMeta(**updated_session.get("metadata", {})),
            created_at=updated_session["created_at"],
            updated_at=updated_session["updated_at"],
            message_count=message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update playground session: {str(e)}"
        )


@router.get("/api-keys/status")
async def get_api_keys_status(
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get status of configured API keys for playground."""
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    
    try:
        result = supabase_service.table("api_keys").select(
            """
            name,
            is_active,
            last_used_at,
            ai_providers(name, display_name)
            """
        ).eq("organization_id", str(organization.id)).execute()
        
        return {
            "api_keys": [
                {
                    "provider": key['ai_providers']['name'],
                    "provider_display_name": key['ai_providers']['display_name'],
                    "name": key['name'],
                    "is_active": key['is_active'],
                    "last_used_at": key['last_used_at']
                }
                for key in result.data
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API keys status: {str(e)}"
        )
