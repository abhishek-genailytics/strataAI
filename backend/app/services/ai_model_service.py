from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ai_model import AIModel, AIModelCreate, AIModelUpdate
from .base import BaseService


class AIModelService(BaseService):
    """Service for managing AI models."""

    def __init__(self):
        super().__init__(AIModel)

    async def create(self, db: AsyncSession, model_data: AIModelCreate) -> AIModel:
        """Create a new AI model."""
        model = AIModel(**model_data.dict())
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model

    async def get_by_id(self, db: AsyncSession, model_id: UUID) -> Optional[AIModel]:
        """Get AI model by ID."""
        result = await db.execute(select(AIModel).where(AIModel.id == model_id))
        return result.scalars().first()

    async def get_by_provider(self, db: AsyncSession, provider_id: UUID) -> List[AIModel]:
        """Get all models for a specific provider."""
        result = await db.execute(
            select(AIModel).where(
                AIModel.provider_id == provider_id,
                AIModel.is_active == True
            )
        )
        return result.scalars().all()

    async def get_by_model_name(self, db: AsyncSession, model_name: str) -> Optional[AIModel]:
        """Get AI model by model name."""
        result = await db.execute(
            select(AIModel).where(
                AIModel.model_name == model_name,
                AIModel.is_active == True
            )
        )
        return result.scalars().first()

    async def get_by_type(self, db: AsyncSession, model_type: str) -> List[AIModel]:
        """Get all models of a specific type."""
        result = await db.execute(
            select(AIModel).where(
                AIModel.model_type == model_type,
                AIModel.is_active == True
            )
        )
        return result.scalars().all()

    async def get_all_active(self, db: AsyncSession) -> List[AIModel]:
        """Get all active AI models."""
        result = await db.execute(
            select(AIModel).where(AIModel.is_active == True)
        )
        return result.scalars().all()

    async def update(self, db: AsyncSession, model_id: UUID, model_data: AIModelUpdate) -> Optional[AIModel]:
        """Update an AI model."""
        model = await self.get_by_id(db, model_id)
        if not model:
            return None

        update_data = model_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)

        await db.commit()
        await db.refresh(model)
        return model

    async def delete(self, db: AsyncSession, model_id: UUID) -> bool:
        """Soft delete an AI model."""
        model = await self.get_by_id(db, model_id)
        if not model:
            return False

        model.is_active = False
        await db.commit()
        return True

    async def get_models_with_pricing(self, db: AsyncSession, provider_id: Optional[UUID] = None) -> List[dict]:
        """Get models with their pricing information."""
        from ..models.model_pricing import ModelPricing
        
        query = select(AIModel, ModelPricing).join(
            ModelPricing, 
            ModelPricing.model_id == AIModel.id,
            isouter=True
        ).where(AIModel.is_active == True)
        
        if provider_id:
            query = query.where(AIModel.provider_id == provider_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        models_with_pricing = []
        for row in rows:
            model, pricing = row
            model_dict = {
                "id": model.id,
                "provider_id": model.provider_id,
                "model_name": model.model_name,
                "display_name": model.display_name,
                "description": model.description,
                "model_type": model.model_type,
                "max_tokens": model.max_tokens,
                "max_input_tokens": model.max_input_tokens,
                "supports_streaming": model.supports_streaming,
                "supports_function_calling": model.supports_function_calling,
                "supports_vision": model.supports_vision,
                "supports_audio": model.supports_audio,
                "capabilities": model.capabilities,
                "pricing": []
            }
            
            if pricing:
                model_dict["pricing"].append({
                    "id": pricing.id,
                    "pricing_type": pricing.pricing_type,
                    "price_per_unit": float(pricing.price_per_unit),
                    "unit": pricing.unit,
                    "currency": pricing.currency,
                    "region": pricing.region
                })
            
            models_with_pricing.append(model_dict)
        
        return models_with_pricing


ai_model_service = AIModelService()
