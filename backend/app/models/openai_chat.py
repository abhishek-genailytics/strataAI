"""
OpenAI-compatible Pydantic models for chat completions.
Implements the exact contract specified in the backend design.
"""
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, field_validator

Role = Literal["system", "user", "assistant"]

class ChatMessage(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None  # accepted by OpenAI schema

class ChatCompletionRequest(BaseModel):
    model: str  # "provider/model" (e.g., "openai/gpt-4o-mini")
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    n: Optional[int] = 1
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    user: Optional[str] = None
    stream: Optional[bool] = False  # ignored/forced false for MVP

    @field_validator("stream")
    @classmethod
    def _force_stream_false(cls, v):
        """Force streaming to False for MVP - no SSE support."""
        return False

    # Model validation moved to route handler to enable proper OpenAI error formatting

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None  # e.g., "stop", "length", "content_filter"

class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str                     # e.g., "chatcmpl_..."
    object: str = "chat.completion"
    created: int                # epoch seconds
    model: str                  # echo back request.model
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage
