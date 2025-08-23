import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.utils.auth import verify_jwt_token, get_user_from_token, AuthError

# Test client
client = TestClient(app)

class TestAuthUtils:
    """Test authentication utility functions."""
    
    def test_verify_jwt_token_valid(self):
        """Test JWT token verification with valid token."""
        # Mock a valid JWT payload
        mock_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated"
        }
        
        with patch('app.utils.auth.jwt.decode', return_value=mock_payload):
            result = verify_jwt_token("valid.jwt.token")
            assert result == mock_payload
    
    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token."""
        with patch('app.utils.auth.jwt.decode', side_effect=Exception("Invalid token")):
            with pytest.raises(AuthError):
                verify_jwt_token("invalid.jwt.token")
    
    def test_get_user_from_token_valid(self):
        """Test user extraction from valid token."""
        mock_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "authenticated"
        }
        
        with patch('app.utils.auth.verify_jwt_token', return_value=mock_payload):
            result = get_user_from_token("valid.jwt.token")
            assert result["id"] == "user-123"
            assert result["email"] == "test@example.com"
            assert result["role"] == "authenticated"
    
    def test_get_user_from_token_invalid(self):
        """Test user extraction from invalid token."""
        with patch('app.utils.auth.verify_jwt_token', side_effect=AuthError("Invalid")):
            result = get_user_from_token("invalid.jwt.token")
            assert result is None

class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    @patch('app.api.auth.supabase')
    def test_register_success(self, mock_supabase):
        """Test successful user registration."""
        # Mock Supabase auth response
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        
        mock_session = MagicMock()
        mock_session.access_token = "mock.jwt.token"
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        mock_supabase.auth.sign_up.return_value = mock_auth_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = None
        
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock.jwt.token"
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
    
    @patch('app.api.auth.supabase')
    def test_register_failure(self, mock_supabase):
        """Test failed user registration."""
        from gotrue.errors import AuthApiError
        
        mock_supabase.auth.sign_up.side_effect = AuthApiError("Email already exists")
        
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        
        assert response.status_code == 400
    
    @patch('app.api.auth.supabase')
    def test_login_success(self, mock_supabase):
        """Test successful user login."""
        # Mock Supabase auth response
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        
        mock_session = MagicMock()
        mock_session.access_token = "mock.jwt.token"
        
        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_auth_response
        
        # Mock user details response
        mock_table_response = MagicMock()
        mock_table_response.data = [{"id": "user-123", "email": "test@example.com", "full_name": "Test User"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_table_response
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock.jwt.token"
        assert data["user"]["email"] == "test@example.com"
    
    @patch('app.api.auth.supabase')
    def test_login_invalid_credentials(self, mock_supabase):
        """Test login with invalid credentials."""
        from gotrue.errors import AuthApiError
        
        mock_supabase.auth.sign_in_with_password.side_effect = AuthApiError("Invalid credentials")
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    @patch('app.api.auth.supabase')
    @patch('app.core.middleware.get_user_from_token')
    def test_logout_success(self, mock_get_user, mock_supabase):
        """Test successful logout."""
        mock_get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        mock_supabase.auth.sign_out.return_value = None
        
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    @patch('app.core.middleware.get_user_from_token')
    @patch('app.api.auth.supabase')
    def test_get_current_user_success(self, mock_supabase, mock_get_user):
        """Test getting current user information."""
        mock_get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        
        # Mock user details response
        mock_table_response = MagicMock()
        mock_table_response.data = [{
            "id": "user-123",
            "email": "test@example.com",
            "full_name": "Test User",
            "created_at": "2023-01-01T00:00:00Z"
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_table_response
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer mock.jwt.token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
    
    def test_get_current_user_unauthorized(self):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @patch('app.core.middleware.get_user_from_token')
    @patch('app.api.auth.supabase')
    def test_update_profile_success(self, mock_supabase, mock_get_user):
        """Test successful profile update."""
        mock_get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        
        # Mock update response
        mock_table_response = MagicMock()
        mock_table_response.data = [{
            "id": "user-123",
            "email": "test@example.com",
            "full_name": "Updated Name"
        }]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_table_response
        
        response = client.put(
            "/api/v1/auth/profile",
            json={"full_name": "Updated Name"},
            headers={"Authorization": "Bearer mock.jwt.token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

class TestAuthMiddleware:
    """Test authentication middleware."""
    
    @patch('app.core.middleware.get_user_from_token')
    def test_require_auth_valid_token(self, mock_get_user):
        """Test require_auth with valid token."""
        from app.core.middleware import require_auth
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        result = require_auth(credentials)
        
        assert result["id"] == "user-123"
        assert result["email"] == "test@example.com"
    
    def test_require_auth_no_credentials(self):
        """Test require_auth without credentials."""
        from app.core.middleware import require_auth
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            require_auth(None)
        
        assert exc_info.value.status_code == 401
    
    @patch('app.core.middleware.get_user_from_token')
    def test_optional_auth_valid_token(self, mock_get_user):
        """Test optional_auth with valid token."""
        from app.core.middleware import optional_auth
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_get_user.return_value = {"id": "user-123", "email": "test@example.com"}
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        result = optional_auth(credentials)
        
        assert result["id"] == "user-123"
    
    def test_optional_auth_no_credentials(self):
        """Test optional_auth without credentials."""
        from app.core.middleware import optional_auth
        
        result = optional_auth(None)
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__])
