"""
Pydantic models for model enablement functionality.
"""
from typing import List
from pydantic import BaseModel


class EnableModelsRequest(BaseModel):
    """Request to enable models for an organization."""
    provider: str  # Provider ID
    model_ids: List[str]  # List of model IDs to enable


class EnableModelsResponse(BaseModel):
    """Response for model enablement."""
    message: str
    enabled_count: int
    provider_id: str
    model_ids: List[str]
