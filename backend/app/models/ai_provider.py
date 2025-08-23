from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class AIProviderBase(BaseModel):
    name: str
    display_name: str
    base_url: str
    supported_models: List[str] = []
    pricing_info: Dict[str, Any] = {}
    is_active: bool = True


class AIProviderCreate(AIProviderBase):
    pass


class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    base_url: Optional[str] = None
    supported_models: Optional[List[str]] = None
    pricing_info: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AIProvider(AIProviderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
