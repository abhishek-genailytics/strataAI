from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

class SessionMeta(BaseModel):
    client_session_id: Optional[str] = None
    # keep extensible

class PlaygroundSession(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int
    metadata: SessionMeta

class PlaygroundMessageUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class PlaygroundMessageCost(BaseModel):
    currency: str
    total_cost: str  # keep string to preserve decimal precision

class PlaygroundMessage(BaseModel):
    id: str
    message_index: int
    role: str           # "user" | "assistant"
    content: str
    created_at: datetime
    usage: Optional[PlaygroundMessageUsage] = None   # assistant only (if available)
    cost: Optional[PlaygroundMessageCost] = None     # assistant only (if available)

class MessagesPage(BaseModel):
    session_id: str
    messages: List[PlaygroundMessage]
    next_after_index: Optional[int] = None  # for pagination
