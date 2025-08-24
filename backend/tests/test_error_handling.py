"""
Tests for comprehensive error handling system.
"""
import pytest
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.core.exceptions import (
    StrataAIException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
    ProviderException,
    NetworkException,
    TimeoutException,
    ConfigurationException,
)
from app.models.error_response import (
    ErrorType,
    ErrorSeverity,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
)
from app.services.error_logging_service import ErrorLoggingService


class TestStrataAIExceptions:
    """Test custom exception classes."""
    
    def test_base_exception(self):
        """Test base StrataAI exception."""
        exc = StrataAIException(
            message="Test error",
            error_type=ErrorType.INTERNAL_ERROR,
            error_code="TEST_ERROR",
            severity=ErrorSeverity.HIGH,
        )
        
        assert exc.message == "Test error"
        assert exc.error_type == ErrorType.INTERNAL_ERROR
        assert exc.error_code == "TEST_ERROR"
        assert exc.severity == ErrorSeverity.HIGH
        assert str(exc) == "Test error"
    
    def test_validation_exception(self):
        """Test validation exception."""
        details = [
            ErrorDetail(field="email", message="Invalid email format", code="INVALID_EMAIL")
        ]
        exc = ValidationException(message="Validation failed", details=details)
        
        assert exc.error_type == ErrorType.VALIDATION_ERROR
        assert exc.severity == ErrorSeverity.LOW
        assert len(exc.details) == 1
        assert exc.details[0].field == "email"
    
    def test_authentication_exception(self):
        """Test authentication exception."""
        exc = AuthenticationException()
        
        assert exc.error_type == ErrorType.AUTHENTICATION_ERROR
        assert exc.message == "Authentication required"
        assert exc.severity == ErrorSeverity.MEDIUM
    
    def test_authorization_exception(self):
        """Test authorization exception."""
        exc = AuthorizationException()
        
        assert exc.error_type == ErrorType.AUTHORIZATION_ERROR
        assert exc.message == "Insufficient permissions"
        assert exc.severity == ErrorSeverity.MEDIUM
    
    def test_not_found_exception(self):
        """Test not found exception."""
        exc = NotFoundException(resource_type="User", resource_id="123")
        
        assert exc.error_type == ErrorType.NOT_FOUND_ERROR
        assert "User with ID '123' not found" in exc.message
        assert exc.severity == ErrorSeverity.LOW
    
    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = RateLimitException(retry_after=120)
        
        assert exc.error_type == ErrorType.RATE_LIMIT_ERROR
        assert exc.retry_after == 120
        assert exc.severity == ErrorSeverity.MEDIUM
    
    def test_provider_exception(self):
        """Test provider exception."""
        exc = ProviderException(
            message="OpenAI API error",
            provider="openai",
            provider_error_code="rate_limit_exceeded",
            provider_message="Rate limit exceeded",
        )
        
        assert exc.error_type == ErrorType.PROVIDER_ERROR
        assert exc.provider == "openai"
        assert exc.provider_error_code == "rate_limit_exceeded"
        assert exc.severity == ErrorSeverity.HIGH
    
    def test_network_exception(self):
        """Test network exception."""
        exc = NetworkException()
        
        assert exc.error_type == ErrorType.NETWORK_ERROR
        assert exc.message == "Network error occurred"
        assert exc.severity == ErrorSeverity.MEDIUM
    
    def test_timeout_exception(self):
        """Test timeout exception."""
        exc = TimeoutException(timeout_seconds=30)
        
        assert exc.error_type == ErrorType.TIMEOUT_ERROR
        assert "30 seconds" in exc.message
        assert exc.severity == ErrorSeverity.MEDIUM
    
    def test_configuration_exception(self):
        """Test configuration exception."""
        exc = ConfigurationException(
            message="Missing API key",
            config_key="OPENAI_API_KEY"
        )
        
        assert exc.error_type == ErrorType.CONFIGURATION_ERROR
        assert "OPENAI_API_KEY" in exc.message
        assert exc.severity == ErrorSeverity.HIGH


