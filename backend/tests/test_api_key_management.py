"""
Unit tests for API key management system.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.core.encryption import EncryptionService
from app.models.api_key import APIKeyCreate, APIKeyValidationResult
from app.services.api_key_service import APIKeyService
from app.services.api_key_validator import APIKeyValidator


class TestEncryptionService:
    """Test encryption utilities."""
    
    def setup_method(self):
        self.encryption_service = EncryptionService()
    
    def test_encrypt_decrypt_api_key(self):
        """Test API key encryption and decryption."""
        original_key = "sk-test1234567890abcdef"
        
        # Encrypt the key
        encrypted_key = self.encryption_service.encrypt_api_key(original_key)
        assert encrypted_key != original_key
        assert len(encrypted_key) > 0
        
        # Decrypt the key
        decrypted_key = self.encryption_service.decrypt_api_key(encrypted_key)
        assert decrypted_key == original_key
    
    def test_encrypt_empty_key_raises_error(self):
        """Test that encrypting empty key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            self.encryption_service.encrypt_api_key("")
    
    def test_decrypt_empty_key_raises_error(self):
        """Test that decrypting empty key raises ValueError."""
        with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
            self.encryption_service.decrypt_api_key("")
    
    def test_decrypt_invalid_key_raises_error(self):
        """Test that decrypting invalid key raises ValueError."""
        with pytest.raises(ValueError, match="Failed to decrypt API key"):
            self.encryption_service.decrypt_api_key("invalid-encrypted-key")
    
    def test_mask_api_key(self):
        """Test API key masking functionality."""
        api_key = "sk-test1234567890abcdef"
        
        # Default masking (4 visible chars)
        masked = self.encryption_service.mask_api_key(api_key)
        assert masked == "sk-t" + "*" * (len(api_key) - 4)
        
        # Custom visible chars
        masked_custom = self.encryption_service.mask_api_key(api_key, visible_chars=6)
        assert masked_custom == "sk-tes" + "*" * (len(api_key) - 6)
        
        # Short key
        short_key = "abc"
        masked_short = self.encryption_service.mask_api_key(short_key)
        assert masked_short == "***"
        
        # Empty key
        assert self.encryption_service.mask_api_key("") == ""
    
    def test_get_key_prefix(self):
        """Test key prefix extraction."""
        api_key = "sk-test1234567890abcdef"
        
        # Default prefix length (7)
        prefix = self.encryption_service.get_key_prefix(api_key)
        assert prefix == "sk-test"
        
        # Custom prefix length
        prefix_custom = self.encryption_service.get_key_prefix(api_key, prefix_length=10)
        assert prefix_custom == "sk-test123"
        
        # Short key
        short_key = "abc"
        prefix_short = self.encryption_service.get_key_prefix(short_key)
        assert prefix_short == "abc"
        
        # Empty key
        assert self.encryption_service.get_key_prefix("") == ""


