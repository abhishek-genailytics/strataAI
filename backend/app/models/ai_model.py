from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class AIModelBase(BaseModel):
    provider_id: UUID
    model_name: str
    display_name: str
    description: Optional[str] = None
    model_type: str  # chat, completion, embedding, image, audio, multimodal
    max_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    capabilities: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    is_active: bool = True


class AIModelCreate(AIModelBase):
    pass


class AIModelUpdate(BaseModel):
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    model_type: Optional[str] = None
    max_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None
    supports_streaming: Optional[bool] = None
    supports_function_calling: Optional[bool] = None
    supports_vision: Optional[bool] = None
    supports_audio: Optional[bool] = None
    capabilities: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AIModel(AIModelBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