class TestErrorLoggingService:
    """Test error logging service."""
    
    @pytest.fixture
    def error_service(self):
        return ErrorLoggingService()
    
    @pytest.fixture
    def mock_request(self):
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/test"
        request.url = Mock()
        request.url.__str__ = Mock(return_value="http://localhost/api/test")
        request.state.user_agent = "test-agent"
        request.state.client_ip = "127.0.0.1"
        request.state.user = Mock()
        request.state.user.id = "user123"
        return request
    
    @pytest.mark.asyncio
    async def test_log_error(self, error_service, mock_request):
        """Test logging application error."""
        error = StrataAIException(
            message="Test error",
            error_type=ErrorType.VALIDATION_ERROR,
            error_code="TEST_ERROR",
        )
        
        with patch.object(error_service, '_store_error_log', new_callable=AsyncMock) as mock_store:
            error_id = await error_service.log_error(
                error=error,
                request=mock_request,
                request_id="req123",
            )
            
            assert error_id.startswith("err_")
            mock_store.assert_called_once()
            
            # Check stored data structure
            call_args = mock_store.call_args[0][0]
            assert call_args["error_type"] == ErrorType.VALIDATION_ERROR
            assert call_args["message"] == "Test error"
            assert call_args["request_id"] == "req123"
            assert call_args["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_log_validation_error(self, error_service, mock_request):
        """Test logging validation error."""
        from pydantic import ValidationError, BaseModel
        from typing import List
        
        class TestModel(BaseModel):
            email: str
            age: int
        
        try:
            TestModel(email="invalid", age="not_a_number")
        except ValidationError as validation_error:
            with patch.object(error_service, '_store_error_log', new_callable=AsyncMock) as mock_store:
                error_id = await error_service.log_validation_error(
                    validation_error=validation_error,
                    request=mock_request,
                    request_id="req123",
                )
                
                assert error_id.startswith("err_")
                mock_store.assert_called_once()
                
                # Check stored data structure
                call_args = mock_store.call_args[0][0]
                assert call_args["error_type"] == ErrorType.VALIDATION_ERROR
                assert call_args["error_code"] == "VALIDATION_FAILED"
                assert len(call_args["details"]) > 0
    
    @pytest.mark.asyncio
    async def test_log_unexpected_error(self, error_service, mock_request):
        """Test logging unexpected error."""
        error = ValueError("Unexpected error")
        traceback_str = "Traceback (most recent call last):\n  ValueError: Unexpected error"
        
        with patch.object(error_service, '_store_error_log', new_callable=AsyncMock) as mock_store:
            with patch.object(error_service, '_send_error_alert', new_callable=AsyncMock) as mock_alert:
                error_id = await error_service.log_unexpected_error(
                    error=error,
                    request=mock_request,
                    request_id="req123",
                    traceback_str=traceback_str,
                )
                
                assert error_id.startswith("err_")
                mock_store.assert_called_once()
                mock_alert.assert_called_once()  # Should send alert for unexpected errors
                
                # Check stored data structure
                call_args = mock_store.call_args[0][0]
                assert call_args["error_type"] == ErrorType.INTERNAL_ERROR
                assert call_args["severity"] == ErrorSeverity.CRITICAL
                assert call_args["exception_type"] == "ValueError"
                assert call_args["traceback"] == traceback_str


class TestErrorHandlingMiddleware:
    """Test error handling middleware integration."""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_validation_error_response(self, client):
        """Test validation error response format."""
        # This would test an endpoint that triggers validation errors
        # For now, we'll test the response format structure
        pass
    
    def test_authentication_error_response(self, client):
        """Test authentication error response format."""
        # Test accessing protected endpoint without auth
        response = client.get("/api/protected-endpoint")
        
        # Should return 401 with structured error response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == ErrorType.AUTHENTICATION_ERROR
        assert "request_id" in data
    
    def test_not_found_error_response(self, client):
        """Test not found error response format."""
        response = client.get("/api/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == ErrorType.NOT_FOUND_ERROR
    
    def test_internal_error_response(self, client):
        """Test internal error response format."""
        # This would test an endpoint that triggers internal errors
        # The response should not expose internal details
        pass


class TestErrorResponseModels:
    """Test error response model validation."""
    
    def test_error_response_model(self):
        """Test basic error response model."""
        response = ErrorResponse(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Test error",
            error_code="TEST_ERROR",
        )
        
        assert response.error is True
        assert response.error_type == ErrorType.VALIDATION_ERROR
        assert response.message == "Test error"
        assert response.error_code == "TEST_ERROR"
        assert isinstance(response.timestamp, datetime)
        assert response.severity == ErrorSeverity.MEDIUM  # default
    
    def test_validation_error_response_model(self):
        """Test validation error response model."""
        details = [
            ErrorDetail(field="email", message="Invalid format", code="INVALID_EMAIL")
        ]
        response = ValidationErrorResponse(details=details)
        
        assert response.error_type == ErrorType.VALIDATION_ERROR
        assert len(response.details) == 1
        assert response.details[0].field == "email"
    
    def test_error_detail_model(self):
        """Test error detail model."""
        detail = ErrorDetail(
            field="password",
            message="Password too short",
            code="PASSWORD_TOO_SHORT",
            value="123",
        )
        
        assert detail.field == "password"
        assert detail.message == "Password too short"
        assert detail.code == "PASSWORD_TOO_SHORT"
        assert detail.value == "123"


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_end_to_end_error_flow(self, client):
        """Test complete error handling flow."""
        # This would test a complete flow from error occurrence to logging
        pass
    
    def test_error_monitoring_endpoints(self, client):
        """Test error monitoring and statistics endpoints."""
        # Test endpoints that provide error statistics
        pass
    
    def test_error_recovery_scenarios(self, client):
        """Test error recovery and retry scenarios."""
        # Test how the system handles and recovers from various error types
        pass
