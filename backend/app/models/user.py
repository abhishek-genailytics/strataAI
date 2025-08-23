from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    organization_name: Optional[str] = None
    subscription_tier: str = Field(default="free", pattern="^(free|pro|enterprise)$")


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    organization_name: Optional[str] = None
    subscription_tier: Optional[str] = Field(None, pattern="^(free|pro|enterprise)$")


class UserProfile(UserProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
