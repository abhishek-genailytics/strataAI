import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.chat_completion import (
    ChatCompletionRequest, 
    ChatMessage, 
    ProviderError
)
from app.services.provider_service import provider_service


class TestProviderService:
    """Test cases for the provider service."""
    
    @pytest.fixture
    def sample_request(self):
        """Sample chat completion request."""
        return ChatCompletionRequest(
            messages=[
                ChatMessage(role="user", content="Hello, how are you?")
            ],
            model="gpt-3.5-turbo",
            project_id=uuid4(),
            temperature=0.7
        )
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_id(self):
        """Mock user ID."""
        return uuid4()
    
    def test_get_provider_from_model(self):
        """Test provider detection from model name."""
        # OpenAI models
        assert provider_service._get_provider_from_model("gpt-4") == "openai"
        assert provider_service._get_provider_from_model("gpt-3.5-turbo") == "openai"
        
        # Anthropic models
        assert provider_service._get_provider_from_model("claude-3-opus-20240229") == "anthropic"
        assert provider_service._get_provider_from_model("claude-3-sonnet-20240229") == "anthropic"
        
        # Unknown model
        assert provider_service._get_provider_from_model("unknown-model") is None
    
    def test_convert_messages_to_langchain(self):
        """Test message conversion to LangChain format."""
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant"),
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!")
        ]
        
        langchain_messages = provider_service._convert_messages_to_langchain(messages)
        
        assert len(langchain_messages) == 3
        assert langchain_messages[0].content == "You are a helpful assistant"
        assert langchain_messages[1].content == "Hello"
        assert langchain_messages[2].content == "Hi there!"
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        # Short text
        assert provider_service._estimate_tokens("Hello") == 2  # 5 chars / 4 = 1.25 -> 2
        
        # Longer text
        assert provider_service._estimate_tokens("This is a longer text") == 6  # 21 chars / 4 = 5.25 -> 6
        
        # Empty text
        assert provider_service._estimate_tokens("") == 1  # Minimum 1 token
    
    def test_get_supported_models(self):
        """Test getting supported models."""
        models = provider_service.get_supported_models()
        
        assert len(models) > 0
        
        # Check OpenAI models are included
        openai_models = [m for m in models if m.provider == "openai"]
        assert len(openai_models) > 0
        
        # Check Anthropic models are included
        anthropic_models = [m for m in models if m.provider == "anthropic"]
        assert len(anthropic_models) > 0
        
        # Verify model structure
        for model in models:
            assert model.provider in ["openai", "anthropic"]
            assert model.model
            assert model.display_name
            assert model.max_tokens > 0
            assert model.cost_per_1k_input_tokens >= 0
            assert model.cost_per_1k_output_tokens >= 0
    
    def test_get_provider_models(self):
        """Test getting models for specific provider."""
        # OpenAI models
        openai_models = provider_service.get_provider_models("openai")
        assert "gpt-4" in openai_models
        assert "gpt-3.5-turbo" in openai_models
        
        # Anthropic models
        anthropic_models = provider_service.get_provider_models("anthropic")
        assert "claude-3-opus-20240229" in anthropic_models
        assert "claude-3-sonnet-20240229" in anthropic_models
        
        # Unknown provider
        unknown_models = provider_service.get_provider_models("unknown")
        assert unknown_models == []
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test retry logic with successful execution."""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "success"
        
        result = await provider_service._retry_with_backoff(mock_func, max_retries=3)
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure(self):
        """Test retry logic with persistent failure."""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")
        
        with pytest.raises(Exception, match="Persistent error"):
            await provider_service._retry_with_backoff(mock_func, max_retries=2)
        
        assert call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.provider_service.api_key_service')
    async def test_get_provider_client_openai(self, mock_api_key_service, mock_db, mock_user_id):
        """Test getting OpenAI provider client."""
        # Mock provider lookup
        mock_provider = MagicMock()
        mock_provider.id = uuid4()
        mock_provider.name = "openai"
        
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_provider
        
        # Mock API key lookup
        mock_api_key = MagicMock()
        mock_api_key.id = uuid4()
        mock_api_key_service.get_by_project_and_provider.return_value = [mock_api_key]
        mock_api_key_service.get_decrypted_key.return_value = "test-api-key"
        
        with patch('app.services.provider_service.ChatOpenAI') as mock_chat_openai:
            mock_client = MagicMock()
            mock_chat_openai.return_value = mock_client
            
            client = await provider_service._get_provider_client(
                db=mock_db,
                provider="openai",
                model="gpt-3.5-turbo",
                user_id=mock_user_id,
                project_id=uuid4(),
                temperature=0.7
            )
            
            assert client == mock_client
            mock_chat_openai.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.provider_service.api_key_service')
    async def test_get_provider_client_no_api_key(self, mock_api_key_service, mock_db, mock_user_id):
        """Test getting provider client with no API key."""
        # Mock provider lookup
        mock_provider = MagicMock()
        mock_provider.id = uuid4()
        mock_provider.name = "openai"
        
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_provider
        
        # Mock no API keys found
        mock_api_key_service.get_by_project_and_provider.return_value = []
        
        with pytest.raises(ValueError, match="No API key found"):
            await provider_service._get_provider_client(
                db=mock_db,
                provider="openai",
                model="gpt-3.5-turbo",
                user_id=mock_user_id,
                project_id=uuid4()
            )
    
    @pytest.mark.asyncio
    @patch('app.services.provider_service.provider_service._get_provider_client')
    async def test_chat_completion_success(self, mock_get_client, mock_db, mock_user_id, sample_request):
        """Test successful chat completion."""
        # Mock LangChain response
        mock_response = MagicMock()
        mock_response.content = "Hello! I'm doing well, thank you for asking."
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.ainvoke.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        response = await provider_service.chat_completion(
            db=mock_db,
            request=sample_request,
            user_id=mock_user_id
        )
        
        assert response.model == "gpt-3.5-turbo"
        assert response.provider == "openai"
        assert len(response.choices) == 1
        assert response.choices[0].message.role == "assistant"
        assert response.choices[0].message.content == "Hello! I'm doing well, thank you for asking."
        assert response.usage.total_tokens > 0
    
    @pytest.mark.asyncio
    @patch('app.services.provider_service.provider_service._get_provider_client')
    async def test_chat_completion_provider_error(self, mock_get_client, mock_db, mock_user_id, sample_request):
        """Test chat completion with provider error."""
        # Mock client that raises an exception
        mock_client = AsyncMock()
        mock_client.ainvoke.side_effect = Exception("API rate limit exceeded")
        mock_get_client.return_value = mock_client
        
        with pytest.raises(ProviderError) as exc_info:
            await provider_service.chat_completion(
                db=mock_db,
                request=sample_request,
                user_id=mock_user_id
            )
        
        error = exc_info.value
        assert error.provider == "openai"
        assert "API rate limit exceeded" in error.error_message
    
    @pytest.mark.asyncio
    async def test_chat_completion_unknown_model(self, mock_db, mock_user_id):
        """Test chat completion with unknown model."""
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="unknown-model",
            project_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="Unknown model"):
            await provider_service.chat_completion(
                db=mock_db,
                request=request,
                user_id=mock_user_id
            )
    
    @pytest.mark.asyncio
    @patch('app.services.provider_service.provider_service.chat_completion')
    async def test_chat_completion_stream(self, mock_chat_completion, mock_db, mock_user_id, sample_request):
        """Test streaming chat completion."""
        # Mock regular completion response
        mock_response = MagicMock()
        mock_response.id = "test-id"
        mock_response.created = 1234567890
        mock_response.model = "gpt-3.5-turbo"
        mock_response.provider = "openai"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there friend"
        
        mock_chat_completion.return_value = mock_response
        
        chunks = []
        async for chunk in provider_service.chat_completion_stream(
            db=mock_db,
            request=sample_request,
            user_id=mock_user_id
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 1  # Should have multiple chunks plus [DONE]
        assert chunks[-1] == "data: [DONE]\n\n"  # Last chunk should be [DONE]
