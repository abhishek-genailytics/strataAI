from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.utils.supabase_client import supabase
from app.core.middleware import require_auth
from gotrue.errors import AuthApiError

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """
    Register a new user with Supabase Auth.
    
    Args:
        user_data: User registration data
        
    Returns:
        Authentication response with access token
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        # Create user record in users table
        user_record = {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "full_name": user_data.full_name,
            "created_at": auth_response.user.created_at
        }
        
        supabase.table("users").insert(user_record).execute()
        
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": user_data.full_name
            }
        )
        
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLogin):
    """
    Authenticate user with email and password.
    
    Args:
        user_data: User login credentials
        
    Returns:
        Authentication response with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get user details from users table
        user_response = supabase.table("users").select("*").eq("id", auth_response.user.id).execute()
        user_details = user_response.data[0] if user_response.data else {}
        
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": user_details.get("full_name", "")
            }
        )
        
    except AuthApiError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Logout current user by invalidating their session.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from middleware
        
    Returns:
        User information
    """
    try:
        # Get detailed user information from users table
        user_response = supabase.table("users").select("*").eq("id", current_user["id"]).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_response.data[0]
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data.get("full_name", ""),
            "created_at": user_data.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )

@router.put("/profile")
async def update_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Update current user's profile information.
    
    Args:
        profile_data: Profile data to update
        current_user: Current authenticated user
        
    Returns:
        Updated user information
    """
    try:
        # Update user record in users table
        allowed_fields = ["full_name"]
        update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        response = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
