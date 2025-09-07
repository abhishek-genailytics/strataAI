"""
Pydantic models for playground messages pagination and usage.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class PlaygroundTokenUsage(BaseModel):
    """Per-message token usage summary for HUD/cost intelligence."""
    input_tokens: int = Field(0, description="Input tokens consumed")
    output_tokens: int = Field(0, description="Output tokens consumed")
    total_tokens: int = Field(0, description="Total tokens consumed")


class PlaygroundMessageRead(BaseModel):
    """Flattened message row with optional usage."""
    id: UUID = Field(..., description="Message ID")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Creation timestamp")
    usage: Optional[PlaygroundTokenUsage] = Field(None, description="Per-message token usage")


class PageInfo(BaseModel):
    next_cursor: Optional[str] = Field(None, description="Cursor for the next page (newer)")
    prev_cursor: Optional[str] = Field(None, description="Cursor for the previous page (older)")
    has_next: bool = Field(False, description="Whether there are newer items after this page")
    has_prev: bool = Field(False, description="Whether there are older items before this page")


class MessagesPage(BaseModel):
    data: List[PlaygroundMessageRead]
    page: PageInfo
    meta: dict = Field(default_factory=dict, description="Additional metadata like session_id and count")

