from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.provider_capability import ProviderCapability, ProviderCapabilityCreate, ProviderCapabilityUpdate
from .base import BaseService


class ProviderCapabilityService(BaseService):
    """Service for managing provider capabilities."""

    async def create(self, db: AsyncSession, capability_data: ProviderCapabilityCreate) -> ProviderCapability:
        """Create new provider capability."""
        capability = ProviderCapability(**capability_data.dict())
        db.add(capability)
        await db.commit()
        await db.refresh(capability)
        return capability

    async def get_by_id(self, db: AsyncSession, capability_id: UUID) -> Optional[ProviderCapability]:
        """Get capability by ID."""
        result = await db.execute(select(ProviderCapability).where(ProviderCapability.id == capability_id))
        return result.scalars().first()

    async def get_by_provider(self, db: AsyncSession, provider_id: UUID) -> List[ProviderCapability]:
        """Get all capabilities for a specific provider."""
        result = await db.execute(
            select(ProviderCapability).where(
                ProviderCapability.provider_id == provider_id,
                ProviderCapability.is_active == True
            )
        )
        return result.scalars().all()

    async def get_by_name(self, db: AsyncSession, provider_id: UUID, capability_name: str) -> Optional[ProviderCapability]:
        """Get specific capability by name for a provider."""
        result = await db.execute(
            select(ProviderCapability).where(
                ProviderCapability.provider_id == provider_id,
                ProviderCapability.capability_name == capability_name,
                ProviderCapability.is_active == True
            )
        )
        return result.scalars().first()

    async def get_provider_capabilities_dict(self, db: AsyncSession, provider_id: UUID) -> Dict[str, Any]:
        """Get all capabilities for a provider as a dictionary."""
        capabilities = await self.get_by_provider(db, provider_id)
        capabilities_dict = {}
        
        for capability in capabilities:
            capabilities_dict[capability.capability_name] = capability.capability_value
        
        return capabilities_dict

    async def update(self, db: AsyncSession, capability_id: UUID, capability_data: ProviderCapabilityUpdate) -> Optional[ProviderCapability]:
        """Update provider capability."""
        capability = await self.get_by_id(db, capability_id)
        if not capability:
            return None

        update_data = capability_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(capability, field, value)

        await db.commit()
        await db.refresh(capability)
        return capability

    async def delete(self, db: AsyncSession, capability_id: UUID) -> bool:
        """Soft delete provider capability."""
        capability = await self.get_by_id(db, capability_id)
        if not capability:
            return False

        capability.is_active = False
        await db.commit()
        return True

    async def bulk_create(self, db: AsyncSession, provider_id: UUID, capabilities: Dict[str, Any]) -> List[ProviderCapability]:
        """Bulk create capabilities for a provider."""
        created_capabilities = []
        
        for capability_name, capability_value in capabilities.items():
            capability_data = ProviderCapabilityCreate(
                provider_id=provider_id,
                capability_name=capability_name,
                capability_value=capability_value
            )
            capability = await self.create(db, capability_data)
            created_capabilities.append(capability)
        
        return created_capabilities

    async def check_capability(self, db: AsyncSession, provider_id: UUID, capability_name: str) -> bool:
        """Check if a provider has a specific capability."""
        capability = await self.get_by_name(db, provider_id, capability_name)
        return capability is not None and capability.capability_value is not None

    async def get_providers_with_capability(self, db: AsyncSession, capability_name: str) -> List[UUID]:
        """Get all provider IDs that have a specific capability."""
        result = await db.execute(
            select(ProviderCapability.provider_id).where(
                ProviderCapability.capability_name == capability_name,
                ProviderCapability.is_active == True
            )
        )
        return result.scalars().all()


provider_capability_service = ProviderCapabilityService()
