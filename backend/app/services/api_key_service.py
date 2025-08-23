from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.api_key import APIKey, APIKeyCreate, APIKeyUpdate, APIKeyDisplay, APIKeyValidationResult
from ..models.ai_provider import AIProvider
from ..core.encryption import encryption_service
from .api_key_validator import api_key_validator
from .base import BaseService


class APIKeyService(BaseService[APIKey, APIKeyCreate, APIKeyUpdate]):
    def __init__(self):
        super().__init__(APIKey)

    async def create_with_encryption(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: APIKeyCreate, 
        user_id: UUID
    ) -> APIKey:
        """Create a new API key with encryption."""
        # Encrypt the API key
        encrypted_key = encryption_service.encrypt_api_key(obj_in.api_key_value)
        key_prefix = encryption_service.get_key_prefix(obj_in.api_key_value)
        
        # Create the database object
        db_obj = self.model(
            name=obj_in.name,
            user_id=user_id,
            project_id=obj_in.project_id,
            provider_id=obj_in.provider_id,
            encrypted_key_value=encrypted_key,
            key_prefix=key_prefix,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def validate_and_create(
        self,
        db: AsyncSession,
        *,
        obj_in: APIKeyCreate,
        user_id: UUID,
        validate_key: bool = True
    ) -> tuple[APIKey, APIKeyValidationResult]:
        """Validate and create an API key."""
        # Get provider info for validation
        provider = await db.get(AIProvider, obj_in.provider_id)
        if not provider:
            raise ValueError("Invalid provider ID")
        
        validation_result = None
        if validate_key:
            # Validate the API key
            validation_result = await api_key_validator.validate_api_key(
                obj_in.api_key_value, 
                provider.name
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"API key validation failed: {validation_result.error_message}")
        
        # Create the API key
        api_key = await self.create_with_encryption(db, obj_in=obj_in, user_id=user_id)
        
        return api_key, validation_result

    async def get_with_provider(
        self, 
        db: AsyncSession, 
        *, 
        api_key_id: UUID, 
        user_id: UUID
    ) -> Optional[APIKey]:
        """Get API key with provider information."""
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.provider))
            .where(
                and_(
                    self.model.id == api_key_id,
                    self.model.user_id == user_id
                )
            )
        )
        return result.scalars().first()

    async def get_user_keys_with_providers(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        project_id: Optional[UUID] = None
    ) -> List[APIKeyDisplay]:
        """Get user's API keys with provider info for display."""
        query = (
            select(self.model, AIProvider)
            .join(AIProvider, self.model.provider_id == AIProvider.id)
            .where(self.model.user_id == user_id)
        )
        
        if project_id:
            query = query.where(self.model.project_id == project_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        display_keys = []
        for api_key, provider in rows:
            # Decrypt key for masking
            try:
                decrypted_key = encryption_service.decrypt_api_key(api_key.encrypted_key_value)
                masked_key = encryption_service.mask_api_key(decrypted_key)
            except Exception:
                masked_key = "****"
            
            display_keys.append(APIKeyDisplay(
                id=api_key.id,
                name=api_key.name,
                provider_name=provider.name,
                provider_display_name=provider.display_name,
                key_prefix=api_key.key_prefix,
                masked_key=masked_key,
                is_active=api_key.is_active,
                last_used_at=api_key.last_used_at,
                created_at=api_key.created_at,
                updated_at=api_key.updated_at
            ))
        
        return display_keys

    async def get_decrypted_key(
        self, 
        db: AsyncSession, 
        *, 
        api_key_id: UUID, 
        user_id: UUID
    ) -> Optional[str]:
        """Get decrypted API key value for use."""
        api_key = await self.get_with_provider(db, api_key_id=api_key_id, user_id=user_id)
        if not api_key or not api_key.is_active:
            return None
        
        try:
            decrypted_key = encryption_service.decrypt_api_key(api_key.encrypted_key_value)
            # Update last used timestamp
            await self.update_last_used(db, api_key_id=api_key_id)
            return decrypted_key
        except Exception:
            return None

    async def get_by_project_and_provider(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID, 
        project_id: UUID, 
        provider_id: UUID
    ) -> List[APIKey]:
        """Get API keys for a specific project and provider."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.project_id == project_id,
                    self.model.provider_id == provider_id,
                    self.model.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def get_active_keys(self, db: AsyncSession, *, user_id: UUID) -> List[APIKey]:
        """Get all active API keys for a user."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_active == True
                )
            )
        )
        return result.scalars().all()

    async def update_last_used(self, db: AsyncSession, *, api_key_id: UUID) -> Optional[APIKey]:
        """Update the last_used_at timestamp for an API key."""
        db_obj = await db.get(self.model, api_key_id)
        if db_obj:
            db_obj.last_used_at = datetime.utcnow()
            db_obj.updated_at = datetime.utcnow()
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def deactivate(self, db: AsyncSession, *, api_key_id: UUID, user_id: UUID) -> Optional[APIKey]:
        """Deactivate an API key (soft delete)."""
        db_obj = await self.get_with_provider(db, api_key_id=api_key_id, user_id=user_id)
        if db_obj:
            db_obj.is_active = False
            db_obj.updated_at = datetime.utcnow()
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj


api_key_service = APIKeyService()
