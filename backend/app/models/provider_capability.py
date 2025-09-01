from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ProviderCapabilityBase(BaseModel):
    provider_id: UUID
    capability_name: str
    capability_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: bool = True


class ProviderCapabilityCreate(ProviderCapabilityBase):
    pass


class ProviderCapabilityUpdate(BaseModel):
    capability_name: Optional[str] = None
    capability_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProviderCapability(ProviderCapabilityBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
