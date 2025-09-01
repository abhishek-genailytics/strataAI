import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from app.services.cost_calculation_service import CostCalculationService


class TestCostCalculationService:
    
    @pytest.fixture
    def cost_service(self):
        return CostCalculationService()
    
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = MagicMock()
        return db
    
    def test_estimate_tokens(self, cost_service):
        """Test token estimation."""
        text = "Hello world"
        tokens = cost_service.estimate_tokens(text)
        assert tokens == 2  # "Hello world" ≈ 2 tokens
        
        # Test empty string
        tokens = cost_service.estimate_tokens("")
        assert tokens == 1  # Minimum 1 token
    
    @pytest.mark.asyncio
    async def test_calculate_cost_with_database_pricing(self, cost_service, mock_db):
        """Test cost calculation using pricing from database."""
        provider_id = uuid4()
        
        # Mock model lookup
        mock_model = MagicMock()
        mock_model.id = uuid4()
        
        # Mock pricing lookup
        mock_pricing_input = MagicMock()
        mock_pricing_input.pricing_type = "input"
        mock_pricing_input.price_per_unit = Decimal('0.03')
        
        mock_pricing_output = MagicMock()
        mock_pricing_output.pricing_type = "output"
        mock_pricing_output.price_per_unit = Decimal('0.06')
        
        # Mock database responses
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_model)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_pricing_input, mock_pricing_output]))))
        ]
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Expected: (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.03 + 0.03 = 0.06
        expected_cost = Decimal('0.060000')
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_calculate_cost_with_default_pricing(self, cost_service, mock_db):
        """Test cost calculation using default pricing when database has no pricing."""
        provider_id = uuid4()
        
        # Mock no model found
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=MagicMock(name="openai")))))
        ]
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Should use default pricing: (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.06
        expected_cost = Decimal('0.060000')
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_calculate_cost_unknown_model(self, cost_service, mock_db):
        """Test cost calculation for unknown model returns zero cost."""
        provider_id = uuid4()
        
        # Mock no model found and no provider found
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))
        ]
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="unknown-model",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert cost == Decimal('0')
    
    @pytest.mark.asyncio
    async def test_calculate_cost_anthropic_model(self, cost_service, mock_db):
        """Test cost calculation for Anthropic model."""
        provider_id = uuid4()
        
        # Mock no model found, but provider found
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=MagicMock(name="anthropic")))))
        ]
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="claude-3-opus",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Default pricing: (1000/1000 * 0.015) + (500/1000 * 0.075) = 0.015 + 0.0375 = 0.0525
        expected_cost = Decimal('0.052500')
        assert cost == expected_cost
    
    @pytest.mark.asyncio
    async def test_calculate_cost_zero_tokens(self, cost_service, mock_db):
        """Test cost calculation with zero tokens."""
        provider_id = uuid4()
        
        # Mock no model found, but provider found
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=MagicMock(name="openai")))))
        ]
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="gpt-4",
            input_tokens=0,
            output_tokens=0
        )
        
        assert cost == Decimal('0')
    
    def test_get_model_pricing_info(self, cost_service):
        """Test getting model pricing info from default pricing."""
        pricing = cost_service.get_model_pricing_info("openai", "gpt-4")
        assert pricing == {"input": 0.03, "output": 0.06}
        
        pricing = cost_service.get_model_pricing_info("anthropic", "claude-3-opus")
        assert pricing == {"input": 0.015, "output": 0.075}
        
        # Test unknown provider
        pricing = cost_service.get_model_pricing_info("unknown", "gpt-4")
        assert pricing is None
        
        # Test unknown model
        pricing = cost_service.get_model_pricing_info("openai", "unknown-model")
        assert pricing is None
