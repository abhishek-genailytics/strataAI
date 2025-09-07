"""
Send pipeline orchestration for playground chat completions.
Implements PG-9 specification with Gateway/Direct mode routing, persistence, and analytics.
"""
import time
from typing import Dict, Any, Optional, Tuple, NamedTuple
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from ..core.deps import CurrentUser
from ..models.openai_chat import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice, ChatCompletionUsage
from ..models.playground_mode import PlaygroundRequestSource, PlaygroundSessionMeta
from ..models.playground_session import MessageDraft
from ..services.gateway_bridge import GatewayBridge
from ..services.key_preflight import require_active_key, get_provider_id_by_name
from ..services.message_indexer import next_index, append_messages
from ..services.analytics_logger import AnalyticsLogger
from ..services.adapter_factory import get_adapter
from ..utils.supabase_client import supabase_service, get_supabase_user_client
from ..utils.idempotency import find_prior_result, get_token_usage_for_message
from ..errors.openai_envelope import (
    invalid_model_format_error,
    model_not_found_error,
    session_not_found_error,
    openai_error,
    server_error
)


class SendHeaders(NamedTuple):
    """Headers for send pipeline requests."""
    session_id: Optional[str] = None
    client_message_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class SendContext(NamedTuple):
    """Context returned from send pipeline for response headers."""
    user_msg_id: UUID
    assistant_msg_id: UUID
    start_index: int
    usage: Optional[ChatCompletionUsage] = None
    provider_request_id: Optional[str] = None


