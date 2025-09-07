"""
User model preferences service for managing per-model parameter defaults.
Backed by user_model_configurations.configuration JSONB with RLS.
"""

import json
from typing import Optional
from uuid import UUID

from ..models.model_params import ModelParams
from ..utils.supabase_client import supabase_service


class UserModelPrefsService:
    """Service for managing user's per-model parameter preferences."""
    
    def __init__(self, supabase_client=None):
        """Initialize with optional Supabase client (for testing)."""
        self.supabase = supabase_client or supabase_service
    
    async def get_user_defaults(
        self, 
        user_id: UUID, 
        org_id: UUID, 
        model_id: str
    ) -> Optional[ModelParams]:
        """
        Get user's default parameters for a specific model.
        
        Args:
            user_id: User UUID
            org_id: Organization UUID  
            model_id: Model ID in format "provider/model"
            
        Returns:
            ModelParams if found, None otherwise
        """
        try:
            # Query user_model_configurations for this user+org+model
            response = self.supabase.table("user_model_configurations").select(
                "configuration"
            ).eq(
                "user_id", str(user_id)
            ).eq(
                "organization_id", str(org_id)
            ).eq(
                "model_id", model_id
            ).eq(
                "is_active", True
            ).limit(1).execute()
            
            if not response.data:
                return None
            
            config = response.data[0]["configuration"]
            if not config or not isinstance(config, dict):
                return None
            
            # Extract parameters from configuration
            params_data = config.get("default_params", {})
            if not params_data:
                return None
            
            return ModelParams.from_dict(params_data)
            
        except Exception as e:
            # Log error but don't fail - return None as fallback
            print(f"Error getting user defaults for {model_id}: {e}")
            return None
    
    async def upsert_user_defaults(
        self,
        user_id: UUID,
        org_id: UUID, 
        model_id: str,
        params: ModelParams
    ) -> bool:
        """
        Upsert user's default parameters for a specific model.
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
            model_id: Model ID in format "provider/model"  
            params: ModelParams to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, check if configuration exists
            existing_response = self.supabase.table("user_model_configurations").select(
                "id, configuration"
            ).eq(
                "user_id", str(user_id)
            ).eq(
                "organization_id", str(org_id)
            ).eq(
                "model_id", model_id
            ).eq(
                "is_active", True
            ).limit(1).execute()
            
            # Prepare configuration with default_params
            params_dict = params.to_dict(exclude_none=True)
            
            if existing_response.data:
                # Update existing configuration
                existing_config = existing_response.data[0]["configuration"] or {}
                existing_config["default_params"] = params_dict
                
                update_response = self.supabase.table("user_model_configurations").update({
                    "configuration": existing_config
                }).eq(
                    "id", existing_response.data[0]["id"]
                ).execute()
                
                return len(update_response.data) > 0
            else:
                # Create new configuration
                new_config = {
                    "default_params": params_dict,
                    "created_via": "parameter_override"
                }
                
                insert_response = self.supabase.table("user_model_configurations").insert({
                    "user_id": str(user_id),
                    "organization_id": str(org_id),
                    "model_id": model_id,
                    "configuration": new_config,
                    "is_active": True
                }).execute()
                
                return len(insert_response.data) > 0
                
        except Exception as e:
            print(f"Error upserting user defaults for {model_id}: {e}")
            return False
    
    async def get_session_defaults(
        self,
        session_id: UUID,
        supabase_client=None
    ) -> Optional[ModelParams]:
        """
        Get default parameters from session metadata.
        
        Args:
            session_id: Session UUID
            supabase_client: Optional user-scoped Supabase client
            
        Returns:
            ModelParams if found in session metadata, None otherwise
        """
        try:
            client = supabase_client or self.supabase
            
            response = client.table("chat_sessions").select(
                "metadata"
            ).eq(
                "id", str(session_id)
            ).limit(1).execute()
            
            if not response.data:
                return None
            
            metadata = response.data[0]["metadata"]
            if not metadata or not isinstance(metadata, dict):
                return None
            
            # Extract default_params from metadata
            params_data = metadata.get("default_params", {})
            if not params_data:
                return None
            
            return ModelParams.from_dict(params_data)
            
        except Exception as e:
            print(f"Error getting session defaults for {session_id}: {e}")
            return None
    
    async def update_session_defaults(
        self,
        session_id: UUID,
        params: ModelParams,
        supabase_client=None
    ) -> bool:
        """
        Update session metadata with default parameters.
        
        Args:
            session_id: Session UUID
            params: ModelParams to save in session metadata
            supabase_client: Optional user-scoped Supabase client
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = supabase_client or self.supabase
            
            # Get existing metadata
            response = client.table("chat_sessions").select(
                "metadata"
            ).eq(
                "id", str(session_id)
            ).limit(1).execute()
            
            if not response.data:
                return False
            
            metadata = response.data[0]["metadata"] or {}
            metadata["default_params"] = params.to_dict(exclude_none=True)
            
            # Update session metadata
            update_response = client.table("chat_sessions").update({
                "metadata": metadata
            }).eq(
                "id", str(session_id)
            ).execute()
            
            return len(update_response.data) > 0
            
        except Exception as e:
            print(f"Error updating session defaults for {session_id}: {e}")
            return False
    
    async def merge_all_defaults(
        self,
        user_id: UUID,
        org_id: UUID,
        model_id: str,
        session_id: Optional[UUID] = None,
        request_params: Optional[ModelParams] = None,
        supabase_client=None
    ) -> ModelParams:
        """
        Merge parameters from all sources with proper precedence.
        
        Precedence (highest to lowest):
        1. request_params (request-scoped overrides)
        2. session metadata defaults  
        3. user defaults for this model
        4. system defaults
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
            model_id: Model ID in format "provider/model"
            session_id: Optional session UUID for session defaults
            request_params: Optional request-scoped parameter overrides
            supabase_client: Optional user-scoped Supabase client
            
        Returns:
            Merged ModelParams with all defaults applied
        """
        # Start with system defaults (lowest precedence)
        merged = ModelParams.get_system_defaults()
        
        # Apply user defaults for this model
        user_defaults = await self.get_user_defaults(user_id, org_id, model_id)
        if user_defaults:
            merged = merged.merge_with(user_defaults)
        
        # Apply session defaults if session_id provided
        if session_id:
            session_defaults = await self.get_session_defaults(session_id, supabase_client)
            if session_defaults:
                merged = merged.merge_with(session_defaults)
        
        # Apply request overrides (highest precedence)
        if request_params:
            merged = merged.merge_with(request_params)
        
        return merged


# Global service instance
user_model_prefs_service = UserModelPrefsService()


# Convenience functions for common operations
async def get_user_defaults(user_id: UUID, org_id: UUID, model_id: str) -> Optional[ModelParams]:
    """Get user's default parameters for a model."""
    return await user_model_prefs_service.get_user_defaults(user_id, org_id, model_id)


async def upsert_user_defaults(user_id: UUID, org_id: UUID, model_id: str, params: ModelParams) -> bool:
    """Upsert user's default parameters for a model."""
    return await user_model_prefs_service.upsert_user_defaults(user_id, org_id, model_id, params)


async def merge_all_defaults(
    user_id: UUID,
    org_id: UUID, 
    model_id: str,
    session_id: Optional[UUID] = None,
    request_params: Optional[ModelParams] = None,
    supabase_client=None
) -> ModelParams:
    """Merge parameters from all sources with proper precedence."""
    return await user_model_prefs_service.merge_all_defaults(
        user_id, org_id, model_id, session_id, request_params, supabase_client
    )
