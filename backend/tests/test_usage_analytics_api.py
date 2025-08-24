import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app.models import UserProfile, UsageMetrics, APIRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return UserProfile(
        id=uuid4(),
        organization_name="Test Org",
        subscription_tier="pro",
        created_at=date.today(),
        updated_at=date.today()
    )


@pytest.fixture
def sample_usage_metrics():
    return [
        UsageMetrics(
            id=uuid4(),
            user_id=uuid4(),
            project_id=uuid4(),
            provider_id=uuid4(),
            date=date.today(),
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            total_tokens=10000,
            total_cost_usd=Decimal('1.50'),
            avg_latency_ms=Decimal('150'),
            created_at=date.today(),
            updated_at=date.today()
        )
    ]


@pytest.fixture
def sample_api_requests():
    return [
        APIRequest(
            id=uuid4(),
            user_id=uuid4(),
            project_id=uuid4(),
            api_key_id=uuid4(),
            provider_id=uuid4(),
            model_name="gpt-4",
            request_payload={"model": "gpt-4", "messages": []},
            response_payload={"choices": []},
            status_code=200,
            error_message=None,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=Decimal('0.015'),
            latency_ms=200,
            created_at=date.today()
        )
    ]


class TestUsageAnalyticsAPI:
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_metrics_service')
    def test_get_usage_metrics(self, mock_service, mock_get_user, client, mock_user, sample_usage_metrics):
        """Test getting usage metrics endpoint."""
        mock_get_user.return_value = mock_user
        mock_service.get_date_range.return_value = sample_usage_metrics
        
        response = client.get("/api/v1/analytics/usage-metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_requests"] == 100
        assert data[0]["total_cost_usd"] == "1.50"
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_metrics_service')
    def test_get_usage_metrics_with_filters(self, mock_service, mock_get_user, client, mock_user, sample_usage_metrics):
        """Test getting usage metrics with date and ID filters."""
        mock_get_user.return_value = mock_user
        mock_service.get_date_range.return_value = sample_usage_metrics
        
        project_id = uuid4()
        provider_id = uuid4()
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        response = client.get(
            f"/api/v1/analytics/usage-metrics"
            f"?start_date={start_date}&end_date={end_date}"
            f"&project_id={project_id}&provider_id={provider_id}"
        )
        
        assert response.status_code == 200
        mock_service.get_date_range.assert_called_once()
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_metrics_service')
    def test_get_usage_summary(self, mock_service, mock_get_user, client, mock_user):
        """Test getting usage summary endpoint."""
        mock_get_user.return_value = mock_user
        mock_service.get_aggregated_metrics.return_value = {
            'total_requests': 500,
            'successful_requests': 475,
            'failed_requests': 25,
            'total_tokens': 50000,
            'total_cost_usd': 7.5,
            'avg_latency_ms': 180.0
        }
        
        response = client.get("/api/v1/analytics/usage-summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 500
        assert data["total_cost_usd"] == 7.5
        assert "start_date" in data
        assert "end_date" in data
        assert "days_count" in data
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_tracking_service')
    def test_get_usage_trends(self, mock_service, mock_get_user, client, mock_user):
        """Test getting usage trends endpoint."""
        mock_get_user.return_value = mock_user
        mock_trends = [
            {
                "date": "2024-01-01",
                "total_requests": 100,
                "total_cost_usd": 1.5,
                "total_tokens": 10000
            }
        ]
        mock_service.get_usage_trends.return_value = mock_trends
        
        response = client.get("/api/v1/analytics/usage-trends?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert data["days"] == 7
        assert len(data["trends"]) == 1
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_tracking_service')
    def test_get_current_usage(self, mock_service, mock_get_user, client, mock_user):
        """Test getting current usage endpoint."""
        mock_get_user.return_value = mock_user
        mock_service.get_current_usage_summary.return_value = {
            "date": date.today().isoformat(),
            "total_requests": 50,
            "total_cost_usd": 0.75
        }
        
        response = client.get("/api/v1/analytics/current-usage")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 50
        assert data["total_cost_usd"] == 0.75
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.api_request_service')
    def test_get_api_requests(self, mock_service, mock_get_user, client, mock_user, sample_api_requests):
        """Test getting API requests endpoint."""
        mock_get_user.return_value = mock_user
        mock_service.get_recent_requests.return_value = sample_api_requests
        
        response = client.get("/api/v1/analytics/api-requests")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["model_name"] == "gpt-4"
        assert data[0]["status_code"] == 200
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.api_request_service')
    def test_get_failed_requests(self, mock_service, mock_get_user, client, mock_user):
        """Test getting failed requests endpoint."""
        mock_get_user.return_value = mock_user
        failed_request = APIRequest(
            id=uuid4(),
            user_id=mock_user.id,
            project_id=uuid4(),
            api_key_id=uuid4(),
            provider_id=uuid4(),
            model_name="gpt-4",
            request_payload={"model": "gpt-4"},
            response_payload={"error": {"message": "Rate limit exceeded"}},
            status_code=429,
            error_message="Rate limit exceeded",
            input_tokens=100,
            output_tokens=0,
            total_tokens=100,
            cost_usd=Decimal('0'),
            latency_ms=100,
            created_at=date.today()
        )
        mock_service.get_failed_requests.return_value = [failed_request]
        
        response = client.get("/api/v1/analytics/failed-requests?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status_code"] == 429
        assert data[0]["error_message"] == "Rate limit exceeded"
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_metrics_service')
    def test_get_cost_analysis_by_day(self, mock_service, mock_get_user, client, mock_user, sample_usage_metrics):
        """Test cost analysis grouped by day."""
        mock_get_user.return_value = mock_user
        mock_service.get_date_range.return_value = sample_usage_metrics
        
        response = client.get("/api/v1/analytics/cost-analysis?group_by=day")
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "day"
        assert "data" in data
        assert len(data["data"]) >= 1
    
    @patch('app.api.usage_analytics.get_current_user')
    @patch('app.api.usage_analytics.usage_metrics_service')
    def test_get_cost_analysis_by_provider(self, mock_service, mock_get_user, client, mock_user, sample_usage_metrics):
        """Test cost analysis grouped by provider."""
        mock_get_user.return_value = mock_user
        mock_service.get_date_range.return_value = sample_usage_metrics
        
        response = client.get("/api/v1/analytics/cost-analysis?group_by=provider")
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "provider"
        assert "data" in data
    
    def test_get_usage_metrics_invalid_date_range(self, client):
        """Test usage metrics with invalid date range."""
        with patch('app.api.usage_analytics.get_current_user') as mock_get_user:
            mock_get_user.return_value = MagicMock(id=uuid4())
            
            response = client.get(
                "/api/v1/analytics/usage-metrics"
                "?start_date=2024-01-31&end_date=2024-01-01"
            )
            
            assert response.status_code == 400
            assert "Start date must be before end date" in response.json()["detail"]
    
    def test_get_usage_trends_invalid_days(self, client):
        """Test usage trends with invalid days parameter."""
        with patch('app.api.usage_analytics.get_current_user') as mock_get_user:
            mock_get_user.return_value = MagicMock(id=uuid4())
            
            response = client.get("/api/v1/analytics/usage-trends?days=500")
            
            assert response.status_code == 422  # Validation error
