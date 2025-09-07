"""
Tests for playground models listing endpoint.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from app.services.models_service import ModelsService
from app.models.playground_models import PlaygroundModelsResponse, PlaygroundModel, ModelAvailability
from app.core.deps import CurrentUser


class TestPlaygroundModelsEndpoint:
    """Test cases for GET /playground/models endpoint."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock current user."""
        return CurrentUser(
            user_id=uuid4(),
            email="test@example.com",
            organizations=[{
                'id': str(uuid4()),
                'name': 'test-org',
                'role': 'admin'
            }]
        )
    
    @pytest.fixture
    def mock_org_id(self):
        """Mock organization ID."""
        return uuid4()
    
    @pytest.fixture
    def models_service(self):
        """Models service instance."""
        return ModelsService()
    
    @pytest.mark.asyncio
    async def test_list_models_basic(self, models_service, mock_user, mock_org_id):
        """Test basic models listing functionality."""
        # Mock the database responses
        with patch.object(models_service, '_get_base_catalog') as mock_catalog, \
             patch.object(models_service, '_get_pricing_data') as mock_pricing, \
             patch.object(models_service, '_get_org_api_keys') as mock_keys, \
             patch.object(models_service, '_get_org_model_enablement') as mock_enablement, \
             patch.object(models_service, '_get_user_model_configurations') as mock_configs:
            
            # Setup mock data
            model_id = str(uuid4())
            provider_id = str(uuid4())
            
            mock_catalog.return_value = [{
                'id': model_id,
                'provider_id': provider_id,
                'model_name': 'gpt-4o-mini',
                'display_name': 'GPT-4o mini',
                'model_type': 'chat',
                'max_tokens': 4096,
                'max_input_tokens': 128000,
                'supports_streaming': True,
                'supports_function_calling': True,
                'supports_vision': False,
                'supports_audio': False,
                'metadata': {},
                'ai_providers': {
                    'id': provider_id,
                    'name': 'openai',
                    'display_name': 'OpenAI'
                }
            }]
            
            mock_pricing.return_value = {
                model_id: {
                    'input': {
                        'price': Decimal('0.000003'),
                        'unit': 'token',
                        'currency': 'USD'
                    },
                    'output': {
                        'price': Decimal('0.000015'),
                        'unit': 'token',
                        'currency': 'USD'
                    }
                }
            }
            
            mock_keys.return_value = {'openai': True}
            mock_enablement.return_value = {}  # Default enabled
            mock_configs.return_value = {}  # Default enabled
            
            # Call the service
            response = await models_service.list_models(
                current_user=mock_user,
                current_org_id=mock_org_id,
                model_type="chat",
                provider=None,
                include_pricing=True,
                include_capabilities=True
            )
            
            # Assertions
            assert isinstance(response, PlaygroundModelsResponse)
            assert len(response.data) == 1
            
            model = response.data[0]
            assert model.id == "openai/gpt-4o-mini"
            assert model.provider == "openai"
            assert model.model_name == "gpt-4o-mini"
            assert model.display_name == "GPT-4o mini"
            assert model.type == "chat"
            
            # Check capabilities
            assert model.capabilities is not None
            assert model.capabilities.supports_streaming is True
            assert model.capabilities.supports_function_calling is True
            assert model.capabilities.vision is False
            
            # Check limits
            assert model.limits is not None
            assert model.limits.max_input_tokens == 128000
            assert model.limits.max_output_tokens == 4096
            
            # Check pricing
            assert model.pricing is not None
            assert model.pricing.input is not None
            assert model.pricing.input.price == Decimal('0.000003')
            assert model.pricing.input.unit == "token"
            assert model.pricing.output is not None
            assert model.pricing.output.price == Decimal('0.000015')
            
            # Check availability
            assert model.availability.org_enabled is True
            assert model.availability.has_org_api_key is True
            assert model.availability.user_enabled is True
            assert model.availability.locked_reason is None
            
            # Check metadata
            assert response.meta["org_id"] == str(mock_org_id)
            assert response.meta["count"] == 1
            assert "generated_at" in response.meta
    
    @pytest.mark.asyncio
    async def test_list_models_missing_api_key(self, models_service, mock_user, mock_org_id):
        """Test models listing when API key is missing."""
        with patch.object(models_service, '_get_base_catalog') as mock_catalog, \
             patch.object(models_service, '_get_pricing_data') as mock_pricing, \
             patch.object(models_service, '_get_org_api_keys') as mock_keys, \
             patch.object(models_service, '_get_org_model_enablement') as mock_enablement, \
             patch.object(models_service, '_get_user_model_configurations') as mock_configs:
            
            model_id = str(uuid4())
            mock_catalog.return_value = [{
                'id': model_id,
                'provider_id': str(uuid4()),
                'model_name': 'claude-3-haiku',
                'display_name': 'Claude 3 Haiku',
                'model_type': 'chat',
                'max_tokens': 4096,
                'max_input_tokens': 200000,
                'supports_streaming': True,
                'supports_function_calling': False,
                'supports_vision': True,
                'supports_audio': False,
                'metadata': {},
                'ai_providers': {
                    'name': 'anthropic',
                    'display_name': 'Anthropic'
                }
            }]
            
            mock_pricing.return_value = {}
            mock_keys.return_value = {}  # No API key for anthropic
            mock_enablement.return_value = {}
            mock_configs.return_value = {}
            
            response = await models_service.list_models(
                current_user=mock_user,
                current_org_id=mock_org_id
            )
            
            model = response.data[0]
            assert model.availability.has_org_api_key is False
            assert model.availability.locked_reason == "missing_org_api_key"
    
    @pytest.mark.asyncio
    async def test_list_models_org_disabled(self, models_service, mock_user, mock_org_id):
        """Test models listing when model is disabled by organization."""
        with patch.object(models_service, '_get_base_catalog') as mock_catalog, \
             patch.object(models_service, '_get_pricing_data') as mock_pricing, \
             patch.object(models_service, '_get_org_api_keys') as mock_keys, \
             patch.object(models_service, '_get_org_model_enablement') as mock_enablement, \
             patch.object(models_service, '_get_user_model_configurations') as mock_configs:
            
            model_id = str(uuid4())
            mock_catalog.return_value = [{
                'id': model_id,
                'provider_id': str(uuid4()),
                'model_name': 'gpt-4',
                'display_name': 'GPT-4',
                'model_type': 'chat',
                'max_tokens': 4096,
                'max_input_tokens': 8192,
                'supports_streaming': True,
                'supports_function_calling': True,
                'supports_vision': False,
                'supports_audio': False,
                'metadata': {},
                'ai_providers': {
                    'name': 'openai',
                    'display_name': 'OpenAI'
                }
            }]
            
            mock_pricing.return_value = {}
            mock_keys.return_value = {'openai': True}
            mock_enablement.return_value = {model_id: False}  # Disabled by org
            mock_configs.return_value = {}
            
            response = await models_service.list_models(
                current_user=mock_user,
                current_org_id=mock_org_id
            )
            
            model = response.data[0]
            assert model.availability.org_enabled is False
            assert model.availability.locked_reason == "disabled_by_org"
    
    @pytest.mark.asyncio
    async def test_list_models_provider_filter(self, models_service, mock_user, mock_org_id):
        """Test models listing with provider filter."""
        with patch.object(models_service, '_get_base_catalog') as mock_catalog, \
             patch.object(models_service, '_get_pricing_data') as mock_pricing, \
             patch.object(models_service, '_get_org_api_keys') as mock_keys, \
             patch.object(models_service, '_get_org_model_enablement') as mock_enablement, \
             patch.object(models_service, '_get_user_model_configurations') as mock_configs:
            
            # Setup mocks
            mock_catalog.return_value = []  # Provider filter should be applied in query
            mock_pricing.return_value = {}
            mock_keys.return_value = {}
            mock_enablement.return_value = {}
            mock_configs.return_value = {}
            
            await models_service.list_models(
                current_user=mock_user,
                current_org_id=mock_org_id,
                provider="openai"
            )
            
            # Verify provider filter was passed to catalog query
            mock_catalog.assert_called_once_with("chat", "openai")
    
    @pytest.mark.asyncio
    async def test_list_models_no_pricing(self, models_service, mock_user, mock_org_id):
        """Test models listing without pricing information."""
        with patch.object(models_service, '_get_base_catalog') as mock_catalog, \
             patch.object(models_service, '_get_pricing_data') as mock_pricing, \
             patch.object(models_service, '_get_org_api_keys') as mock_keys, \
             patch.object(models_service, '_get_org_model_enablement') as mock_enablement, \
             patch.object(models_service, '_get_user_model_configurations') as mock_configs:
            
            model_id = str(uuid4())
            mock_catalog.return_value = [{
                'id': model_id,
                'provider_id': str(uuid4()),
                'model_name': 'test-model',
                'display_name': 'Test Model',
                'model_type': 'chat',
                'max_tokens': 1000,
                'max_input_tokens': 2000,
                'supports_streaming': False,
                'supports_function_calling': False,
                'supports_vision': False,
                'supports_audio': False,
                'metadata': {},
                'ai_providers': {
                    'name': 'test-provider',
                    'display_name': 'Test Provider'
                }
            }]
            
            mock_pricing.return_value = {}
            mock_keys.return_value = {'test-provider': True}
            mock_enablement.return_value = {}
            mock_configs.return_value = {}
            
            response = await models_service.list_models(
                current_user=mock_user,
                current_org_id=mock_org_id,
                include_pricing=False
            )
            
            model = response.data[0]
            assert model.pricing is None
            
            # Verify pricing data was not fetched
            mock_pricing.assert_not_called()


