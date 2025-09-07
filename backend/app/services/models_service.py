"""
Models service for playground models listing with filtering and availability logic.
"""
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import logging

from ..models.playground_models import (
    PlaygroundModel, 
    PlaygroundModelsResponse, 
    ModelCapabilities, 
    ModelLimits, 
    PricingInfo, 
    ModelPricing, 
    ModelAvailability
)
from ..utils.supabase_client import supabase_service
from ..core.deps import CurrentUser

logger = logging.getLogger(__name__)


class ModelsService:
    """Service for managing playground models listing."""
    
    def __init__(self):
        self.sb = supabase_service
    
    async def list_models(
        self,
        current_user: CurrentUser,
        current_org_id: UUID,
        model_type: str = "chat",
        provider: Optional[str] = None,
        include_pricing: bool = True,
        include_capabilities: bool = True
    ) -> PlaygroundModelsResponse:
        """
        List models available to user in playground with filtering and availability.
        
        Args:
            current_user: Authenticated user
            current_org_id: Current organization ID
            model_type: Model type filter (default: "chat")
            provider: Optional provider filter (openai, anthropic, etc.)
            include_pricing: Include pricing information
            include_capabilities: Include capabilities information
            
        Returns:
            PlaygroundModelsResponse with filtered and enriched models
        """
        logger.info(f"Listing models for user {current_user.user_id} in org {current_org_id}")
        
        # 1. Get base catalog with provider info
        models_data = await self._get_base_catalog(model_type, provider)
        
        # 2. Get pricing data (if requested)
        pricing_data = {}
        if include_pricing and models_data:
            model_ids = [model['id'] for model in models_data]
            pricing_data = await self._get_pricing_data(model_ids)
        
        # 3. Get organization and user context data
        org_api_keys = await self._get_org_api_keys(current_org_id)
        org_enablement = await self._get_org_model_enablement(current_org_id)
        user_configs = await self._get_user_model_configurations(current_user.user_id, current_org_id)
        
        # 4. Build response models
        playground_models = []
        for model_data in models_data:
            playground_model = await self._build_playground_model(
                model_data=model_data,
                pricing_data=pricing_data,
                org_api_keys=org_api_keys,
                org_enablement=org_enablement,
                user_configs=user_configs,
                include_pricing=include_pricing,
                include_capabilities=include_capabilities
            )
            playground_models.append(playground_model)
        
        # 5. Build response
        response = PlaygroundModelsResponse(
            data=playground_models,
            meta={
                "org_id": str(current_org_id),
                "count": len(playground_models),
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Returning {len(playground_models)} models")
        return response
    
    async def _get_base_catalog(self, model_type: str, provider: Optional[str]) -> List[Dict[str, Any]]:
        """Get base model catalog with provider information."""
        query = self.sb.table("ai_models")\
            .select("""
                id,
                provider_id,
                model_name,
                display_name,
                model_type,
                max_tokens,
                max_input_tokens,
                supports_streaming,
                supports_function_calling,
                supports_vision,
                supports_audio,
                metadata,
                ai_providers!inner(
                    id,
                    name,
                    display_name
                )
            """)\
            .eq("model_type", model_type)\
            .eq("is_active", True)\
            .eq("ai_providers.is_active", True)
        
        if provider:
            query = query.eq("ai_providers.name", provider)
        
        response = query.execute()
        
        if not response.data:
            logger.warning(f"No models found for type={model_type}, provider={provider}")
            return []
        
        logger.info(f"Found {len(response.data)} models in catalog")
        return response.data
    
    async def _get_pricing_data(self, model_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get pricing data for models."""
        if not model_ids:
            return {}
        
        # Get active pricing for all models with temporal filtering
        current_time = datetime.utcnow().isoformat()
        response = self.sb.table("model_pricing")\
            .select("model_id, pricing_type, price_per_unit, unit, currency")\
            .in_("model_id", model_ids)\
            .eq("is_active", True)\
            .lte("effective_from", current_time)\
            .or_(f"effective_until.is.null,effective_until.gt.{current_time}")\
            .execute()
        
        if not response.data:
            logger.warning(f"No pricing data found for {len(model_ids)} models")
            return {}
        
        # Group by model_id and pricing_type
        pricing_by_model = {}
        for pricing in response.data:
            model_id = pricing["model_id"]
            pricing_type = pricing["pricing_type"]
            
            if model_id not in pricing_by_model:
                pricing_by_model[model_id] = {}
            
            pricing_by_model[model_id][pricing_type] = {
                "price": Decimal(str(pricing["price_per_unit"])),
                "unit": pricing["unit"],
                "currency": pricing["currency"]
            }
        
        logger.info(f"Loaded pricing for {len(pricing_by_model)} models")
        return pricing_by_model
    
    async def _get_org_api_keys(self, org_id: UUID) -> Dict[str, bool]:
        """Get organization's active API keys by provider."""
        response = self.sb.table("api_keys")\
            .select("""
                provider_id,
                ai_providers!inner(name)
            """)\
            .eq("organization_id", str(org_id))\
            .eq("is_active", True)\
            .execute()
        
        if not response.data:
            logger.info(f"No API keys found for org {org_id}")
            return {}
        
        # Map provider name to has_key
        api_keys_by_provider = {}
        for key_data in response.data:
            provider_name = key_data["ai_providers"]["name"]
            api_keys_by_provider[provider_name] = True
        
        logger.info(f"Found API keys for providers: {list(api_keys_by_provider.keys())}")
        return api_keys_by_provider
    
    async def _get_org_model_enablement(self, org_id: UUID) -> Dict[str, bool]:
        """Get organization model enablement settings."""
        response = self.sb.table("org_model_enablement")\
            .select("model_id, is_enabled")\
            .eq("organization_id", str(org_id))\
            .execute()
        
        if not response.data:
            logger.info(f"No org model enablement found for org {org_id}")
            return {}
        
        # Map model_id to is_enabled
        enablement_by_model = {}
        for enablement in response.data:
            enablement_by_model[enablement["model_id"]] = enablement["is_enabled"]
        
        logger.info(f"Found enablement settings for {len(enablement_by_model)} models")
        return enablement_by_model
    
    async def _get_user_model_configurations(self, user_id: UUID, org_id: UUID) -> Dict[str, Dict[str, Any]]:
        """Get user model configurations."""
        response = self.sb.table("user_model_configurations")\
            .select("model_id, is_enabled, configuration")\
            .eq("user_id", str(user_id))\
            .eq("organization_id", str(org_id))\
            .execute()
        
        if not response.data:
            logger.info(f"No user model configs found for user {user_id}")
            return {}
        
        # Map model_id to config
        configs_by_model = {}
        for config in response.data:
            configs_by_model[config["model_id"]] = {
                "is_enabled": config["is_enabled"],
                "configuration": config["configuration"] or {},
                "is_default": config["configuration"].get("is_default", False) if config["configuration"] else False
            }
        
        logger.info(f"Found user configs for {len(configs_by_model)} models")
        return configs_by_model
    
    async def _build_playground_model(
        self,
        model_data: Dict[str, Any],
        pricing_data: Dict[str, Dict[str, Any]],
        org_api_keys: Dict[str, bool],
        org_enablement: Dict[str, bool],
        user_configs: Dict[str, Dict[str, Any]],
        include_pricing: bool,
        include_capabilities: bool
    ) -> PlaygroundModel:
        """Build a single PlaygroundModel from raw data."""
        model_id = model_data["id"]
        provider_name = model_data["ai_providers"]["name"]
        model_name = model_data["model_name"]
        
        # Build model ID in "provider/model" format
        playground_model_id = f"{provider_name}/{model_name}"
        
        # Build capabilities
        capabilities = None
        if include_capabilities:
            capabilities = ModelCapabilities(
                supports_streaming=model_data.get("supports_streaming", False),
                supports_function_calling=model_data.get("supports_function_calling", False),
                vision=model_data.get("supports_vision", False)
            )
        
        # Build limits
        limits = ModelLimits(
            max_input_tokens=model_data.get("max_input_tokens"),
            max_output_tokens=model_data.get("max_tokens")
        )
        
        # Build pricing
        pricing = None
        if include_pricing and model_id in pricing_data:
            model_pricing_data = pricing_data[model_id]
            pricing = ModelPricing()
            
            if "input" in model_pricing_data:
                input_pricing = model_pricing_data["input"]
                pricing.input = PricingInfo(
                    unit=input_pricing["unit"],
                    price=input_pricing["price"],
                    currency=input_pricing["currency"]
                )
            
            if "output" in model_pricing_data:
                output_pricing = model_pricing_data["output"]
                pricing.output = PricingInfo(
                    unit=output_pricing["unit"],
                    price=output_pricing["price"],
                    currency=output_pricing["currency"]
                )
        
        # Build availability
        availability = self._build_availability(
            model_id=model_id,
            provider_name=provider_name,
            org_api_keys=org_api_keys,
            org_enablement=org_enablement,
            user_configs=user_configs
        )
        
        # Check if this is user's default
        user_config = user_configs.get(model_id, {})
        is_default_for_user = user_config.get("is_default", False)
        
        return PlaygroundModel(
            id=playground_model_id,
            provider=provider_name,
            model_name=model_name,
            display_name=model_data["display_name"],
            type=model_data["model_type"],
            capabilities=capabilities,
            limits=limits,
            pricing=pricing,
            availability=availability,
            is_default_for_user=is_default_for_user,
            metadata=model_data.get("metadata", {})
        )
    
    def _build_availability(
        self,
        model_id: str,
        provider_name: str,
        org_api_keys: Dict[str, bool],
        org_enablement: Dict[str, bool],
        user_configs: Dict[str, Dict[str, Any]]
    ) -> ModelAvailability:
        """Build availability information for a model."""
        # Check org enablement (default to enabled if not specified)
        org_enabled = org_enablement.get(model_id, True)
        locked_reason = None
        
        if not org_enabled:
            locked_reason = "disabled_by_org"
        
        # Check API key availability
        has_org_api_key = org_api_keys.get(provider_name, False)
        if not has_org_api_key and not locked_reason:
            locked_reason = "missing_org_api_key"
        
        # Check user enablement (default to enabled if not specified)
        user_config = user_configs.get(model_id, {})
        user_enabled = user_config.get("is_enabled", True)
        
        return ModelAvailability(
            org_enabled=org_enabled,
            has_org_api_key=has_org_api_key,
            user_enabled=user_enabled,
            locked_reason=locked_reason
        )
