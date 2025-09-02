from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class APIRequestBase(BaseModel):
    model_name: str
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal('0')
    latency_ms: Optional[int] = None


class APIRequestCreate(APIRequestBase):
    user_id: UUID
    api_key_id: UUID
    provider_id: UUID
    organization_id: UUID


class APIRequest(APIRequestBase):
    id: UUID
    user_id: UUID
    api_key_id: UUID
    provider_id: UUID
    organization_id: UUID
    total_tokens: int
    created_at: datetime

    class Config:
        from_attributes = True


class APIRequestWithDetails(APIRequest):
    provider_name: str