class TestModelsServiceEdgeCases:
    """Test edge cases for ModelsService."""
    
    @pytest.fixture
    def models_service(self):
        return ModelsService()
    
    @pytest.mark.asyncio
    async def test_empty_catalog(self, models_service):
        """Test handling of empty model catalog."""
        with patch.object(models_service, '_get_base_catalog', return_value=[]):
            mock_user = CurrentUser(uuid4(), "test@example.com")
            mock_org_id = uuid4()
            
            response = await models_service.list_models(mock_user, mock_org_id)
            
            assert len(response.data) == 0
            assert response.meta["count"] == 0
    
    def test_build_availability_logic(self, models_service):
        """Test availability logic combinations."""
        # Test case 1: All enabled
        availability = models_service._build_availability(
            model_id="test-model",
            provider_name="openai",
            org_api_keys={"openai": True},
            org_enablement={},  # Default enabled
            user_configs={}  # Default enabled
        )
        assert availability.org_enabled is True
        assert availability.has_org_api_key is True
        assert availability.user_enabled is True
        assert availability.locked_reason is None
        
        # Test case 2: Org disabled takes precedence
        availability = models_service._build_availability(
            model_id="test-model",
            provider_name="openai",
            org_api_keys={"openai": True},
            org_enablement={"test-model": False},
            user_configs={}
        )
        assert availability.org_enabled is False
        assert availability.locked_reason == "disabled_by_org"
        
        # Test case 3: Missing API key
        availability = models_service._build_availability(
            model_id="test-model",
            provider_name="anthropic",
            org_api_keys={},  # No API key
            org_enablement={},
            user_configs={}
        )
        assert availability.has_org_api_key is False
        assert availability.locked_reason == "missing_org_api_key"
        
        # Test case 4: User disabled (but still usable)
        availability = models_service._build_availability(
            model_id="test-model",
            provider_name="openai",
            org_api_keys={"openai": True},
            org_enablement={},
            user_configs={"test-model": {"is_enabled": False}}
        )
        assert availability.user_enabled is False
        assert availability.locked_reason is None  # User preference doesn't lock
