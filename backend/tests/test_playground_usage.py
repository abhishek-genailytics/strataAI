import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from app.services.playground_usage_svc import PlaygroundUsageService
from app.models.playground_usage import SessionTotals, SessionBreakdownItem, SessionUsageResponse


class TestPlaygroundUsageService:
    """Test suite for playground usage service functionality."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing."""
        mock_client = Mock()
        return mock_client
    
    @pytest.fixture
    def usage_service(self, mock_supabase_client):
        """Create usage service with mocked client."""
        return PlaygroundUsageService(mock_supabase_client)
    
    @pytest.mark.asyncio
    async def test_get_session_totals_empty_data(self, usage_service, mock_supabase_client):
        """Test session totals with no data returns zero values."""
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test
        result = await usage_service._get_session_totals("test-session", None, None)
        
        # Verify
        assert isinstance(result, SessionTotals)
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0
        assert result.total_tokens == 0
        assert result.cost == Decimal("0")
        assert result.currency == "USD"
        assert result.request_count == 0
    
    @pytest.mark.asyncio
    async def test_get_session_totals_with_data(self, usage_service, mock_supabase_client):
        """Test session totals calculation with sample data."""
        # Mock response with sample data
        mock_response = Mock()
        mock_response.data = [
            {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "cost": 0.01,
                "currency": "USD"
            },
            {
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300,
                "cost": 0.02,
                "currency": "USD"
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = mock_response
        
        # Test
        result = await usage_service._get_session_totals("test-session", None, None)
        
        # Verify aggregation
        assert result.prompt_tokens == 300
        assert result.completion_tokens == 150
        assert result.total_tokens == 450
        assert result.cost == Decimal("0.03")
        assert result.currency == "USD"
        assert result.request_count == 2
    
    def test_time_window_calculations(self, usage_service):
        """Test time window boundary calculations."""
        # Test 'all' window
        from_time, to_time = usage_service._get_time_window("all", "test-session")
        assert from_time is None
        assert to_time is None
        
        # Test '24h' window
        from_time, to_time = usage_service._get_time_window("24h", "test-session")
        assert from_time is not None
        assert to_time is not None
        assert (to_time - from_time).total_seconds() == 24 * 3600
        
        # Test '7d' window
        from_time, to_time = usage_service._get_time_window("7d", "test-session")
        assert from_time is not None
        assert to_time is not None
        assert (to_time - from_time).days == 7
        
        # Test '30d' window
        from_time, to_time = usage_service._get_time_window("30d", "test-session")
        assert from_time is not None
        assert to_time is not None
        assert (to_time - from_time).days == 30
    
    @pytest.mark.asyncio
    async def test_usage_series_bucketing(self, usage_service, mock_supabase_client):
        """Test time series data bucketing."""
        # Mock response with time series data
        mock_response = Mock()
        mock_response.data = [
            {
                "created_at": "2025-09-07T10:15:30Z",
                "total_tokens": 100,
                "cost": 0.01
            },
            {
                "created_at": "2025-09-07T10:45:30Z",
                "total_tokens": 150,
                "cost": 0.015
            },
            {
                "created_at": "2025-09-07T11:15:30Z",
                "total_tokens": 200,
                "cost": 0.02
            }
        ]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = mock_response
        
        # Test hourly bucketing
        since = datetime(2025, 9, 7, 10, 0, 0)
        until = datetime(2025, 9, 7, 12, 0, 0)
        
        result = await usage_service._get_usage_series("test-session", "hour", since, until)
        
        # Should have 2 buckets: 10:00 and 11:00
        assert len(result) == 2
        
        # First bucket (10:00) should have 2 requests
        first_bucket = next(r for r in result if r.period_start.hour == 10)
        assert first_bucket.request_count == 2
        assert first_bucket.total_tokens == 250
        assert first_bucket.cost == Decimal("0.025")
        
        # Second bucket (11:00) should have 1 request
        second_bucket = next(r for r in result if r.period_start.hour == 11)
        assert second_bucket.request_count == 1
        assert second_bucket.total_tokens == 200
        assert second_bucket.cost == Decimal("0.02")


if __name__ == "__main__":
    pytest.main([__file__])
