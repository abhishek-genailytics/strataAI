import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.usage_tracking_service import UsageTrackingService
from app.models import UsageMetrics, UsageMetricsCreate


@pytest.fixture
def tracking_service():
    return UsageTrackingService()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_usage_metrics():
    return UsageMetrics(
        id=uuid4(),
        user_id=uuid4(),
        project_id=uuid4(),
        provider_id=uuid4(),
        date=date.today(),
        total_requests=10,
        successful_requests=8,
        failed_requests=2,
        total_tokens=5000,
        total_cost_usd=Decimal('0.50'),
        avg_latency_ms=Decimal('150'),
        created_at=date.today(),
        updated_at=date.today()
    )


class TestUsageTrackingService:
    
    @pytest.mark.asyncio
    async def test_update_usage_metrics_new_entry(self, tracking_service, mock_db):
        """Test creating new usage metrics entry."""
        user_id = uuid4()
        project_id = uuid4()
        provider_id = uuid4()
        
        # Mock no existing metrics
        with patch('app.services.usage_tracking_service.usage_metrics_service') as mock_service:
            mock_service.get_by_date.return_value = None
            mock_service.create.return_value = MagicMock(id=uuid4())
            
            result = await tracking_service.update_usage_metrics(
                db=mock_db,
                user_id=user_id,
                project_id=project_id,
                provider_id=provider_id,
                input_tokens=1000,
                output_tokens=500,
                cost_usd=Decimal('0.05'),
                latency_ms=200,
                is_successful=True
            )
            
            # Verify create was called with correct data
            mock_service.create.assert_called_once()
            create_call = mock_service.create.call_args[1]['obj_in']
            assert create_call.user_id == user_id
            assert create_call.total_requests == 1
            assert create_call.successful_requests == 1
            assert create_call.failed_requests == 0
            assert create_call.total_tokens == 1500
            assert create_call.total_cost_usd == Decimal('0.05')
    
    @pytest.mark.asyncio
    async def test_update_usage_metrics_existing_entry(self, tracking_service, mock_db, sample_usage_metrics):
        """Test updating existing usage metrics entry."""
        user_id = sample_usage_metrics.user_id
        project_id = sample_usage_metrics.project_id
        provider_id = sample_usage_metrics.provider_id
        
        with patch('app.services.usage_tracking_service.usage_metrics_service') as mock_service:
            mock_service.get_by_date.return_value = sample_usage_metrics
            mock_service.update.return_value = MagicMock()
            
            await tracking_service.update_usage_metrics(
                db=mock_db,
                user_id=user_id,
                project_id=project_id,
                provider_id=provider_id,
                input_tokens=1000,
                output_tokens=500,
                cost_usd=Decimal('0.05'),
                latency_ms=100,
                is_successful=True
            )
            
            # Verify update was called
            mock_service.update.assert_called_once()
            update_call = mock_service.update.call_args[1]['obj_in']
            assert update_call.total_requests == 11  # 10 + 1
            assert update_call.successful_requests == 9  # 8 + 1
            assert update_call.failed_requests == 2  # unchanged
            assert update_call.total_tokens == 6500  # 5000 + 1500
            assert update_call.total_cost_usd == Decimal('0.55')  # 0.50 + 0.05
    
    @pytest.mark.asyncio
    async def test_update_usage_metrics_failed_request(self, tracking_service, mock_db, sample_usage_metrics):
        """Test updating metrics for failed request."""
        user_id = sample_usage_metrics.user_id
        project_id = sample_usage_metrics.project_id
        provider_id = sample_usage_metrics.provider_id
        
        with patch('app.services.usage_tracking_service.usage_metrics_service') as mock_service:
            mock_service.get_by_date.return_value = sample_usage_metrics
            mock_service.update.return_value = MagicMock()
            
            await tracking_service.update_usage_metrics(
                db=mock_db,
                user_id=user_id,
                project_id=project_id,
                provider_id=provider_id,
                input_tokens=1000,
                output_tokens=0,  # No output tokens for failed request
                cost_usd=Decimal('0'),
                latency_ms=500,
                is_successful=False
            )
            
            # Verify update was called with correct failed request counts
            update_call = mock_service.update.call_args[1]['obj_in']
            assert update_call.total_requests == 11  # 10 + 1
            assert update_call.successful_requests == 8  # unchanged
            assert update_call.failed_requests == 3  # 2 + 1
    
    @pytest.mark.asyncio
    async def test_get_current_usage_summary(self, tracking_service, mock_db):
        """Test getting current usage summary."""
        user_id = uuid4()
        
        with patch('app.services.usage_tracking_service.usage_metrics_service') as mock_service:
            mock_service.get_aggregated_metrics.return_value = {
                'total_requests': 100,
                'successful_requests': 95,
                'failed_requests': 5,
                'total_tokens': 50000,
                'total_cost_usd': 5.0,
                'avg_latency_ms': 150.0
            }
            
            summary = await tracking_service.get_current_usage_summary(
                db=mock_db,
                user_id=user_id
            )
            
            assert summary['date'] == date.today().isoformat()
            assert summary['total_requests'] == 100
            assert summary['total_cost_usd'] == 5.0
    
    @pytest.mark.asyncio
    async def test_get_usage_trends(self, tracking_service, mock_db):
        """Test getting usage trends."""
        user_id = uuid4()
        
        # Mock metrics for the last 7 days
        mock_metrics = []
        for i in range(7):
            metrics_date = date.today() - timedelta(days=i)
            mock_metrics.append(MagicMock(
                date=metrics_date,
                total_requests=10 + i,
                successful_requests=9 + i,
                failed_requests=1,
                total_tokens=1000 * (i + 1),
                total_cost_usd=Decimal(str(0.1 * (i + 1))),
                avg_latency_ms=Decimal('150')
            ))
        
        with patch('app.services.usage_tracking_service.usage_metrics_service') as mock_service:
            mock_service.get_date_range.return_value = mock_metrics
            
            trends = await tracking_service.get_usage_trends(
                db=mock_db,
                user_id=user_id,
                days=7
            )
            
            assert len(trends) == 7
            assert all('date' in trend for trend in trends)
            assert all('total_requests' in trend for trend in trends)
            assert all('total_cost_usd' in trend for trend in trends)


# Import patch for mocking
from unittest.mock import patch
