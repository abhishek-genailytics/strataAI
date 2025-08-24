import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app.models.chat_completion import ChatCompletionRequest, ChatMessage


class TestChatAPI:
    """Test cases for the chat completion API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.mock_user_id = uuid4()
        self.mock_project_id = uuid4()
    
    @patch('app.api.chat.get_current_user')
    @patch('app.api.chat.provider_service.chat_completion')
    async def test_create_chat_completion_success(self, mock_chat_completion, mock_get_user):
        """Test successful chat completion."""
        # Mock user
        mock_user = AsyncMock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        mock_chat_completion.return_value = mock_response
        
        # Test request
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "gpt-3.5-turbo",
            "project_id": str(self.mock_project_id)
        }
        
        response = self.client.post(
            "/api/v1/chat/completions",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-3.5-turbo"
        assert data["provider"] == "openai"
    
    @patch('app.api.chat.get_current_user')
    async def test_list_models(self, mock_get_user):
        """Test listing available models."""
        # Mock user
        mock_user = AsyncMock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        response = self.client.get(
            "/api/v1/models",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Check that we have both OpenAI and Anthropic models
        providers = {model["provider"] for model in data}
        assert "openai" in providers
        assert "anthropic" in providers
    
    @patch('app.api.chat.get_current_user')
    async def test_list_provider_models(self, mock_get_user):
        """Test listing models for specific provider."""
        # Mock user
        mock_user = AsyncMock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        response = self.client.get(
            "/api/v1/models/openai",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "gpt-3.5-turbo" in data
        assert "gpt-4" in data
    
    @patch('app.api.chat.get_current_user')
    async def test_list_provider_models_not_found(self, mock_get_user):
        """Test listing models for unknown provider."""
        # Mock user
        mock_user = AsyncMock()
        mock_user.id = self.mock_user_id
        mock_get_user.return_value = mock_user
        
        response = self.client.get(
            "/api/v1/models/unknown",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    async def test_chat_completion_unauthorized(self):
        """Test chat completion without authentication."""
        request_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "gpt-3.5-turbo",
            "project_id": str(self.mock_project_id)
        }
        
        response = self.client.post("/api/v1/chat/completions", json=request_data)
        assert response.status_code == 403  # No authorization header
