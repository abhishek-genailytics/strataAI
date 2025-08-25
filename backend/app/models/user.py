from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(UserBase):
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
