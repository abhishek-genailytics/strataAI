"""
Gateway bridge service for in-process unified pipeline calls.
Enables playground to use unified pipeline without HTTP overhead or PAT authentication.
"""
from uuid import UUID
from typing import Optional
from app.models.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from app.services.unified_service import UnifiedChatService


class GatewayBridge:
    """In-process call into the unified pipeline to ensure parity with /v1."""
    
    def __init__(self, unified: Optional[UnifiedChatService] = None):
        self.unified = unified or UnifiedChatService()
    
    async def chat_completion_openai_compatible(
        self, 
        *,
        org_id: UUID,
        user_id: UUID,
        request: ChatCompletionRequest,
        session_hint: Optional[str] = None
    ) -> ChatCompletionResponse:
        """
        Call the same service used by /v1/chat/completions route:
        - model prefix routing (openai/... anthropic/...)
        - pricing + usage calc
        - non-stream JSON
        - OpenAI envelope
        
        Args:
            org_id: Organization ID
            user_id: User ID initiating the request
            request: OpenAI-compatible chat completion request
            session_hint: Optional session ID for playground session logging
            
        Returns:
            ChatCompletionResponse: OpenAI-compatible response
        """
        return await self.unified.chat_completions_internal(
            organization_id=org_id,
            initiated_by_user_id=user_id,
            request=request,
            x_session_id=session_hint,
        )
