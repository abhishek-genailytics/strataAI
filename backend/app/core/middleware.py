from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.auth import get_user_from_token, AuthError

security = HTTPBearer()

class AuthMiddleware:
    """JWT Authentication middleware for FastAPI."""
    
    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = security):
        """
        Dependency to get current authenticated user from JWT token.
        
        Args:
            credentials: HTTP Bearer credentials
            
        Returns:
            User information dict
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user_from_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    @staticmethod
    def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = security):
        """
        Optional dependency to get current user if token is provided.
        
        Args:
            credentials: Optional HTTP Bearer credentials
            
        Returns:
            User information dict or None
        """
        if not credentials:
            return None
        
        return get_user_from_token(credentials.credentials)

# Convenience functions for route dependencies
def require_auth(credentials: HTTPAuthorizationCredentials = security):
    """Require authentication for route."""
    return AuthMiddleware.get_current_user(credentials)

def optional_auth(credentials: Optional[HTTPAuthorizationCredentials] = security):
    """Optional authentication for route."""
    return AuthMiddleware.get_optional_user(credentials)