class SendPipeline:
    """
    Orchestrates the full playground send pipeline with Gateway/Direct mode routing,
    persistence, analytics, and OpenAI-compatible response normalization.
    """
    
    def __init__(
        self,
        gateway_bridge: Optional[GatewayBridge] = None,
        analytics_logger: Optional[AnalyticsLogger] = None
    ):
        self.gateway_bridge = gateway_bridge or GatewayBridge()
        self.analytics_logger = analytics_logger or AnalyticsLogger()
        # Using adapter factory function instead of class
    
    async def run(
        self,
        *,
        session_id: UUID,
        request: ChatCompletionRequest,
        user_ctx: CurrentUser,
        organization_id: UUID,
        headers: SendHeaders
    ) -> Tuple[ChatCompletionResponse, SendContext]:
        """
        Orchestrates the complete send pipeline according to PG-9 specification.
        
        Steps:
        1. Load session + mode
        2. Parse/validate model id
        3. Idempotency short-circuit
        4. Persist user turn (optimistic)
        5. Provider key preflight
        6. Dispatch (Gateway/Direct)
        7. Persist assistant + token usage
        8. Analytics log
        9. Return OpenAI-normalized response + headers
        
        Args:
            session_id: Playground session UUID
            request: OpenAI-style chat completion request
            user_ctx: Current user context with JWT
            organization_id: Organization UUID
            headers: Request headers (X-Session-ID, X-Client-Message-ID, X-Idempotency-Key)
            
        Returns:
            Tuple of (ChatCompletionResponse, SendContext)
        """
        start_time = time.time()
        
        try:
            # Step 1: Load session + mode
            session_data, request_source = await self._load_session_and_mode(
                session_id, user_ctx
            )
            
            # Step 2: Parse/validate model id
            provider_name, model_name, provider_id = await self._parse_and_validate_model(
                request.model, user_ctx.jwt_token
            )
            
            # Check for idempotent retry
            if headers.idempotency_key:
                prior_result = await find_prior_result(
                    organization_id, headers.idempotency_key
                )
                if prior_result:
                    # Return cached response
                    return prior_result["response"], SendContext(
                        user_msg_id=prior_result["user_message_id"],
                        assistant_msg_id=prior_result["assistant_message_id"],
                        start_index=prior_result["start_index"],
                        usage=prior_result["usage"],
                        provider_request_id=prior_result["provider_request_id"]
                    )          
            
            # Step 3: Idempotency short-circuit
            if headers.idempotency_key:
                prior_result = await self._check_idempotency(
                    session_id, headers.idempotency_key, request.model
                )
                if prior_result:
                    return prior_result
            
            # Step 4: Persist user turn (optimistic)
            user_msg_id, start_index = await self._persist_user_message(
                session_id, request, headers
            )
            
            # Step 5: Provider key preflight
            await self._provider_key_preflight(
                organization_id, provider_id, user_ctx.jwt_token
            )
            
            # Step 6: Dispatch (Gateway/Direct mode)
            response_data, provider_request_id = await self._dispatch_completion(
                request_source, organization_id, user_ctx.id, request, 
                provider_name, model_name, str(session_id)
            )
            
            # Step 7: Persist assistant + token usage
            assistant_msg_id, usage = await self._persist_assistant_response(
                session_id, response_data, headers.idempotency_key, provider_request_id
            )
            
            # Step 8: Analytics log
            duration_ms = int((time.time() - start_time) * 1000)
            await self._log_analytics(
                organization_id, user_ctx.id, session_id, request.model,
                provider_id, provider_request_id, usage, duration_ms
            )
            
            # Step 9: Return OpenAI-normalized response + headers
            response = self._build_openai_response(
                request.model, response_data, usage
            )
            
            context = SendContext(
                user_msg_id=user_msg_id,
                assistant_msg_id=assistant_msg_id,
                start_index=start_index,
                usage=usage,
                provider_request_id=provider_request_id
            )
            
            return response, context
            
        except Exception as e:
            # Log failed request for analytics
            duration_ms = int((time.time() - start_time) * 1000)
            await self._log_failed_request(
                organization_id, user_ctx.id, session_id, request.model, 
                duration_ms, str(e)
            )
            
            # Re-raise with proper error formatting
            if hasattr(e, 'status_code'):
                raise e  # Already an OpenAI-formatted error
            else:
                server_error(f"Send pipeline failed: {str(e)}")
    
    async def run_regenerate(
        self,
        *,
        session_id: UUID,
        request_body: Dict[str, Any],
        idempotency_key: str,
        user_id: UUID,
        org_id: UUID,
        supabase_client
    ) -> Dict[str, Any]:
        """
        Run regeneration using the same send pipeline logic.
        This is a thin wrapper that converts the request and calls run().
        
        Args:
            session_id: Session UUID
            request_body: OpenAI-style request body dict
            idempotency_key: New idempotency key for regeneration
            user_id: User UUID
            org_id: Organization UUID
            supabase_client: User-scoped Supabase client
            
        Returns:
            Dict with "body" (OpenAI response) and "headers" keys
        """
        try:
            # Convert request body to ChatCompletionRequest
            from ..models.openai_chat import ChatCompletionRequest, ChatMessage
            
            messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in request_body.get("messages", [])
            ]
            
            request = ChatCompletionRequest(
                model=request_body["model"],
                messages=messages,
                temperature=request_body.get("temperature"),
                top_p=request_body.get("top_p"),
                max_tokens=request_body.get("max_tokens"),
                stop=request_body.get("stop"),
                presence_penalty=request_body.get("presence_penalty"),
                frequency_penalty=request_body.get("frequency_penalty"),
                stream=request_body.get("stream", False)
            )
            
            # Create user context (simplified for regeneration)
            user_ctx = CurrentUser(
                user_id=user_id,
                organization_id=org_id,
                jwt_token=supabase_client.auth.get_session().access_token if hasattr(supabase_client.auth.get_session(), 'access_token') else None
            )
            
            # Create headers with new idempotency key
            headers = SendHeaders(
                session_id=str(session_id),
                client_message_id=None,  # No client message ID for regeneration
                idempotency_key=idempotency_key
            )
            
            # Call the main run method
            openai_response, send_context = await self.run(
                session_id=session_id,
                request=request,
                user_ctx=user_ctx,
                organization_id=org_id,
                headers=headers
            )
            
            # Convert response to dict format for JSON serialization
            response_dict = {
                "id": openai_response.id,
                "object": openai_response.object,
                "created": openai_response.created,
                "model": openai_response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in openai_response.choices
                ],
                "usage": {
                    "prompt_tokens": openai_response.usage.prompt_tokens,
                    "completion_tokens": openai_response.usage.completion_tokens,
                    "total_tokens": openai_response.usage.total_tokens
                } if openai_response.usage else None
            }
            
            # Build response headers
            response_headers = {
                "X-User-Message-ID": str(send_context.user_msg_id),
                "X-Assistant-Message-ID": str(send_context.assistant_msg_id),
                "X-Message-Index-Start": str(send_context.start_index)
            }
            
            return {
                "body": response_dict,
                "headers": response_headers
            }
            
        except Exception as e:
            # Convert to OpenAI error format
            if hasattr(e, 'status_code'):
                raise e
            else:
                server_error(f"Regeneration failed: {str(e)}")
    
    async def _load_session_and_mode(
        self, session_id: UUID, user_ctx: CurrentUser
    ) -> Tuple[Dict[str, Any], PlaygroundRequestSource]:
        """Load session data and determine request source mode."""
        result = supabase_service.table("chat_sessions").select(
            "metadata, user_id"
        ).eq("id", str(session_id)).execute()
        
        if not result.data:
            session_not_found_error(str(session_id))
        
        session_data = result.data[0]
        
        # Verify session ownership
        if session_data["user_id"] != str(user_ctx.id):
            session_not_found_error(str(session_id))
        
        # Determine request source (default to gateway)
        session_metadata = session_data.get("metadata", {})
        request_source = PlaygroundRequestSource.gateway
        if isinstance(session_metadata, dict):
            request_source = PlaygroundRequestSource(
                session_metadata.get("request_source", "gateway")
            )
        
        return session_data, request_source
    
    async def _parse_and_validate_model(
        self, model: str, user_jwt: str
    ) -> Tuple[str, str, UUID]:
        """Parse and validate model format, return provider info."""
        # Validate model prefix format
        if "/" not in model:
            invalid_model_format_error(model)
        
        provider_name, model_name = model.split("/", 1)
        
        # Validate provider is supported
        supported_providers = ["openai", "anthropic"]
        if provider_name.lower() not in supported_providers:
            model_not_found_error(model)
        
        # Get provider ID
        provider_id = await get_provider_id_by_name(provider_name, user_jwt)
        if not provider_id:
            model_not_found_error(model)
        
        return provider_name, model_name, provider_id
    
    async def _check_idempotency(
        self, session_id: UUID, idempotency_key: str, model: str
    ) -> Optional[Tuple[ChatCompletionResponse, SendContext]]:
        """Check for prior result with same idempotency key."""
        prior_result = find_prior_result(session_id, idempotency_key)
        if prior_result:
            user_msg, assistant_msg = prior_result
            
            # Get token usage for assistant message
            token_usage = get_token_usage_for_message(UUID(assistant_msg["id"]))
            
            usage = ChatCompletionUsage(
                prompt_tokens=token_usage.get("input_tokens", 0) if token_usage else 0,
                completion_tokens=token_usage.get("output_tokens", 0) if token_usage else 0,
                total_tokens=(token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)) if token_usage else 0
            )
            
            # Reconstruct OpenAI response
            response = ChatCompletionResponse(
                id=f"chatcmpl-{uuid4().hex[:29]}",
                object="chat.completion",
                created=int(time.time()),
                model=model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=assistant_msg["content"]
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=usage
            )
            
            context = SendContext(
                user_msg_id=UUID(user_msg["id"]) if user_msg else UUID(assistant_msg["id"]),
                assistant_msg_id=UUID(assistant_msg["id"]),
                start_index=assistant_msg.get("message_index", 0)
            )
            
            return response, context
        
        return None
    
    async def _persist_user_message(
        self, session_id: UUID, request: ChatCompletionRequest, headers: SendHeaders
    ) -> Tuple[UUID, int]:
        """Persist user message optimistically."""
        # Validate last message is from user
        if not request.messages or request.messages[-1].role != "user":
            openai_error(400, "Last message must be from user", code="invalid_request")
        
        user_message = request.messages[-1]
        
        # Get next message index
        start_index = await next_index(session_id)
        
        # Create user message draft
        user_draft = MessageDraft(
            role="user",
            content=user_message.content,
            metadata={
                "client_message_id": headers.client_message_id,
                "idempotency_key": headers.idempotency_key
            }
        )
        
        # Persist user message
        user_messages = await append_messages(session_id, [user_draft])
        user_msg_id = UUID(user_messages[0]["id"]) if user_messages else None
        
        if not user_msg_id:
            server_error("Failed to persist user message")
        
        return user_msg_id, start_index
    
    async def _provider_key_preflight(
        self, organization_id: UUID, provider_id: UUID, user_jwt: str
    ) -> None:
        """Validate organization has active API key for provider."""
        await require_active_key(organization_id, provider_id, user_jwt)
    
    async def _dispatch_completion(
        self,
        request_source: PlaygroundRequestSource,
        organization_id: UUID,
        user_id: UUID,
        request: ChatCompletionRequest,
        provider_name: str,
        model_name: str,
        session_hint: str
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Dispatch to Gateway or Direct mode."""
        if request_source == PlaygroundRequestSource.gateway:
            # Gateway mode: use unified pipeline
            response = await self.gateway_bridge.chat_completion_openai_compatible(
                org_id=organization_id,
                user_id=user_id,
                request=request,
                session_hint=session_hint
            )
            
            # Convert response to dict format
            response_data = {
                "id": response.id,
                "choices": [
                    {
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else {}
            }
            
            return response_data, response.id
        
        else:
            # Direct mode: use provider adapters
            return await self._direct_completion(
                organization_id, provider_name, model_name, request
            )
    
    async def _direct_completion(
        self,
        organization_id: UUID,
        provider_name: str,
        model_name: str,
        request: ChatCompletionRequest
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Execute direct provider API call."""
        # Get decrypted API key
        api_key = await self._get_decrypted_api_key(organization_id, provider_name)
        if not api_key:
            server_error(f"No API key found for provider: {provider_name}")
        
        # Get adapter and execute
        adapter = get_adapter(provider_name)
        
        try:
            response = await adapter.chat_completion(request, api_key)
            
            # Convert to dict format
            response_data = {
                "id": response.id,
                "choices": [
                    {
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else {}
            }
            
            return response_data, response.id
            
        finally:
            await adapter.client.aclose()
    
    async def _persist_assistant_response(
        self,
        session_id: UUID,
        response_data: Dict[str, Any],
        idempotency_key: Optional[str],
        provider_request_id: Optional[str]
    ) -> Tuple[UUID, ChatCompletionUsage]:
        """Persist assistant message and token usage."""
        # Extract response content and usage
        assistant_content = ""
        usage_data = response_data.get("usage", {})
        
        if "choices" in response_data and response_data["choices"]:
            assistant_content = response_data["choices"][0]["message"]["content"]
        
        # Create usage object
        usage = ChatCompletionUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )
        
        # Create assistant message draft
        assistant_draft = MessageDraft(
            role="assistant",
            content=assistant_content,
            metadata={
                "idempotency_key": idempotency_key,
                "response_id": response_data.get("id"),
                "provider_request_id": provider_request_id
            }
        )
        
        # Persist assistant message
        assistant_messages = await append_messages(session_id, [assistant_draft])
        assistant_msg_id = UUID(assistant_messages[0]["id"]) if assistant_messages else None
        
        if not assistant_msg_id:
            server_error("Failed to persist assistant message")
        
        # Save token usage for assistant message
        if usage.completion_tokens > 0:
            supabase_service.table("token_usage").insert({
                "message_id": str(assistant_msg_id),
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            }).execute()
        
        return assistant_msg_id, usage
    
    async def _log_analytics(
        self,
        organization_id: UUID,
        user_id: UUID,
        session_id: UUID,
        model_id: str,
        provider_id: UUID,
        provider_request_id: Optional[str],
        usage: ChatCompletionUsage,
        duration_ms: int
    ) -> None:
        """Log request to api_requests table for analytics."""
        # Calculate cost
        model_name = model_id.split("/", 1)[1] if "/" in model_id else model_id
        cost = await self.analytics_logger.calculate_model_cost(
            model_name, usage.prompt_tokens, usage.completion_tokens
        )
        
        await self.analytics_logger.log_playground_request(
            organization_id=organization_id,
            user_id=user_id,
            session_id=session_id,
            model_id=model_id,
            provider_id=provider_id,
            provider_request_id=provider_request_id,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost=cost,
            duration_ms=duration_ms,
            status_code=200
        )
    
    async def _log_failed_request(
        self,
        organization_id: UUID,
        user_id: UUID,
        session_id: UUID,
        model_id: str,
        duration_ms: int,
        error_message: str
    ) -> None:
        """Log failed request for analytics."""
        await self.analytics_logger.log_playground_request(
            organization_id=organization_id,
            user_id=user_id,
            session_id=session_id,
            model_id=model_id,
            prompt_tokens=0,
            completion_tokens=0,
            duration_ms=duration_ms,
            status_code=500
        )
    
    def _build_openai_response(
        self, model: str, response_data: Dict[str, Any], usage: ChatCompletionUsage
    ) -> ChatCompletionResponse:
        """Build OpenAI-compatible response."""
        choices = []
        if "choices" in response_data and response_data["choices"]:
            for i, choice_data in enumerate(response_data["choices"]):
                choice = ChatCompletionChoice(
                    index=i,
                    message=ChatMessage(
                        role=choice_data["message"]["role"],
                        content=choice_data["message"]["content"]
                    ),
                    finish_reason=choice_data.get("finish_reason", "stop")
                )
                choices.append(choice)
        
        return ChatCompletionResponse(
            id=response_data.get("id", f"chatcmpl-{uuid4().hex[:29]}"),
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=choices,
            usage=usage
        )
    
    async def _get_decrypted_api_key(
        self, organization_id: UUID, provider_name: str
    ) -> Optional[str]:
        """Get and decrypt API key for provider."""
        try:
            # Get provider ID
            provider_result = supabase_service.table("ai_providers").select(
                "id"
            ).eq("name", provider_name.lower()).execute()
            
            if not provider_result.data:
                return None
            
            provider_id = provider_result.data[0]['id']
            
            # Get API key
            result = supabase_service.table("api_keys").select(
                "encrypted_key_value"
            ).eq("organization_id", str(organization_id)).eq(
                "provider_id", provider_id
            ).eq("is_active", True).execute()
            
            if not result.data:
                return None
            
            encrypted_key = result.data[0]['encrypted_key_value']
            
            # Decrypt the API key
            from ..core.encryption import encryption_service
            decrypted_key = encryption_service.decrypt_api_key(encrypted_key)
            return decrypted_key
            
        except Exception:
            return None
