from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ResolvedProvider(BaseModel):
    id: UUID
    name: str          # slug, e.g., "openai"
    display_name: str
    is_active: bool

class ResolvedModel(BaseModel):
    id: UUID
    provider_id: UUID
    provider_name: str  # convenience copy
    model_name: str     # native name, e.g., "gpt-4o-mini"
    display_name: str
    model_type: str     # expect "chat" for MVP
    supports_streaming: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_audio: bool
    max_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None
    is_active: bool
