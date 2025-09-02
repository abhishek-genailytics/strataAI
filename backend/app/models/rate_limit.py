from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RateLimitBase(BaseModel):
    limit_type: str = Field(..., pattern="^(requests_per_minute|requests_per_hour|requests_per_day|tokens_per_day|cost_per_day)$")
    limit_value: int
    current_usage: int = 0
    reset_at: datetime
    is_active: bool = True


class RateLimitCreate(RateLimitBase):
    user_id: UUID
    provider_id: UUID
    organization_id: UUID


class RateLimitUpdate(BaseModel):
    limit_value: Optional[int] = None
    current_usage: Optional[int] = None
    reset_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class RateLimit(RateLimitBase):
    id: UUID
    user_id: UUID
    provider_id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RateLimitWithDetails(RateLimit):
    provider_name: str
