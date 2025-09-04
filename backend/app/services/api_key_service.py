from typing import List, Optional
from uuid import UUID
from datetime import datetime

from supabase import Client
from ..core.database import get_supabase_client
from ..utils.supabase_client import supabase_service
from ..models.api_key import APIKeyCreate, APIKeyUpdate, APIKeyDisplay, APIKeyValidationResult
from ..core.encryption import encryption_service
from .api_key_validator import api_key_validator


class APIKeyService:
    """Service for managing API keys with organization context"""
    
    def __init__(self):
        self.supabase: Client = get_supabase_client()

    async def create_with_encryption(
        self, 
        *, 
        obj_in: APIKeyCreate, 
        organization_id: UUID
    ) -> dict:
        """Create a new API key with encryption for an organization + provider."""
        # Encrypt the API key
        encrypted_key = encryption_service.encrypt_api_key(obj_in.api_key_value)
        key_prefix = encryption_service.get_key_prefix(obj_in.api_key_value)
        
        # Create the database object
        api_key_data = {
            "name": obj_in.name,
            "organization_id": str(organization_id),
            "provider_id": str(obj_in.provider_id),
            "encrypted_key_value": encrypted_key,
            "key_prefix": key_prefix,
            "is_active": True
        }
        
        result = supabase_service.table("api_keys").insert(api_key_data).execute()
        
        if not result.data:
            raise Exception("Failed to create API key")
        
        return result.data[0]

    async def validate_and_create(
        self,
        *,
        obj_in: APIKeyCreate,
        organization_id: UUID,
        validate_key: bool = True
    ) -> tuple[dict, Optional[APIKeyValidationResult]]:
        """Validate and create an API key for an organization + provider."""
        validation_result = None
        if validate_key:
            # Get provider name from provider_id for validation
            provider_response = supabase_service.table("ai_providers").select("name").eq("id", str(obj_in.provider_id)).execute()
            if not provider_response.data:
                raise ValueError(f"Provider with ID {obj_in.provider_id} not found")
            
            provider_name = provider_response.data[0]["name"]
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Provider name for validation: {provider_name}")
            logger.info(f"API key value (first 10 chars): {obj_in.api_key_value[:10]}...")
            
            # Validate the API key
            validation_result = await api_key_validator.validate_api_key(
                obj_in.api_key_value, 
                provider_name
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"API key validation failed: {validation_result.error_message}")
        
        # Create the API key
        api_key = await self.create_with_encryption(
            obj_in=obj_in, 
            organization_id=organization_id
        )
        
        return api_key, validation_result



    async def get_api_key(
        self, 
        *, 
        api_key_id: UUID, 
        organization_id: UUID
    ) -> Optional[dict]:
        """Get API key by ID for an organization."""
        result = self.supabase.table("api_keys").select("*").eq("id", str(api_key_id)).eq("organization_id", str(organization_id)).execute()
        
        if not result.data:
            return None
        
        return result.data[0]

    async def get_organization_keys(
        self, 
        *, 
        organization_id: UUID
    ) -> List[APIKeyDisplay]:
        """Get organization's API keys for display."""
        result = supabase_service.table("api_keys").select("*").eq("organization_id", str(organization_id)).eq("is_active", True).execute()
        
        display_keys = []
        for api_key in result.data:
            # Get provider information from provider_id
            provider_response = supabase_service.table("ai_providers").select("name, display_name").eq("id", api_key["provider_id"]).execute()
            provider_name = "Unknown"
            provider_display_name = "Unknown"
            if provider_response.data:
                provider_name = provider_response.data[0]["name"]
                provider_display_name = provider_response.data[0]["display_name"]
            
            # Decrypt key for masking
            try:
                decrypted_key = encryption_service.decrypt_api_key(api_key["encrypted_key_value"])
                masked_key = encryption_service.mask_api_key(decrypted_key)
            except Exception:
                masked_key = "****"
            
            display_keys.append(APIKeyDisplay(
                id=UUID(api_key["id"]),
                name=api_key["name"],
                provider_name=provider_name,
                provider_display_name=provider_display_name,
                key_prefix=api_key["key_prefix"],
                masked_key=masked_key,
                is_active=api_key["is_active"],
                last_used_at=api_key.get("last_used_at"),
                created_at=api_key["created_at"],
                updated_at=api_key["updated_at"]
            ))
        
        return display_keys

    async def get_decrypted_key(
        self, 
        *, 
        api_key_id: UUID, 
        organization_id: UUID
    ) -> Optional[str]:
        """Get decrypted API key value for use."""
        api_key = await self.get_api_key(
            api_key_id=api_key_id, 
            organization_id=organization_id
        )
        if not api_key or not api_key["is_active"]:
            return None
        
        try:
            decrypted_key = encryption_service.decrypt_api_key(api_key["encrypted_key_value"])
            # Update last used timestamp
            await self.update_last_used(api_key_id=api_key_id)
            return decrypted_key
        except Exception:
            return None

    async def get_by_provider(
        self, 
        *, 
        organization_id: UUID, 
        provider_id: UUID
    ) -> Optional[dict]:
        """Get API key for a specific organization + provider combination."""
        result = self.supabase.table("api_keys").select("*").eq("organization_id", str(organization_id)).eq("provider_id", str(provider_id)).eq("is_active", True).execute()
        
        if not result.data:
            return None
        
        return result.data[0]

    async def get_organization_keys_raw(self, organization_id: UUID) -> List[dict]:
        """Get all active API keys for an organization (raw data)."""
        result = supabase_service.table("api_keys").select("*").eq("organization_id", str(organization_id)).eq("is_active", True).execute()
        return result.data or []



    async def get_with_provider(
        self, 
        *, 
        api_key_id: UUID, 
        organization_id: UUID
    ) -> Optional[dict]:
        """Get API key with provider information."""
        result = self.supabase.table("api_keys").select("*").eq("id", str(api_key_id)).eq("organization_id", str(organization_id)).execute()
        
        if not result.data:
            return None
        
        return result.data[0]

    async def update_last_used(self, *, api_key_id: UUID) -> bool:
        """Update the last_used_at timestamp for an API key."""
        try:
            result = self.supabase.table("api_keys").update({
                "last_used_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(api_key_id)).execute()
            
            return bool(result.data)
        except Exception:
            return False

    async def deactivate(self, *, api_key_id: UUID, organization_id: UUID) -> bool:
        """Deactivate an API key (soft delete)."""
        try:
            result = self.supabase.table("api_keys").update({
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(api_key_id)).eq("organization_id", str(organization_id)).execute()
            
            return bool(result.data)
        except Exception:
            return False

    async def update_api_key(
        self, 
        *, 
        api_key_id: UUID, 
        update_data: APIKeyUpdate,
        organization_id: UUID
    ) -> Optional[dict]:
        """Update an API key."""
        try:
            update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items()}
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("api_keys").update(update_dict).eq("id", str(api_key_id)).eq("organization_id", str(organization_id)).execute()
            
            if not result.data:
                return None
            
            return result.data[0]
        except Exception:
            return None


api_key_service = APIKeyService()
