from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.model_pricing import ModelPricing, ModelPricingCreate, ModelPricingUpdate
from .base import BaseService


class ModelPricingService(BaseService):
    """Service for managing model pricing."""

    def __init__(self):
        super().__init__(ModelPricing)

    async def create(self, db: AsyncSession, pricing_data: ModelPricingCreate) -> ModelPricing:
        """Create new model pricing."""
        pricing = ModelPricing(**pricing_data.dict())
        db.add(pricing)
        await db.commit()
        await db.refresh(pricing)
        return pricing

    async def get_by_id(self, db: AsyncSession, pricing_id: UUID) -> Optional[ModelPricing]:
        """Get pricing by ID."""
        result = await db.execute(select(ModelPricing).where(ModelPricing.id == pricing_id))
        return result.scalars().first()

    async def get_by_model(self, db: AsyncSession, model_id: UUID) -> List[ModelPricing]:
        """Get all pricing for a specific model."""
        result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.model_id == model_id,
                ModelPricing.is_active == True
            )
        )
        return result.scalars().all()

    async def get_current_pricing(self, db: AsyncSession, model_id: UUID) -> List[ModelPricing]:
        """Get current active pricing for a model."""
        from datetime import datetime
        
        result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.model_id == model_id,
                ModelPricing.is_active == True,
                ModelPricing.effective_from <= datetime.utcnow(),
                (ModelPricing.effective_until.is_(None) | (ModelPricing.effective_until > datetime.utcnow()))
            )
        )
        return result.scalars().all()

    async def get_pricing_by_type(self, db: AsyncSession, model_id: UUID, pricing_type: str) -> Optional[ModelPricing]:
        """Get pricing for a specific model and type."""
        from datetime import datetime
        
        result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.model_id == model_id,
                ModelPricing.pricing_type == pricing_type,
                ModelPricing.is_active == True,
                ModelPricing.effective_from <= datetime.utcnow(),
                (ModelPricing.effective_until.is_(None) | (ModelPricing.effective_until > datetime.utcnow()))
            )
        )
        return result.scalars().first()

    async def update(self, db: AsyncSession, pricing_id: UUID, pricing_data: ModelPricingUpdate) -> Optional[ModelPricing]:
        """Update model pricing."""
        pricing = await self.get_by_id(db, pricing_id)
        if not pricing:
            return None

        update_data = pricing_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pricing, field, value)

        await db.commit()
        await db.refresh(pricing)
        return pricing

    async def delete(self, db: AsyncSession, pricing_id: UUID) -> bool:
        """Soft delete model pricing."""
        pricing = await self.get_by_id(db, pricing_id)
        if not pricing:
            return False

        pricing.is_active = False
        await db.commit()
        return True

    async def calculate_cost(
        self, 
        db: AsyncSession, 
        model_id: UUID, 
        input_tokens: int = 0, 
        output_tokens: int = 0
    ) -> dict:
        """Calculate cost for a model based on token usage."""
        cost_breakdown = {
            "input_cost": Decimal('0'),
            "output_cost": Decimal('0'),
            "total_cost": Decimal('0'),
            "currency": "USD"
        }

        # Get input pricing
        input_pricing = await self.get_pricing_by_type(db, model_id, "input")
        if input_pricing and input_tokens > 0:
            input_cost = (input_pricing.price_per_unit * Decimal(str(input_tokens))) / Decimal('1000')
            cost_breakdown["input_cost"] = input_cost
            cost_breakdown["currency"] = input_pricing.currency

        # Get output pricing
        output_pricing = await self.get_pricing_by_type(db, model_id, "output")
        if output_pricing and output_tokens > 0:
            output_cost = (output_pricing.price_per_unit * Decimal(str(output_tokens))) / Decimal('1000')
            cost_breakdown["output_cost"] = output_cost
            cost_breakdown["currency"] = output_pricing.currency

        cost_breakdown["total_cost"] = cost_breakdown["input_cost"] + cost_breakdown["output_cost"]
        
        return cost_breakdown

    async def get_pricing_history(self, db: AsyncSession, model_id: UUID) -> List[ModelPricing]:
        """Get pricing history for a model."""
        result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.model_id == model_id
            ).order_by(ModelPricing.effective_from.desc())
        )
        return result.scalars().all()


model_pricing_service = ModelPricingService()
