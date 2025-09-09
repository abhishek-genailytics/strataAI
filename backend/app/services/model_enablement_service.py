"""
Service for managing organization model enablement.
"""
from typing import List, Dict, Any
from uuid import UUID
import logging

from ..utils.supabase_client import supabase_service
from ..models.model_enablement import EnableModelsRequest, EnableModelsResponse

logger = logging.getLogger(__name__)


class ModelEnablementService:
    """Service for managing organization model enablement."""
    
    def __init__(self):
        self.sb = supabase_service
    
    async def enable_models_for_organization(
        self,
        organization_id: UUID,
        request: EnableModelsRequest
    ) -> EnableModelsResponse:
        """
        Enable selected models for an organization by saving to org_model_enablement table.
        
        Args:
            organization_id: Organization UUID
            request: EnableModelsRequest with provider and model_ids
            
        Returns:
            EnableModelsResponse with success details
        """
        logger.info(f"Enabling {len(request.model_ids)} models for org {organization_id}, provider {request.provider}")
        
        # 1. Validate provider exists and get provider_id
        provider_id = await self._validate_provider_and_models(request.provider, request.model_ids)
        
        # 2. Clear existing enablement for this organization + provider combination
        # This ensures we only enable the selected models and disable others
        await self._clear_provider_enablement(organization_id, provider_id)
        
        # 4. Insert new enablement records
        enablement_records = []
        for model_id in request.model_ids:
            enablement_records.append({
                "organization_id": str(organization_id),
                "model_id": model_id,
                "is_enabled": True
            })
        
        if enablement_records:
            insert_response = self.sb.table("org_model_enablement")\
                .insert(enablement_records)\
                .execute()
            
            if not insert_response.data:
                raise Exception("Failed to insert model enablement records")
        
        logger.info(f"Successfully enabled {len(request.model_ids)} models for org {organization_id}")
        
        return EnableModelsResponse(
            message=f"Successfully enabled {len(request.model_ids)} models",
            enabled_count=len(request.model_ids),
            provider_id=provider_id,
            model_ids=request.model_ids
        )
    
    async def _validate_provider_and_models(self, provider_id: str, model_ids: List[str]) -> str:
        """
        Validate that provider exists and all model IDs are valid for that provider.
        
        Args:
            provider_id: ID of the provider (UUID string)
            model_ids: List of model IDs to validate
            
        Returns:
            Provider UUID string
            
        Raises:
            ValueError: If provider not found or model IDs are invalid
        """
        # 1. Get provider by ID
        provider_response = self.sb.table("ai_providers")\
            .select("id, name")\
            .eq("id", provider_id)\
            .eq("is_active", True)\
            .execute()
        
        if not provider_response.data:
            raise ValueError(f"Provider '{provider_id}' not found or inactive")
        
        provider_id = provider_response.data[0]["id"]
        
        # 2. Validate all model IDs exist for this provider
        models_response = self.sb.table("ai_models")\
            .select("id")\
            .eq("provider_id", provider_id)\
            .eq("is_active", True)\
            .in_("id", model_ids)\
            .execute()
        
        if len(models_response.data) != len(model_ids):
            found_ids = [m["id"] for m in models_response.data]
            missing_ids = [mid for mid in model_ids if mid not in found_ids]
            raise ValueError(f"Invalid model IDs for provider {provider_id}: {missing_ids}")
        
        return provider_id
    
    async def _clear_provider_enablement(self, organization_id: UUID, provider_id: str) -> None:
        """Clear existing enablement records for organization + provider."""
        # Get all models for this provider
        models_response = self.sb.table("ai_models")\
            .select("id")\
            .eq("provider_id", provider_id)\
            .execute()
        
        if not models_response.data:
            return
        
        model_ids = [m["id"] for m in models_response.data]
        
        # Delete existing enablement records for these models
        delete_response = self.sb.table("org_model_enablement")\
            .delete()\
            .eq("organization_id", str(organization_id))\
            .in_("model_id", model_ids)\
            .execute()
        
        logger.info(f"Cleared existing enablement for org {organization_id}, provider {provider_id}")
    
    async def get_enabled_models_for_provider(
        self,
        organization_id: UUID,
        provider_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get enabled models for an organization + provider combination.
        
        Args:
            organization_id: Organization UUID
            provider_id: Provider UUID
            
        Returns:
            List of enabled model data with details
        """
        logger.info(f"Getting enabled models for org {organization_id}, provider {provider_id}")
        
        # First, get the provider UUID from name if needed
        provider_uuid = provider_id
        if not provider_id.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f')):
            # Looks like a name, not UUID - convert to UUID
            provider_lookup = self.sb.table("ai_providers")\
                .select("id")\
                .eq("name", provider_id)\
                .eq("is_active", True)\
                .execute()
            
            if provider_lookup.data:
                provider_uuid = provider_lookup.data[0]["id"]
            else:
                logger.warning(f"Provider {provider_id} not found")
                return []

        # Get enabled models with full model details
        response = self.sb.table("org_model_enablement")\
            .select("""
                model_id,
                is_enabled,
                created_at,
                ai_models!inner(
                    id,
                    model_name,
                    display_name,
                    description,
                    model_type,
                    max_tokens,
                    max_input_tokens,
                    supports_streaming,
                    supports_function_calling,
                    supports_vision,
                    metadata,
                    provider_id
                )
            """)\
            .eq("organization_id", str(organization_id))\
            .eq("is_enabled", True)\
            .eq("ai_models.provider_id", provider_uuid)\
            .eq("ai_models.is_active", True)\
            .execute()
        
        if not response.data:
            logger.info(f"No enabled models found for org {organization_id}, provider {provider_id}")
            return []
        
        # Transform the response to flatten the model data
        enabled_models = []
        for record in response.data:
            model_data = record["ai_models"]
            enabled_models.append({
                "id": model_data["id"],
                "model_name": model_data["model_name"],
                "display_name": model_data["display_name"],
                "description": model_data.get("description"),
                "model_type": model_data["model_type"],
                "max_tokens": model_data.get("max_tokens"),
                "max_input_tokens": model_data.get("max_input_tokens"),
                "supports_streaming": model_data.get("supports_streaming", False),
                "supports_function_calling": model_data.get("supports_function_calling", False),
                "supports_vision": model_data.get("supports_vision", False),
                "metadata": model_data.get("metadata", {}),
                "enabled_at": record["created_at"]
            })
        
        logger.info(f"Found {len(enabled_models)} enabled models for org {organization_id}, provider {provider_id}")
        return enabled_models


model_enablement_service = ModelEnablementService()