class TestAPIKeyValidator:
    """Test API key validation service."""
    
    def setup_method(self):
        self.validator = APIKeyValidator()
    
    def test_validate_openai_key_format(self):
        """Test OpenAI key format validation."""
        valid_key = "sk-" + "a" * 48
        invalid_key = "invalid-key"
        
        assert self.validator._validate_key_format(valid_key, "openai") is True
        assert self.validator._validate_key_format(invalid_key, "openai") is False
    
    def test_validate_anthropic_key_format(self):
        """Test Anthropic key format validation."""
        valid_key = "sk-ant-api03-" + "a" * 95
        invalid_key = "sk-invalid-key"
        
        assert self.validator._validate_key_format(valid_key, "anthropic") is True
        assert self.validator._validate_key_format(invalid_key, "anthropic") is False
    
    def test_validate_google_key_format(self):
        """Test Google key format validation."""
        valid_key = "AIza" + "a" * 35
        invalid_key = "invalid-key"
        
        assert self.validator._validate_key_format(valid_key, "google") is True
        assert self.validator._validate_key_format(invalid_key, "google") is False
    
    def test_validate_unknown_provider_format(self):
        """Test validation for unknown provider (should return True)."""
        assert self.validator._validate_key_format("any-key", "unknown") is True
    
    @pytest.mark.asyncio
    async def test_validate_api_key_invalid_format(self):
        """Test validation with invalid format."""
        result = await self.validator.validate_api_key("invalid-key", "openai")
        
        assert result.is_valid is False
        assert result.provider_name == "openai"
        assert "Invalid API key format" in result.error_message
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_validate_openai_key_success(self, mock_get):
        """Test successful OpenAI key validation."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "model1"}, {"id": "model2"}]}
        mock_get.return_value = mock_response
        
        valid_key = "sk-" + "a" * 48
        result = await self.validator.validate_api_key(valid_key, "openai")
        
        assert result.is_valid is True
        assert result.provider_name == "openai"
        assert result.error_message is None
        assert result.key_info["models_count"] == 2
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_validate_openai_key_invalid(self, mock_get):
        """Test invalid OpenAI key validation."""
        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        valid_key = "sk-" + "a" * 48
        result = await self.validator.validate_api_key(valid_key, "openai")
        
        assert result.is_valid is False
        assert result.provider_name == "openai"
        assert result.error_message == "Invalid API key"


class TestAPIKeyService:
    """Test API key service operations."""
    
    def setup_method(self):
        self.service = APIKeyService()
    
    @pytest.mark.asyncio
    async def test_create_with_encryption(self):
        """Test API key creation with encryption."""
        # Mock database session
        mock_db = AsyncMock()
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Create test data
        user_id = uuid4()
        project_id = uuid4()
        provider_id = uuid4()
        
        api_key_create = APIKeyCreate(
            name="Test API Key",
            project_id=project_id,
            provider_id=provider_id,
            api_key_value="sk-test1234567890abcdef"
        )
        
        # Mock the model creation
        with patch.object(self.service, 'model') as mock_model:
            mock_instance = AsyncMock()
            mock_model.return_value = mock_instance
            
            result = await self.service.create_with_encryption(
                mock_db, obj_in=api_key_create, user_id=user_id
            )
            
            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_create_success(self):
        """Test successful API key validation and creation."""
        mock_db = AsyncMock()
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_provider.name = "openai"
        mock_db.get.return_value = mock_provider
        
        # Mock validation result
        mock_validation = APIKeyValidationResult(
            is_valid=True,
            provider_name="openai",
            key_info={"models_count": 5}
        )
        
        user_id = uuid4()
        project_id = uuid4()
        provider_id = uuid4()
        
        api_key_create = APIKeyCreate(
            name="Test API Key",
            project_id=project_id,
            provider_id=provider_id,
            api_key_value="sk-" + "a" * 48
        )
        
        with patch.object(self.service, 'create_with_encryption') as mock_create:
            with patch('app.services.api_key_service.api_key_validator.validate_api_key') as mock_validate:
                mock_api_key = AsyncMock()
                mock_create.return_value = mock_api_key
                mock_validate.return_value = mock_validation
                
                result_key, result_validation = await self.service.validate_and_create(
                    mock_db, obj_in=api_key_create, user_id=user_id
                )
                
                assert result_key == mock_api_key
                assert result_validation == mock_validation
                mock_validate.assert_called_once()
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_create_invalid_provider(self):
        """Test validation with invalid provider ID."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None  # Provider not found
        
        user_id = uuid4()
        project_id = uuid4()
        provider_id = uuid4()
        
        api_key_create = APIKeyCreate(
            name="Test API Key",
            project_id=project_id,
            provider_id=provider_id,
            api_key_value="sk-test1234567890abcdef"
        )
        
        with pytest.raises(ValueError, match="Invalid provider ID"):
            await self.service.validate_and_create(
                mock_db, obj_in=api_key_create, user_id=user_id
            )
    
    @pytest.mark.asyncio
    async def test_validate_and_create_validation_failure(self):
        """Test creation with validation failure."""
        mock_db = AsyncMock()
        
        # Mock provider
        mock_provider = AsyncMock()
        mock_provider.name = "openai"
        mock_db.get.return_value = mock_provider
        
        # Mock validation failure
        mock_validation = APIKeyValidationResult(
            is_valid=False,
            provider_name="openai",
            error_message="Invalid API key"
        )
        
        user_id = uuid4()
        project_id = uuid4()
        provider_id = uuid4()
        
        api_key_create = APIKeyCreate(
            name="Test API Key",
            project_id=project_id,
            provider_id=provider_id,
            api_key_value="invalid-key"
        )
        
        with patch('app.services.api_key_service.api_key_validator.validate_api_key') as mock_validate:
            mock_validate.return_value = mock_validation
            
            with pytest.raises(ValueError, match="API key validation failed"):
                await self.service.validate_and_create(
                    mock_db, obj_in=api_key_create, user_id=user_id
                )
    
    @pytest.mark.asyncio
    async def test_get_decrypted_key_success(self):
        """Test successful key decryption."""
        mock_db = AsyncMock()
        
        # Mock API key with encrypted value
        mock_api_key = AsyncMock()
        mock_api_key.is_active = True
        mock_api_key.encrypted_key_value = "encrypted-value"
        
        user_id = uuid4()
        api_key_id = uuid4()
        
        with patch.object(self.service, 'get_with_provider') as mock_get:
            with patch.object(self.service, 'update_last_used') as mock_update:
                with patch('app.services.api_key_service.encryption_service.decrypt_api_key') as mock_decrypt:
                    mock_get.return_value = mock_api_key
                    mock_decrypt.return_value = "sk-decrypted-key"
                    
                    result = await self.service.get_decrypted_key(
                        mock_db, api_key_id=api_key_id, user_id=user_id
                    )
                    
                    assert result == "sk-decrypted-key"
                    mock_update.assert_called_once_with(mock_db, api_key_id=api_key_id)
    
    @pytest.mark.asyncio
    async def test_get_decrypted_key_not_found(self):
        """Test key decryption when key not found."""
        mock_db = AsyncMock()
        
        user_id = uuid4()
        api_key_id = uuid4()
        
        with patch.object(self.service, 'get_with_provider') as mock_get:
            mock_get.return_value = None
            
            result = await self.service.get_decrypted_key(
                mock_db, api_key_id=api_key_id, user_id=user_id
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_decrypted_key_inactive(self):
        """Test key decryption when key is inactive."""
        mock_db = AsyncMock()
        
        # Mock inactive API key
        mock_api_key = AsyncMock()
        mock_api_key.is_active = False
        
        user_id = uuid4()
        api_key_id = uuid4()
        
        with patch.object(self.service, 'get_with_provider') as mock_get:
            mock_get.return_value = mock_api_key
            
            result = await self.service.get_decrypted_key(
                mock_db, api_key_id=api_key_id, user_id=user_id
            )
            
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
