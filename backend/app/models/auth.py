"""
Authentication models - MVP stubs.
"""
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class CurrentCaller(BaseModel):
    """Carries user_id, organization_id for authenticated requests"""
    user_id: UUID
    organization_id: UUID
    token_id: UUID
    token_prefix: str
    scopes: list[str] = []
