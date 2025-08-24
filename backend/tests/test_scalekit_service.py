import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.scalekit_service import ScaleKitService, ScaleKitUserProfile, ScaleKitAuthResult
from app.core.config import settings


@pytest.fixture
def scalekit_service():
    """Create a ScaleKit service instance for testing."""
    return ScaleKitService()


@pytest.fixture
def mock_scalekit_client():
    """Mock ScaleKit client."""
    with patch('app.services.scalekit_service.ScaleKit') as mock_client:
        yield mock_client


class TestScaleKitService:
    """Test cases for ScaleKit service."""

    def test_initialization(self, mock_scalekit_client):
        """Test ScaleKit service initialization."""
        service = ScaleKitService()
        
        mock_scalekit_client.assert_called_once_with(
            environment_url=settings.SCALEKIT_ENVIRONMENT_URL,
            client_id=settings.SCALEKIT_CLIENT_ID,
            client_secret=settings.SCALEKIT_CLIENT_SECRET
        )
        assert service.client is not None

    def test_get_authorization_url_basic(self, scalekit_service, mock_scalekit_client):
        """Test basic authorization URL generation."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.get_authorization_url.return_value = "https://auth.example.com/oauth/authorize"
        
        redirect_uri = "https://app.example.com/callback"
        auth_url = scalekit_service.get_authorization_url(redirect_uri)
        
        assert auth_url == "https://auth.example.com/oauth/authorize"
        mock_client_instance.get_authorization_url.assert_called_once()

    def test_get_authorization_url_with_options(self, scalekit_service, mock_scalekit_client):
        """Test authorization URL generation with optional parameters."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.get_authorization_url.return_value = "https://auth.example.com/oauth/authorize"
        
        redirect_uri = "https://app.example.com/callback"
        state = "random_state_123"
        organization_id = "org_123"
        connection_id = "conn_456"
        login_hint = "user@example.com"
        
        auth_url = scalekit_service.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
            organization_id=organization_id,
            connection_id=connection_id,
            login_hint=login_hint
        )
        
        assert auth_url == "https://auth.example.com/oauth/authorize"
        mock_client_instance.get_authorization_url.assert_called_once()
        
        # Verify the call was made with correct parameters
        call_args = mock_client_instance.get_authorization_url.call_args
        assert call_args[1]['redirect_uri'] == redirect_uri

    def test_authenticate_with_code_success(self, scalekit_service, mock_scalekit_client):
        """Test successful authentication with authorization code."""
        mock_client_instance = mock_scalekit_client.return_value
        
        # Mock the authentication result
        mock_auth_result = Mock()
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.email = "user@example.com"
        mock_user.given_name = "John"
        mock_user.family_name = "Doe"
        mock_user.picture = "https://example.com/avatar.jpg"
        
        mock_auth_result.user = mock_user
        mock_auth_result.access_token = "access_token_123"
        mock_auth_result.refresh_token = "refresh_token_123"
        mock_auth_result.id_token = "id_token_123"
        mock_auth_result.expires_in = 3600
        mock_auth_result.token_type = "Bearer"
        
        mock_client_instance.authenticate_with_code.return_value = mock_auth_result
        
        code = "auth_code_123"
        redirect_uri = "https://app.example.com/callback"
        
        result = scalekit_service.authenticate_with_code(code, redirect_uri)
        
        assert isinstance(result, ScaleKitAuthResult)
        assert isinstance(result.user, ScaleKitUserProfile)
        assert result.user.id == "user_123"
        assert result.user.email == "user@example.com"
        assert result.user.given_name == "John"
        assert result.user.family_name == "Doe"
        assert result.access_token == "access_token_123"
        assert result.refresh_token == "refresh_token_123"
        assert result.id_token == "id_token_123"
        assert result.expires_in == 3600
        assert result.token_type == "Bearer"
        
        mock_client_instance.authenticate_with_code.assert_called_once_with(code, redirect_uri)

    def test_authenticate_with_code_failure(self, scalekit_service, mock_scalekit_client):
        """Test authentication failure with invalid code."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.authenticate_with_code.side_effect = Exception("Invalid authorization code")
        
        code = "invalid_code"
        redirect_uri = "https://app.example.com/callback"
        
        with pytest.raises(Exception) as exc_info:
            scalekit_service.authenticate_with_code(code, redirect_uri)
        
        assert "Invalid authorization code" in str(exc_info.value)

    def test_get_user_organizations_success(self, scalekit_service, mock_scalekit_client):
        """Test successful retrieval of user organizations."""
        mock_client_instance = mock_scalekit_client.return_value
        
        # Mock organization data
        mock_org1 = Mock()
        mock_org1.id = "org_123"
        mock_org1.name = "Acme Corp"
        mock_org1.display_name = "Acme Corporation"
        mock_org1.domain = "acme.com"
        
        mock_org2 = Mock()
        mock_org2.id = "org_456"
        mock_org2.name = "Tech Startup"
        mock_org2.display_name = "Tech Startup Inc"
        mock_org2.domain = "techstartup.com"
        
        mock_client_instance.get_user_organizations.return_value = [mock_org1, mock_org2]
        
        user_id = "user_123"
        organizations = scalekit_service.get_user_organizations(user_id)
        
        assert len(organizations) == 2
        assert organizations[0].id == "org_123"
        assert organizations[0].name == "Acme Corp"
        assert organizations[0].display_name == "Acme Corporation"
        assert organizations[0].domain == "acme.com"
        assert organizations[1].id == "org_456"
        assert organizations[1].name == "Tech Startup"
        
        mock_client_instance.get_user_organizations.assert_called_once_with(user_id)

    def test_get_user_organizations_empty(self, scalekit_service, mock_scalekit_client):
        """Test retrieval when user has no organizations."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.get_user_organizations.return_value = []
        
        user_id = "user_123"
        organizations = scalekit_service.get_user_organizations(user_id)
        
        assert len(organizations) == 0
        mock_client_instance.get_user_organizations.assert_called_once_with(user_id)

    def test_get_user_organizations_failure(self, scalekit_service, mock_scalekit_client):
        """Test failure when retrieving user organizations."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.get_user_organizations.side_effect = Exception("API error")
        
        user_id = "user_123"
        
        with pytest.raises(Exception) as exc_info:
            scalekit_service.get_user_organizations(user_id)
        
        assert "API error" in str(exc_info.value)

    def test_validate_token_success(self, scalekit_service, mock_scalekit_client):
        """Test successful token validation."""
        mock_client_instance = mock_scalekit_client.return_value
        
        mock_token_info = Mock()
        mock_token_info.sub = "user_123"
        mock_token_info.email = "user@example.com"
        mock_token_info.exp = 1234567890
        
        mock_client_instance.validate_access_token.return_value = mock_token_info
        
        token = "valid_token_123"
        token_info = scalekit_service.validate_token(token)
        
        assert token_info.sub == "user_123"
        assert token_info.email == "user@example.com"
        assert token_info.exp == 1234567890
        
        mock_client_instance.validate_access_token.assert_called_once_with(token)

    def test_validate_token_invalid(self, scalekit_service, mock_scalekit_client):
        """Test validation of invalid token."""
        mock_client_instance = mock_scalekit_client.return_value
        mock_client_instance.validate_access_token.side_effect = Exception("Invalid token")
        
        token = "invalid_token"
        
        with pytest.raises(Exception) as exc_info:
            scalekit_service.validate_token(token)
        
        assert "Invalid token" in str(exc_info.value)


class TestScaleKitUserProfile:
    """Test cases for ScaleKit user profile model."""

    def test_user_profile_creation(self):
        """Test creation of user profile."""
        profile = ScaleKitUserProfile(
            id="user_123",
            email="user@example.com",
            given_name="John",
            family_name="Doe",
            picture="https://example.com/avatar.jpg"
        )
        
        assert profile.id == "user_123"
        assert profile.email == "user@example.com"
        assert profile.given_name == "John"
        assert profile.family_name == "Doe"
        assert profile.picture == "https://example.com/avatar.jpg"

    def test_user_profile_optional_fields(self):
        """Test user profile with optional fields."""
        profile = ScaleKitUserProfile(
            id="user_123",
            email="user@example.com"
        )
        
        assert profile.id == "user_123"
        assert profile.email == "user@example.com"
        assert profile.given_name is None
        assert profile.family_name is None
        assert profile.picture is None


class TestScaleKitAuthResult:
    """Test cases for ScaleKit authentication result model."""

    def test_auth_result_creation(self):
        """Test creation of authentication result."""
        user_profile = ScaleKitUserProfile(
            id="user_123",
            email="user@example.com",
            given_name="John",
            family_name="Doe"
        )
        
        auth_result = ScaleKitAuthResult(
            user=user_profile,
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            id_token="id_token_123",
            expires_in=3600,
            token_type="Bearer"
        )
        
        assert auth_result.user == user_profile
        assert auth_result.access_token == "access_token_123"
        assert auth_result.refresh_token == "refresh_token_123"
        assert auth_result.id_token == "id_token_123"
        assert auth_result.expires_in == 3600
        assert auth_result.token_type == "Bearer"
