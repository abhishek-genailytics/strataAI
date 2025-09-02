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
    Extract user information from JWT token using direct JWT validation.
    
    Args:
        token: JWT token string
        
    Returns:
        User information dict or None if invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        logger.info(f"Validating token: {token[:20]}...")
        
        # First try direct JWT validation
        try:
            payload = verify_jwt_token(token)
            logger.info(f"JWT payload: {payload}")
            
            if payload and payload.get('sub'):
                user_data = {
                    "id": payload['sub'],
                    "email": payload.get('email', ''),
                    "role": "authenticated"
                }
                logger.info(f"User data from JWT: {user_data}")
                return user_data
        except Exception as jwt_error:
            logger.warning(f"Direct JWT validation failed: {jwt_error}")
        
        # Fallback to Supabase client
        logger.info("Falling back to Supabase client validation")
        response = supabase.auth.get_user(token)
        logger.info(f"Supabase auth response: {response}")
        
        if response.user:
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "role": "authenticated"
            }
            logger.info(f"User data from Supabase: {user_data}")
            return user_data
        else:
            logger.warning("No user found in Supabase auth response")
            return None
    except Exception as e:
        logger.error(f"Error validating token: {e}")
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
