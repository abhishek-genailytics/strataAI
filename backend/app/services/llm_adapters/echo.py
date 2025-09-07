from uuid import UUID
from app.services.llm_adapters.base import LLMAdapter
from app.models.openai_chat import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatCompletionUsage, ChatMessage
)
from app.services.token_counting import unify_usage

class EchoAdapter(LLMAdapter):
    provider_name = "echo"

    async def chat_completion(
        self,
        *,
        organization_id: UUID,
        request: ChatCompletionRequest,
        model_name: str,
        api_key: str | None,
    ) -> ChatCompletionResponse:
        # 1) derive reply
        last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
        user_text = last_user.content if last_user else "Hello!"
        reply_text = f"echo: {user_text}"

        # 2) usage (centralized counting)
        provider_usage = None  # echo has no provider-reported usage
        usage = unify_usage(
            provider_usage=provider_usage,
            messages=request.messages,
            assistant_text=reply_text,
            model_name=model_name,
            provider="echo",
        )

        # 3) response
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content=reply_text),
            finish_reason="stop",
        )
        return ChatCompletionResponse(
            id=self._response_id(),
            created=self._created_ts(),
            model=f"echo/{model_name}",
            choices=[choice],
            usage=usage,
        )
