"""
Pydantic models for playground HUD (Heads-Up Display) panel data.

The HUD provides comprehensive session analytics including:
- Session totals (tokens, cost, request count)
- Per-model breakdown
- Recent activity
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class HudTotals(BaseModel):
    """Aggregated totals for a session within a time window."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    currency: str
    request_count: int


class HudBreakdownItem(BaseModel):
    """Per-provider/model breakdown of usage within a session."""
    provider: str
    model: str
    requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal


class HudRecentItem(BaseModel):
    """Recent API request activity for the session."""
    id: str
    created_at: datetime
    status_code: int
    duration_ms: int
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    provider_request_id: Optional[str] = None


class HudResponse(BaseModel):
    """Complete HUD response containing all session analytics."""
    session_id: str
    window: str
    totals: HudTotals
    breakdown: list[HudBreakdownItem]
    recent: list[HudRecentItem]
    generated_at: datetime
