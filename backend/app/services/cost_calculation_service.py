from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AIProvider
from ..models.model_pricing import ModelPricing
from ..models.ai_model import AIModel


class CostCalculationService:
    """Service for calculating costs based on provider pricing and token usage."""
    
    # Default pricing per 1K tokens (USD) - fallback if not in database
    DEFAULT_PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
    }
    
    async def get_model_pricing(self, db: AsyncSession, model_name: str) -> Optional[Dict]:
        """Get pricing information for a model from the new model_pricing table."""
        from datetime import datetime
        
        # First find the model
        model_result = await db.execute(
            select(AIModel).where(AIModel.model_name == model_name, AIModel.is_active == True)
        )
        model = model_result.scalars().first()
        
        if not model:
            return None
        
        # Get current pricing for the model
        pricing_result = await db.execute(
            select(ModelPricing).where(
                ModelPricing.model_id == model.id,
                ModelPricing.is_active == True,
                ModelPricing.effective_from <= datetime.utcnow(),
                (ModelPricing.effective_until.is_(None) | (ModelPricing.effective_until > datetime.utcnow()))
            )
        )
        pricing_records = pricing_result.scalars().all()
        
        if not pricing_records:
            return None
        
        # Convert to the expected format
        pricing_info = {}
        for pricing in pricing_records:
            if pricing.pricing_type in ["input", "output"]:
                pricing_info[pricing.pricing_type] = float(pricing.price_per_unit)
        
        return pricing_info
    
    async def calculate_cost(
        self, 
        db: AsyncSession,
        provider_id: UUID,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """Calculate cost for a request based on token usage."""
        # Get model pricing from the new model_pricing table
        model_pricing = await self.get_model_pricing(db, model_name)
        
        if not model_pricing:
            # Fallback to default pricing based on provider
            provider_result = await db.execute(
                select(AIProvider.name).where(AIProvider.id == provider_id)
            )
            provider = provider_result.scalars().first()
            provider_name = provider.name.lower() if provider else "openai"
            model_pricing = self.DEFAULT_PRICING.get(provider_name, {}).get(model_name)
        
        if not model_pricing:
            # If no pricing found, return 0 cost
            return Decimal('0')
        
        # Calculate cost per 1K tokens
        input_cost_per_1k = Decimal(str(model_pricing.get("input", 0)))
        output_cost_per_1k = Decimal(str(model_pricing.get("output", 0)))
        
        # Calculate total cost
        input_cost = (Decimal(str(input_tokens)) / Decimal('1000')) * input_cost_per_1k
        output_cost = (Decimal(str(output_tokens)) / Decimal('1000')) * output_cost_per_1k
        
        total_cost = input_cost + output_cost
        return total_cost.quantize(Decimal('0.000001'))  # Round to 6 decimal places
    
    def get_model_pricing_info(self, provider_name: str, model_name: str) -> Optional[Dict]:
        """Get pricing information for a specific model (fallback method)."""
        provider_pricing = self.DEFAULT_PRICING.get(provider_name.lower())
        if provider_pricing:
            return provider_pricing.get(model_name)
        return None
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens from text (approximately 4 characters per token)."""
        return max(1, len(text) // 4)


cost_calculation_service = CostCalculationService()
