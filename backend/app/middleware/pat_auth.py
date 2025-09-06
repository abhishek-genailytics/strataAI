"""
PAT (Personal Access Token) authentication middleware for unified API gateway.
"""
from typing import Optional, Dict, Any, Callable
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
from ..utils.supabase_client import supabase_service

security = HTTPBearer()

class PATAuthenticationError(Exception):
    """Custom exception for PAT authentication errors."""
    pass

class PATAuthMiddleware:
    """Personal Access Token authentication middleware for unified API."""
    
    @staticmethod
    async def authenticate_pat(token: str) -> Dict[str, Any]:
        """
        Authenticate a Personal Access Token and return user/organization context.
        
        Args:
            token: The PAT token to authenticate
            
        Returns:
            Dict containing user_id, organization_id, and token info
            
        Raises:
            PATAuthenticationError: If authentication fails
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Hash the token to match database storage
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            logger.info(f"PAT Auth: Looking for token hash: {token_hash[:20]}...")
            
            # Query for the PAT first
            pat_response = supabase_service.table("personal_access_tokens").select(
                "id, user_id, organization_id, name, scopes, is_active, expires_at"
            ).eq("token_hash", token_hash).eq("is_active", True).execute()
            
            logger.info(f"PAT Auth: Query result: {pat_response.data}")
            
            if not pat_response.data:
                raise PATAuthenticationError("Invalid or inactive token")
            
            token_data = pat_response.data[0]
            
            # Check token expiration if set
            if token_data.get("expires_at"):
                from datetime import datetime
                import dateutil.parser
                expires_at = dateutil.parser.parse(token_data["expires_at"])
                if datetime.now(expires_at.tzinfo) > expires_at:
                    raise PATAuthenticationError("Token has expired")
            
            # Get user profile
            user_response = supabase_service.table("user_profiles").select(
                "full_name, organization_name"
            ).eq("id", token_data["user_id"]).execute()
            
            user_data = user_response.data[0] if user_response.data else {}
            
            # Get organization info
            org_response = supabase_service.table("organizations").select(
                "name, is_active"
            ).eq("id", token_data["organization_id"]).execute()
            
            if not org_response.data:
                raise PATAuthenticationError("Organization not found")
            
            org_data = org_response.data[0]
            
            # Check if organization is active
            if not org_data["is_active"]:
                raise PATAuthenticationError("Organization is inactive")
            
            return {
                "user_id": token_data["user_id"],
                "organization_id": token_data["organization_id"],
                "token_id": token_data["id"],
                "token_name": token_data["name"],
                "scopes": token_data["scopes"],
                "user_email": user_data.get("organization_name", ""),  # Using organization_name as email placeholder
                "user_name": user_data.get("full_name", ""),
                "organization_name": org_data["name"]
            }
            
        except PATAuthenticationError:
            raise
        except Exception as e:
            raise PATAuthenticationError(f"Authentication failed: {str(e)}")
    
    @staticmethod
    async def get_current_user_from_pat(
        credentials: HTTPAuthorizationCredentials = security
    ) -> Dict[str, Any]:
        """
        Dependency to get current user from PAT token.
        
        Args:
            credentials: HTTP Bearer credentials containing PAT
            
        Returns:
            User and organization context
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # The credentials parameter is HTTPAuthorizationCredentials, access the token directly
            user_context = await PATAuthMiddleware.authenticate_pat(credentials.credentials)
            return user_context
        except PATAuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def check_api_scope(user_context: Dict[str, Any], required_scope: str = "api:write") -> bool:
        """
        Check if the PAT has the required scope for API operations.
        
        Args:
            user_context: User context from PAT authentication
            required_scope: Required scope (default: api:write)
            
        Returns:
            True if scope is granted
            
        Raises:
            HTTPException: If scope is not granted
        """
        scopes = user_context.get("scopes", [])
        if required_scope not in scopes and "api:admin" not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return True

# Convenience function for route dependencies
async def require_pat_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Require PAT authentication for unified API routes."""
    return await PATAuthMiddleware.get_current_user_from_pat(credentials)

async def require_pat_auth_with_scope(
    scope: str = "api:write"
) -> Callable:
    """Create a dependency that requires PAT auth with specific scope."""
    async def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        user_context = await PATAuthMiddleware.get_current_user_from_pat(credentials)
        await PATAuthMiddleware.check_api_scope(user_context, scope)
        return user_context
    return dependency
