from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SessionTotals(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    currency: str = "USD"
    request_count: int


class SessionBreakdownItem(BaseModel):
    provider: str
    model: str
    requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal


class SessionUsageResponse(BaseModel):
    session_id: str
    window: str
    totals: SessionTotals
    breakdown: list[SessionBreakdownItem] = []
    generated_at: datetime


class SessionSeriesPoint(BaseModel):
    period_start: datetime
    request_count: int
    total_tokens: int
    cost: Decimal
