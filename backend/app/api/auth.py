from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.utils.supabase_client import supabase
from app.core.middleware import require_auth
from app.models.user import UserProfileCreate, UserProfileUpdate
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
    Register a new user with Supabase Auth and create user profile.
    
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
        
        # Ensure user profile exists (trigger should create it, but let's be safe)
        try:
            # Try to update first (in case profile exists)
            profile_data = {
                "full_name": user_data.full_name
            }
            supabase.table("user_profiles").update(profile_data).eq("id", auth_response.user.id).execute()
        except Exception:
            # If update fails, try to insert (in case trigger didn't work)
            profile_data = {
                "id": auth_response.user.id,
                "full_name": user_data.full_name,
                "created_at": auth_response.user.created_at,
                "updated_at": auth_response.user.updated_at
            }
            supabase.table("user_profiles").insert(profile_data).execute()
        
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
        
        # Get user profile details
        profile_response = supabase.table("user_profiles").select("*").eq("id", auth_response.user.id).execute()
        profile_data = profile_response.data[0] if profile_response.data else {}
        
        return AuthResponse(
            access_token=auth_response.session.access_token,
            user={
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "full_name": profile_data.get("full_name", "")
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
    Logout current user.
    
    Args:
        current_user: Current authenticated user from middleware
        
    Returns:
        Success message
    """
    try:
        # Supabase handles logout automatically when token expires
        # This endpoint can be used for additional cleanup if needed
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user(current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Get current authenticated user information with profile.
    
    Args:
        current_user: Current authenticated user from middleware
        
    Returns:
        User information with profile
    """
    try:
        # Get user profile with organizations using the database function
        response = supabase.rpc(
            "get_user_profile_with_organizations",
            {"user_uuid": current_user["id"]}
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = response.data[0]
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )

@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Update current user's profile information.
    
    Args:
        profile_data: Profile data to update
        current_user: Current authenticated user
        
    Returns:
        Updated user profile
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = profile_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        response = supabase.table("user_profiles").update(update_data).eq("id", current_user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/reset-password")
async def reset_password(email: str):
    """
    Send password reset email.
    
    Args:
        email: User email address
        
    Returns:
        Success message
    """
    try:
        supabase.auth.reset_password_email(email)
        return {"message": "Password reset email sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )
