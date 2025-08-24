import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from app.main import app
from app.core.deps import get_current_user, get_organization_context
from app.services.scalekit_service import ScaleKitService, ScaleKitAuthResult, ScaleKitUserProfile


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": "user_123",
        "email": "user@example.com",
        "name": "John Doe"
    }


@pytest.fixture
def mock_organization():
    """Mock organization."""
    return {
        "id": "org_123",
        "name": "Acme Corp",
        "display_name": "Acme Corporation",
        "domain": "acme.com",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_user_organization():
    """Mock user organization relationship."""
    return {
        "id": "user_org_123",
        "user_id": "user_123",
        "organization_id": "org_123",
        "role": "admin",
        "is_active": True,
        "joined_at": "2024-01-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


class TestOrganizationsAPI:
    """Test cases for organizations API endpoints."""

    def test_get_user_organizations_success(self, client, mock_user, mock_organization, mock_user_organization):
        """Test successful retrieval of user organizations."""
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            # Mock database response
            mock_response = Mock()
            mock_response.data = [
                {
                    **mock_user_organization,
                    "organization": mock_organization
                }
            ]
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.get("/organizations/user-organizations")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == mock_user_organization["id"]
            assert data[0]["role"] == "admin"
            assert data[0]["organization"]["id"] == mock_organization["id"]
            assert data[0]["organization"]["name"] == "Acme Corp"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_user_organizations_empty(self, client, mock_user):
        """Test retrieval when user has no organizations."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = []
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.get("/organizations/user-organizations")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 0
        
        app.dependency_overrides.clear()

    def test_get_user_organizations_unauthorized(self, client):
        """Test unauthorized access to user organizations."""
        response = client.get("/organizations/user-organizations")
        assert response.status_code == 401

    def test_initiate_sso_success(self, client, mock_user):
        """Test successful SSO initiation."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.ScaleKitService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_authorization_url.return_value = "https://auth.example.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            response = client.get("/organizations/sso/login?redirect_uri=https://app.example.com/callback")
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert data["authorization_url"] == "https://auth.example.com/oauth/authorize"
            
            mock_service.get_authorization_url.assert_called_once_with(
                redirect_uri="https://app.example.com/callback",
                state=None,
                organization_id=None,
                connection_id=None,
                login_hint=None
            )
        
        app.dependency_overrides.clear()

    def test_initiate_sso_with_parameters(self, client, mock_user):
        """Test SSO initiation with optional parameters."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.ScaleKitService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_authorization_url.return_value = "https://auth.example.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            params = {
                "redirect_uri": "https://app.example.com/callback",
                "organization_id": "org_123",
                "connection_id": "conn_456",
                "login_hint": "user@example.com"
            }
            
            response = client.get("/organizations/sso/login", params=params)
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            
            mock_service.get_authorization_url.assert_called_once_with(
                redirect_uri="https://app.example.com/callback",
                state=None,
                organization_id="org_123",
                connection_id="conn_456",
                login_hint="user@example.com"
            )
        
        app.dependency_overrides.clear()

    def test_initiate_sso_missing_redirect_uri(self, client, mock_user):
        """Test SSO initiation without redirect URI."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = client.get("/organizations/sso/login")
        assert response.status_code == 422  # Validation error
        
        app.dependency_overrides.clear()

    def test_handle_sso_callback_success(self, client):
        """Test successful SSO callback handling."""
        with patch('app.api.organizations.ScaleKitService') as mock_service_class:
            mock_service = Mock()
            
            # Mock successful authentication
            mock_user_profile = ScaleKitUserProfile(
                id="scalekit_user_123",
                email="user@example.com",
                given_name="John",
                family_name="Doe"
            )
            
            mock_auth_result = ScaleKitAuthResult(
                user=mock_user_profile,
                access_token="access_token_123",
                refresh_token="refresh_token_123",
                id_token="id_token_123",
                expires_in=3600,
                token_type="Bearer"
            )
            
            mock_service.authenticate_with_code.return_value = mock_auth_result
            mock_service_class.return_value = mock_service
            
            # Mock Supabase operations
            with patch('app.api.organizations.supabase') as mock_supabase:
                # Mock user lookup/creation
                mock_user_response = Mock()
                mock_user_response.data = [{
                    "id": "user_123",
                    "email": "user@example.com",
                    "name": "John Doe"
                }]
                mock_user_response.error = None
                
                mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user_response
                
                callback_data = {
                    "code": "auth_code_123",
                    "redirect_uri": "https://app.example.com/callback"
                }
                
                response = client.post("/organizations/sso/callback", json=callback_data)
                
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "user" in data
                assert data["access_token"] == "access_token_123"
                
                mock_service.authenticate_with_code.assert_called_once_with(
                    "auth_code_123",
                    "https://app.example.com/callback"
                )

    def test_handle_sso_callback_invalid_code(self, client):
        """Test SSO callback with invalid authorization code."""
        with patch('app.api.organizations.ScaleKitService') as mock_service_class:
            mock_service = Mock()
            mock_service.authenticate_with_code.side_effect = Exception("Invalid authorization code")
            mock_service_class.return_value = mock_service
            
            callback_data = {
                "code": "invalid_code",
                "redirect_uri": "https://app.example.com/callback"
            }
            
            response = client.post("/organizations/sso/callback", json=callback_data)
            assert response.status_code == 400

    def test_handle_sso_callback_missing_data(self, client):
        """Test SSO callback with missing required data."""
        response = client.post("/organizations/sso/callback", json={})
        assert response.status_code == 422  # Validation error

    def test_get_organization_details_success(self, client, mock_user, mock_organization):
        """Test successful retrieval of organization details."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_organization_context] = lambda: mock_organization
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = [mock_organization]
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.get(f"/organizations/{mock_organization['id']}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_organization["id"]
            assert data["name"] == mock_organization["name"]
            assert data["display_name"] == mock_organization["display_name"]
        
        app.dependency_overrides.clear()

    def test_get_organization_details_not_found(self, client, mock_user):
        """Test retrieval of non-existent organization."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = []
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.get("/organizations/nonexistent_org")
            assert response.status_code == 404
        
        app.dependency_overrides.clear()

    def test_get_organization_details_unauthorized(self, client):
        """Test unauthorized access to organization details."""
        response = client.get("/organizations/org_123")
        assert response.status_code == 401

    def test_update_organization_success(self, client, mock_user, mock_organization):
        """Test successful organization update."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_organization_context] = lambda: mock_organization
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            # Mock user role check (admin)
            mock_user_org_response = Mock()
            mock_user_org_response.data = [{
                "role": "admin",
                "is_active": True
            }]
            mock_user_org_response.error = None
            
            # Mock update operation
            mock_update_response = Mock()
            updated_org = {**mock_organization, "display_name": "Updated Acme Corp"}
            mock_update_response.data = [updated_org]
            mock_update_response.error = None
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_user_org_response
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
            
            update_data = {"display_name": "Updated Acme Corp"}
            response = client.put(f"/organizations/{mock_organization['id']}", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Acme Corp"
        
        app.dependency_overrides.clear()

    def test_update_organization_forbidden(self, client, mock_user, mock_organization):
        """Test organization update by non-admin user."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_organization_context] = lambda: mock_organization
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            # Mock user role check (member, not admin)
            mock_user_org_response = Mock()
            mock_user_org_response.data = [{
                "role": "member",
                "is_active": True
            }]
            mock_user_org_response.error = None
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_user_org_response
            
            update_data = {"display_name": "Updated Acme Corp"}
            response = client.put(f"/organizations/{mock_organization['id']}", json=update_data)
            
            assert response.status_code == 403
        
        app.dependency_overrides.clear()

    def test_leave_organization_success(self, client, mock_user, mock_organization):
        """Test successful organization leave."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_organization_context] = lambda: mock_organization
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = [{"id": "user_org_123"}]
            mock_response.error = None
            
            mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.delete(f"/organizations/{mock_organization['id']}/leave")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Successfully left organization"
        
        app.dependency_overrides.clear()

    def test_leave_organization_not_member(self, client, mock_user, mock_organization):
        """Test leaving organization when not a member."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_organization_context] = lambda: mock_organization
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = []
            mock_response.error = None
            
            mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
            
            response = client.delete(f"/organizations/{mock_organization['id']}/leave")
            
            assert response.status_code == 404
        
        app.dependency_overrides.clear()


class TestOrganizationMiddleware:
    """Test cases for organization context middleware."""

    def test_organization_context_header(self, client, mock_user, mock_organization):
        """Test organization context from header."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            # Mock organization lookup
            mock_response = Mock()
            mock_response.data = [mock_organization]
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            # Mock user organization membership check
            mock_user_org_response = Mock()
            mock_user_org_response.data = [{
                "role": "admin",
                "is_active": True
            }]
            mock_user_org_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_user_org_response
            
            headers = {"X-Organization-ID": mock_organization["id"]}
            response = client.get("/organizations/user-organizations", headers=headers)
            
            assert response.status_code == 200
        
        app.dependency_overrides.clear()

    def test_organization_context_invalid_header(self, client, mock_user):
        """Test invalid organization context header."""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        with patch('app.api.organizations.supabase') as mock_supabase:
            mock_response = Mock()
            mock_response.data = []
            mock_response.error = None
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            headers = {"X-Organization-ID": "nonexistent_org"}
            response = client.get("/organizations/user-organizations", headers=headers)
            
            assert response.status_code == 403  # Forbidden - not a member of organization
        
        app.dependency_overrides.clear()
