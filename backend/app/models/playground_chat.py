"""
OpenAI-compatible Pydantic models for playground chat completions.
Implements the single playground chat API contract with OpenAI-style request/response.
"""
from typing import List, Optional, Union
from pydantic import BaseModel, field_validator
import time
import uuid


# --- Request Models ---

class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class PlaygroundChatCompletionRequest(BaseModel):
    model: str                       # e.g., "openai/gpt-4o-mini" or "anthropic/claude-3-haiku"
    messages: List[ChatMessage]
    system: Optional[str] = None     # NEW: per-request system prompt override
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None
    stream: Optional[bool] = False     # accepted but always ignored (non-stream MVP)
    # Extensions that we ACCEPT but IGNORE for MVP:
    #   n, logprobs, response_format, tool_choice, tools, function_call

    @field_validator("stream")
    @classmethod
    def _force_stream_false(cls, v):   # MVP: non-stream
        return False


# --- Response Models ---

class ChatChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: Optional[str] = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class PlaygroundChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str                            # echo of "provider/model" passed in
    choices: List[ChatChoice]
    usage: ChatUsage

    @classmethod
    def create(
        cls,
        model: str,
        content: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        finish_reason: str = "stop",
        response_id: Optional[str] = None
    ) -> "PlaygroundChatCompletionResponse":
        """Create a standardized playground chat completion response."""
        return cls(
            id=response_id or f"chatcmpl_{uuid.uuid4().hex[:24]}",
            created=int(time.time()),
            model=model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatChoiceMessage(
                        role="assistant",
                        content=content
                    ),
                    finish_reason=finish_reason
                )
            ],
            usage=ChatUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )
