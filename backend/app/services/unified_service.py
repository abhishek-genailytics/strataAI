"""
Unified chat service that can be used by both HTTP routes and in-process calls.
Extracted from unified_api.py to enable reuse by gateway bridge.
"""
from uuid import UUID
from typing import Optional
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.models.auth import CurrentCaller
from app.core.deps import validate_model
from app.services.adapter_factory import get_adapter
from app.services.provider_keys import get_active_api_key
from app.services.costing import compute_cost
from app.services.playground_logging import ensure_session, append_turn


class UnifiedChatService:
    """Service for unified chat completions that can be used by HTTP routes and in-process calls."""
    
    async def chat_completions_internal(
        self,
        organization_id: UUID,
        initiated_by_user_id: UUID,
        request: ChatCompletionRequest,
        x_session_id: Optional[str] = None,
    ) -> ChatCompletionResponse:
        """
        Internal chat completion logic that can be called from HTTP routes or in-process.
        
        Args:
            organization_id: The organization ID
            initiated_by_user_id: The user ID initiating the request
            request: The OpenAI-compatible chat completion request
            x_session_id: Optional session ID for playground logging
            
        Returns:
            ChatCompletionResponse: OpenAI-compatible response
        """
        # 1) Validate and resolve model
        resolved_model = await validate_model(request.model)
        
        # 2) Pick adapter
        adapter = get_adapter(resolved_model.provider_name)
        
        # 3) Load org-scoped provider key (throws OpenAI-style errors via middleware)
        # Special case: echo adapter doesn't need API keys
        if resolved_model.provider_name == "echo":
            api_key_id, plaintext_key = None, None
        else:
            api_key_id, plaintext_key = get_active_api_key(
                organization_id=organization_id,
                provider_id=resolved_model.provider_id
            )
        
        # 4) Call provider adapter
        resp = await adapter.chat_completion(
            organization_id=organization_id,
            request=request,
            model_name=resolved_model.model_name,
            api_key=plaintext_key,
        )
        
        # 5) Compute cost from usage and model pricing
        cost = compute_cost(
            usage=resp.usage,
            model_id=resolved_model.id,
            region=None  # MVP: default; plug header/org setting later
        )
        
        # 6) Playground session logging if session ID provided
        if x_session_id:
            assistant_text = resp.choices[0].message.content if resp.choices else ""
            
            # Pick the last user message in the request (the new turn)
            last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
            
            if last_user:
                session_id = ensure_session(
                    organization_id=organization_id,
                    user_id=initiated_by_user_id,
                    client_session_id=x_session_id,
                    default_title=f"{resolved_model.provider_name}/{resolved_model.model_name}",
                )
                append_turn(
                    session_id=session_id,
                    provider_id=resolved_model.provider_id,
                    model_id=resolved_model.id,
                    last_user_message=last_user,
                    assistant_text=assistant_text,
                    usage=resp.usage,
                    cost=cost,
                )
        
        return resp
