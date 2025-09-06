import math
from uuid import UUID
from app.services.llm_adapters.base import LLMAdapter
from app.models.openai_chat import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatCompletionUsage, ChatMessage
)

def _approx_tokens(text: str) -> int:
    # naive & deterministic: 1 token ~ 4 chars (ASCII assumption)
    return max(1, math.ceil(len(text) / 4))

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

        # 2) usage (approx)
        prompt_text = "".join(m.content for m in request.messages)
        prompt_tokens = _approx_tokens(prompt_text)
        completion_tokens = _approx_tokens(reply_text)
        usage = ChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
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
