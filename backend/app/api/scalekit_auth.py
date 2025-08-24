from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app.services.scalekit_service import scalekit_service
from app.core.middleware import require_auth
from app.utils.supabase_client import supabase
import secrets
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/scalekit", tags=["scalekit-auth"])

class SSOInitiateRequest(BaseModel):
    redirect_uri: str
    organization_id: Optional[str] = None
    connection_id: Optional[str] = None
    login_hint: Optional[str] = None

class SSOCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None
    redirect_uri: str

class SSOInitiateResponse(BaseModel):
    authorization_url: str
    state: str

class SSOCallbackResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    organization: Optional[Dict[str, Any]] = None

@router.post("/initiate", response_model=SSOInitiateResponse)
async def initiate_sso(request: SSOInitiateRequest, response: Response):
    """
    Initiate SSO flow with ScaleKit.
    
    Args:
        request: SSO initiation request with redirect URI and optional parameters
        response: FastAPI response object for setting cookies
        
    Returns:
        Authorization URL and state parameter
        
    Raises:
        HTTPException: If SSO initiation fails
    """
    try:
        # Generate secure state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in secure HTTP-only cookie
        response.set_cookie(
            key="scalekit_state",
            value=state,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=True,  # Set to False for development
            samesite="lax"
        )
        
        # Generate authorization URL
        authorization_url = scalekit_service.get_authorization_url(
            redirect_uri=request.redirect_uri,
            state=state,
            organization_id=request.organization_id,
            connection_id=request.connection_id,
            login_hint=request.login_hint
        )
        
        logger.info(f"Initiated SSO flow with state: {state[:8]}...")
        
        return SSOInitiateResponse(
            authorization_url=authorization_url,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error initiating SSO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SSO: {str(e)}"
        )

@router.post("/callback", response_model=SSOCallbackResponse)
async def handle_sso_callback(
    request: SSOCallbackRequest, 
    http_request: Request,
    response: Response
):
    """
    Handle SSO callback from ScaleKit.
    
    Args:
        request: SSO callback request with authorization code
        http_request: FastAPI request object for accessing cookies
        response: FastAPI response object for setting auth cookies
        
    Returns:
        Authentication response with access token and user data
        
    Raises:
        HTTPException: If callback handling fails
    """
    try:
        # Verify state parameter for CSRF protection
        stored_state = http_request.cookies.get("scalekit_state")
        if not stored_state or stored_state != request.state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Clear state cookie
        response.delete_cookie("scalekit_state")
        
        # Exchange authorization code for tokens and user profile
        auth_result = scalekit_service.authenticate_with_code(
            code=request.code,
            redirect_uri=request.redirect_uri
        )
        
        # Create or update user in Supabase
        user_data = {
            "id": auth_result.user.id,
            "email": auth_result.user.email,
            "full_name": f"{auth_result.user.first_name or ''} {auth_result.user.last_name or ''}".strip(),
            "provider": "scalekit",
            "provider_id": auth_result.user.id,
            "metadata": {
                "scalekit_organization_id": auth_result.user.organization_id,
                "scalekit_metadata": auth_result.user.metadata
            }
        }
        
        # Upsert user in Supabase users table
        supabase.table("users").upsert(user_data, on_conflict="id").execute()
        
        # Handle organization if present
        organization_data = None
        if auth_result.user.organization_id:
            try:
                org_info = scalekit_service.get_organization(auth_result.user.organization_id)
                organization_data = {
                    "id": org_info["id"],
                    "name": org_info["name"],
                    "display_name": org_info["display_name"],
                    "domain": org_info.get("domain")
                }
                
                # Create or update organization in local database
                org_record = {
                    "id": org_info["id"],
                    "name": org_info["name"],
                    "display_name": org_info["display_name"],
                    "domain": org_info.get("domain"),
                    "provider": "scalekit",
                    "settings": org_info.get("settings", {}),
                    "metadata": org_info.get("metadata", {})
                }
                
                supabase.table("organizations").upsert(org_record, on_conflict="id").execute()
                
                # Create user-organization relationship
                user_org_record = {
                    "user_id": auth_result.user.id,
                    "organization_id": org_info["id"],
                    "role": "member",  # Default role, can be updated later
                    "is_active": True
                }
                
                supabase.table("user_organizations").upsert(
                    user_org_record, 
                    on_conflict="user_id,organization_id"
                ).execute()
                
            except Exception as org_error:
                logger.warning(f"Error handling organization: {str(org_error)}")
        
        # Set secure authentication cookies
        response.set_cookie(
            key="scalekit_access_token",
            value=auth_result.access_token,
            max_age=auth_result.expires_in,
            httponly=True,
            secure=True,  # Set to False for development
            samesite="lax"
        )
        
        if auth_result.refresh_token:
            response.set_cookie(
                key="scalekit_refresh_token",
                value=auth_result.refresh_token,
                max_age=86400 * 30,  # 30 days
                httponly=True,
                secure=True,  # Set to False for development
                samesite="lax"
            )
        
        logger.info(f"Successfully authenticated user via ScaleKit: {auth_result.user.email}")
        
        return SSOCallbackResponse(
            access_token=auth_result.access_token,
            user={
                "id": auth_result.user.id,
                "email": auth_result.user.email,
                "full_name": user_data["full_name"],
                "provider": "scalekit"
            },
            organization=organization_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling SSO callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO authentication failed: {str(e)}"
        )

@router.post("/logout")
async def logout_sso(response: Response, current_user: Dict[str, Any] = Depends(require_auth)):
    """
    Logout user from ScaleKit SSO session.
    
    Args:
        response: FastAPI response object for clearing cookies
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        # Clear authentication cookies
        response.delete_cookie("scalekit_access_token")
        response.delete_cookie("scalekit_refresh_token")
        
        # Clear any cached data
        response.delete_cookie("scalekit_state")
        
        logger.info(f"User logged out from ScaleKit: {current_user.get('email', 'unknown')}")
        
        return {"message": "Successfully logged out from SSO"}
        
    except Exception as e:
        logger.error(f"Error during SSO logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/validate")
async def validate_sso_token(http_request: Request):
    """
    Validate ScaleKit access token from cookies.
    
    Args:
        http_request: FastAPI request object for accessing cookies
        
    Returns:
        Token validation status and user info
    """
    try:
        access_token = http_request.cookies.get("scalekit_access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token found"
            )
        
        # Validate token with ScaleKit
        is_valid = scalekit_service.validate_token(access_token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user profile
        user_profile = scalekit_service.get_user_profile(access_token)
        
        return {
            "valid": True,
            "user": {
                "id": user_profile.id,
                "email": user_profile.email,
                "full_name": f"{user_profile.first_name or ''} {user_profile.last_name or ''}".strip(),
                "organization_id": user_profile.organization_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating SSO token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )

@router.get("/redirect")
async def sso_redirect(organization_id: Optional[str] = None):
    """
    Redirect to ScaleKit SSO login page.
    
    Args:
        organization_id: Optional organization ID for direct SSO
        
    Returns:
        Redirect response to ScaleKit authorization URL
    """
    try:
        # Generate state parameter
        state = secrets.token_urlsafe(32)
        
        # Build redirect URI
        redirect_uri = f"{http_request.base_url}auth/scalekit/callback"
        
        # Generate authorization URL
        authorization_url = scalekit_service.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
            organization_id=organization_id
        )
        
        # Create redirect response with state cookie
        response = RedirectResponse(url=authorization_url, status_code=302)
        response.set_cookie(
            key="scalekit_state",
            value=state,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=True,  # Set to False for development
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating SSO redirect: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SSO redirect"
        )
