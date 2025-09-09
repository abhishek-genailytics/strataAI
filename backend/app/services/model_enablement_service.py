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
        provider_response = self.sb.table("ai_providers")\
            .select("id")\
            .eq("id", request.provider)\
            .eq("is_active", True)\
            .execute()
        
        if not provider_response.data:
            raise ValueError(f"Provider {request.provider} not found or inactive")
        
        provider_id = provider_response.data[0]["id"]
        
        # 2. Validate all model_ids exist and belong to the provider
        models_response = self.sb.table("ai_models")\
            .select("id")\
            .eq("provider_id", provider_id)\
            .in_("id", request.model_ids)\
            .eq("is_active", True)\
            .execute()
        
        if len(models_response.data) != len(request.model_ids):
            found_ids = [m["id"] for m in models_response.data]
            missing_ids = [mid for mid in request.model_ids if mid not in found_ids]
            raise ValueError(f"Invalid model IDs for provider {request.provider}: {missing_ids}")
        
        # 3. Clear existing enablement for this organization + provider combination
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
                    metadata
                )
            """)\
            .eq("organization_id", str(organization_id))\
            .eq("is_enabled", True)\
            .eq("ai_models.provider_id", provider_id)\
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
