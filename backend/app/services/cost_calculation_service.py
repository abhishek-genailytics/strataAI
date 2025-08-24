from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AIProvider


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
    
    async def get_provider_pricing(self, db: AsyncSession, provider_id: UUID) -> Optional[Dict]:
        """Get pricing information for a provider from database."""
        result = await db.execute(
            select(AIProvider.pricing_info, AIProvider.name)
            .where(AIProvider.id == provider_id)
        )
        row = result.first()
        if row:
            return {"pricing_info": row.pricing_info, "provider_name": row.name}
        return None
    
    async def calculate_cost(
        self, 
        db: AsyncSession,
        provider_id: UUID,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """Calculate cost for a request based on token usage."""
        # Get provider pricing from database
        provider_data = await self.get_provider_pricing(db, provider_id)
        
        if provider_data and provider_data["pricing_info"]:
            pricing_info = provider_data["pricing_info"]
            model_pricing = pricing_info.get(model_name)
        else:
            # Fallback to default pricing
            provider_name = provider_data["provider_name"].lower() if provider_data else "openai"
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
        """Get pricing information for a specific model."""
        provider_pricing = self.DEFAULT_PRICING.get(provider_name.lower())
        if provider_pricing:
            return provider_pricing.get(model_name)
        return None
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens from text (approximately 4 characters per token)."""
        return max(1, len(text) // 4)


cost_calculation_service = CostCalculationService()
