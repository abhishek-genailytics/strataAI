from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ModelPricingBase(BaseModel):
    model_id: UUID
    pricing_type: str  # input, output, per_request, per_second
    price_per_unit: Decimal
    unit: str  # token, request, second, minute
    currency: str = "USD"
    region: str = "global"
    effective_from: datetime
    effective_until: Optional[datetime] = None
    is_active: bool = True


class ModelPricingCreate(ModelPricingBase):
    pass


class ModelPricingUpdate(BaseModel):
    pricing_type: Optional[str] = None
    price_per_unit: Optional[Decimal] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    region: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class ModelPricing(ModelPricingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
