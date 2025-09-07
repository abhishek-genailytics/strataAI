"""
Pydantic models for playground models listing endpoint.
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ModelCapabilities(BaseModel):
    """Model capabilities information."""
    supports_streaming: bool = False
    supports_function_calling: bool = False
    vision: bool = False


class ModelLimits(BaseModel):
    """Model token limits."""
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None


class PricingInfo(BaseModel):
    """Pricing information for a specific type (input/output)."""
    unit: str  # "token", "request", etc.
    price: Decimal  # Price per unit
    currency: str = "USD"


class ModelPricing(BaseModel):
    """Complete pricing information for a model."""
    input: Optional[PricingInfo] = None
    output: Optional[PricingInfo] = None


class ModelAvailability(BaseModel):
    """Model availability and access information."""
    org_enabled: bool = True
    has_org_api_key: bool = False
    user_enabled: bool = True
    locked_reason: Optional[str] = None


class PlaygroundModel(BaseModel):
    """Individual model in the playground models list."""
    id: str  # Format: "provider/model"
    provider: str  # Provider slug (openai, anthropic, etc.)
    model_name: str  # Native model name
    display_name: str  # Human-readable name
    type: str = "chat"  # Model type
    capabilities: Optional[ModelCapabilities] = None
    limits: Optional[ModelLimits] = None
    pricing: Optional[ModelPricing] = None
    availability: ModelAvailability
    is_default_for_user: bool = False
    metadata: Dict[str, Any] = {}


class PlaygroundModelsResponse(BaseModel):
    """Response for GET /playground/models endpoint."""
    data: List[PlaygroundModel]
    meta: Dict[str, Any]


class PlaygroundModelsMeta(BaseModel):
    """Metadata for playground models response."""
    org_id: str
    count: int
    generated_at: datetime
