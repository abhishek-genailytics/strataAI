from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="The role of the message author (system, user, assistant)")
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(None, description="Optional name of the message author")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion."""
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    model: str = Field(..., description="The model to use for completion")
    provider: Optional[str] = Field(None, description="Specific provider to use (auto-detected if not provided)")
    project_id: UUID = Field(..., description="Project ID for API key lookup")
    
    # Optional parameters
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")


class ChatCompletionUsage(BaseModel):
    """Usage statistics for a chat completion."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage
    
    # Internal tracking
    request_id: Optional[UUID] = None
    processing_time_ms: Optional[int] = None


class ChatCompletionStreamChunk(BaseModel):
    """A single chunk in a streaming response."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    provider: str
    choices: List[Dict[str, Any]]
    
    # Internal tracking
    request_id: Optional[UUID] = None


class ProviderModelInfo(BaseModel):
    """Information about a provider's model."""
    provider: str
    model: str
    display_name: str
    max_tokens: int
    supports_streaming: bool = True
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float


class ProviderError(BaseModel):
    """Error information from a provider."""
    provider: str
    error_type: str
    error_message: str
    error_code: Optional[str] = None
    retry_after: Optional[int] = None
