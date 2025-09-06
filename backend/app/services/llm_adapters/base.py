from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID
import time
import uuid

from app.models.openai_chat import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatCompletionUsage, ChatMessage
)

class LLMAdapter(ABC):
    """
    Provider-agnostic interface for non-stream chat.completions.
    """
    provider_name: str  # e.g., "openai", "anthropic", "echo"

    def _response_id(self) -> str:
        return "chatcmpl_" + uuid.uuid4().hex[:24]

    def _created_ts(self) -> int:
        return int(time.time())

    @abstractmethod
    async def chat_completion(
        self,
        *,
        organization_id: UUID,
        request: ChatCompletionRequest,
        model_name: str,      # native model name (e.g., "gpt-4o-mini")
        api_key: str | None,  # EchoAdapter ignores; real adapters require
    ) -> ChatCompletionResponse:
        ...
