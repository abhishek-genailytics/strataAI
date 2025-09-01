from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.core.config import settings
from app.utils.supabase_client import supabase

class AuthError(Exception):
    """Custom authentication error."""
    pass

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token using Supabase JWT secret.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthError: If token is invalid or expired
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except JWTError as e:
        raise AuthError(f"Invalid token: {str(e)}")

def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from JWT token using Supabase client.
    
    Args:
        token: JWT token string
        
    Returns:
        User information dict or None if invalid
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Use Supabase client to get user from token
        response = supabase.auth.get_user(token)
        
        if response.user:
            return {
                "id": response.user.id,
                "email": response.user.email,
                "role": "authenticated"
            }
        return None
    except Exception:
        return None

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user details from Supabase by user ID.
    
    Args:
        user_id: User UUID
        
    Returns:
        User data or None if not found
    """
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception:
        return None
