from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UsageMetricsBase(BaseModel):
    date: date
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: Decimal = Decimal('0')
    avg_latency_ms: Optional[Decimal] = None


class UsageMetricsCreate(UsageMetricsBase):
    user_id: UUID
    project_id: UUID
    provider_id: UUID


class UsageMetricsUpdate(BaseModel):
    total_requests: Optional[int] = None
    successful_requests: Optional[int] = None
    failed_requests: Optional[int] = None
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[Decimal] = None
    avg_latency_ms: Optional[Decimal] = None


class UsageMetrics(UsageMetricsBase):
    id: UUID
    user_id: UUID
    project_id: UUID
    provider_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UsageMetricsWithDetails(UsageMetrics):
    provider_name: str
    project_name: str
