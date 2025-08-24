import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.cost_calculation_service import CostCalculationService


@pytest.fixture
def cost_service():
    return CostCalculationService()


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestCostCalculationService:
    
    @pytest.mark.asyncio
    async def test_calculate_cost_with_database_pricing(self, cost_service, mock_db):
        """Test cost calculation using pricing from database."""
        provider_id = uuid4()
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            pricing_info={"gpt-4": {"input": 0.03, "output": 0.06}},
            name="openai"
        )
        mock_db.execute.return_value = mock_result
        
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
        
        # Mock database response with no pricing info
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            pricing_info=None,
            name="openai"
        )
        mock_db.execute.return_value = mock_result
        
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
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            pricing_info={"gpt-4": {"input": 0.03, "output": 0.06}},
            name="openai"
        )
        mock_db.execute.return_value = mock_result
        
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
        
        # Mock database response with no pricing info, fallback to default
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            pricing_info=None,
            name="anthropic"
        )
        mock_db.execute.return_value = mock_result
        
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
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock(
            pricing_info={"gpt-4": {"input": 0.03, "output": 0.06}},
            name="openai"
        )
        mock_db.execute.return_value = mock_result
        
        cost = await cost_service.calculate_cost(
            db=mock_db,
            provider_id=provider_id,
            model_name="gpt-4",
            input_tokens=0,
            output_tokens=0
        )
        
        assert cost == Decimal('0')
    
    def test_get_model_pricing_info(self, cost_service):
        """Test getting pricing info for a specific model."""
        pricing = cost_service.get_model_pricing_info("openai", "gpt-4")
        
        assert pricing is not None
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] == 0.03
        assert pricing["output"] == 0.06
    
    def test_get_model_pricing_info_unknown_provider(self, cost_service):
        """Test getting pricing info for unknown provider."""
        pricing = cost_service.get_model_pricing_info("unknown", "gpt-4")
        assert pricing is None
    
    def test_get_model_pricing_info_unknown_model(self, cost_service):
        """Test getting pricing info for unknown model."""
        pricing = cost_service.get_model_pricing_info("openai", "unknown-model")
        assert pricing is None
    
    def test_estimate_tokens(self, cost_service):
        """Test token estimation from text."""
        text = "This is a test message"
        tokens = cost_service.estimate_tokens(text)
        
        # Should be approximately len(text) / 4
        expected_tokens = len(text) // 4
        assert tokens == max(1, expected_tokens)
    
    def test_estimate_tokens_empty_string(self, cost_service):
        """Test token estimation for empty string."""
        tokens = cost_service.estimate_tokens("")
        assert tokens == 1  # Minimum 1 token
