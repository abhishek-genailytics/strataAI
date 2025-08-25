from typing import Optional, Dict, Any, List
from scalekit import ScalekitClient, AuthorizationUrlOptions, CodeAuthenticationOptions
from app.core.config import settings
from app.models.organization import ScaleKitUserProfile, ScaleKitAuthResult
import logging

logger = logging.getLogger(__name__)

class ScaleKitService:
    """Service for ScaleKit authentication and organization management"""
    
    def __init__(self):
        try:
            # Only initialize ScaleKit client if credentials are properly configured
            if (settings.SCALEKIT_ENVIRONMENT_URL and 
                settings.SCALEKIT_CLIENT_ID and 
                settings.SCALEKIT_CLIENT_SECRET and
                not settings.SCALEKIT_ENVIRONMENT_URL.startswith('https://example')):
                self.client = ScalekitClient(
                    env_url=settings.SCALEKIT_ENVIRONMENT_URL,
                    client_id=settings.SCALEKIT_CLIENT_ID,
                    client_secret=settings.SCALEKIT_CLIENT_SECRET
                )
            else:
                logger.warning("ScaleKit credentials not configured, running in development mode")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize ScaleKit client: {e}")
            self.client = None
    
    def get_authorization_url(
        self, 
        redirect_uri: str, 
        state: Optional[str] = None,
        organization_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        login_hint: Optional[str] = None
    ) -> str:
        """Generate authorization URL for SSO flow"""
        try:
            options = AuthorizationUrlOptions()
            
            if state:
                options.state = state
            if organization_id:
                options.organization_id = organization_id
            if connection_id:
                options.connection_id = connection_id
            if login_hint:
                options.login_hint = login_hint
            
            # Set default scopes
            options.scopes = ['openid', 'profile', 'email']
            
            authorization_url = self.client.get_authorization_url(
                redirect_uri=redirect_uri,
                options=options
            )
            
            logger.info(f"Generated authorization URL for redirect_uri: {redirect_uri}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise Exception(f"Failed to generate authorization URL: {str(e)}")
    
    def authenticate_with_code(
        self, 
        code: str, 
        redirect_uri: str
    ) -> ScaleKitAuthResult:
        """Exchange authorization code for user profile and tokens"""
        try:
            options = CodeAuthenticationOptions()
            
            auth_result = self.client.authenticate_with_code(
                code=code,
                redirect_uri=redirect_uri,
                options=options
            )
            
            # Extract user information
            user_data = auth_result.user
            
            # Create ScaleKit user profile
            user_profile = ScaleKitUserProfile(
                id=user_data.id,
                email=user_data.email,
                first_name=getattr(user_data, 'first_name', None),
                last_name=getattr(user_data, 'last_name', None),
                display_name=getattr(user_data, 'display_name', None),
                organization_id=getattr(user_data, 'organization_id', ''),
                metadata=getattr(user_data, 'metadata', {})
            )
            
            # Create authentication result
            result = ScaleKitAuthResult(
                user=user_profile,
                access_token=auth_result.access_token,
                id_token=getattr(auth_result, 'id_token', None),
                refresh_token=getattr(auth_result, 'refresh_token', None),
                expires_in=getattr(auth_result, 'expires_in', 3600),
                token_type=getattr(auth_result, 'token_type', 'Bearer')
            )
            
            logger.info(f"Successfully authenticated user: {user_profile.email}")
            return result
            
        except Exception as e:
            logger.error(f"Error authenticating with code: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_user_profile(self, access_token: str) -> ScaleKitUserProfile:
        """Get user profile using access token"""
        try:
            # Use ScaleKit client to get user profile
            user_data = self.client.get_user(access_token)
            
            user_profile = ScaleKitUserProfile(
                id=user_data.id,
                email=user_data.email,
                first_name=getattr(user_data, 'first_name', None),
                last_name=getattr(user_data, 'last_name', None),
                display_name=getattr(user_data, 'display_name', None),
                organization_id=getattr(user_data, 'organization_id', ''),
                metadata=getattr(user_data, 'metadata', {})
            )
            
            return user_profile
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise Exception(f"Failed to get user profile: {str(e)}")
    
    def validate_token(self, access_token: str) -> bool:
        """Validate ScaleKit access token"""
        try:
            # Attempt to get user profile to validate token
            self.get_user_profile(access_token)
            return True
        except Exception:
            return False
    
    def create_organization(
        self, 
        name: str, 
        display_name: Optional[str] = None,
        domain: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create organization in ScaleKit"""
        try:
            org_data = {
                "name": name,
                "display_name": display_name or name,
                "external_id": external_id
            }
            
            if domain:
                org_data["domain"] = domain
            
            # Create organization using ScaleKit API
            organization = self.client.organization.create_organization(org_data)
            
            logger.info(f"Created organization in ScaleKit: {organization.id}")
            return {
                "id": organization.id,
                "name": organization.name,
                "display_name": organization.display_name,
                "domain": getattr(organization, 'domain', None),
                "external_id": getattr(organization, 'external_id', None)
            }
            
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}")
            raise Exception(f"Failed to create organization: {str(e)}")
    
    def get_organization(self, organization_id: str) -> Dict[str, Any]:
        """Get organization details from ScaleKit"""
        try:
            organization = self.client.organization.get_organization(organization_id)
            
            return {
                "id": organization.id,
                "name": organization.name,
                "display_name": organization.display_name,
                "domain": getattr(organization, 'domain', None),
                "external_id": getattr(organization, 'external_id', None),
                "metadata": getattr(organization, 'metadata', {}),
                "settings": getattr(organization, 'settings', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting organization: {str(e)}")
            raise Exception(f"Failed to get organization: {str(e)}")
    
    def update_organization(
        self, 
        organization_id: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Update organization in ScaleKit"""
        try:
            organization = self.client.organization.update_organization(
                organization_id, 
                kwargs
            )
            
            logger.info(f"Updated organization in ScaleKit: {organization_id}")
            return {
                "id": organization.id,
                "name": organization.name,
                "display_name": organization.display_name,
                "domain": getattr(organization, 'domain', None),
                "external_id": getattr(organization, 'external_id', None)
            }
            
        except Exception as e:
            logger.error(f"Error updating organization: {str(e)}")
            raise Exception(f"Failed to update organization: {str(e)}")
    
    def list_organization_users(self, organization_id: str) -> List[Dict[str, Any]]:
        """List users in an organization"""
        try:
            users = self.client.organization.list_organization_users(organization_id)
            
            return [
                {
                    "id": user.id,
                    "email": user.email,
                    "first_name": getattr(user, 'first_name', None),
                    "last_name": getattr(user, 'last_name', None),
                    "display_name": getattr(user, 'display_name', None),
                    "role": getattr(user, 'role', 'member'),
                    "is_active": getattr(user, 'is_active', True)
                }
                for user in users
            ]
            
        except Exception as e:
            logger.error(f"Error listing organization users: {str(e)}")
            raise Exception(f"Failed to list organization users: {str(e)}")
    
    def generate_admin_portal_link(
        self, 
        organization_id: str, 
        features: Optional[List[str]] = None
    ) -> str:
        """Generate admin portal link for organization"""
        try:
            features = features or ['sso', 'dir_sync']
            
            portal_link = self.client.organization.create_portal_link(
                organization_id=organization_id,
                features=features
            )
            
            logger.info(f"Generated admin portal link for org: {organization_id}")
            return portal_link.url
            
        except Exception as e:
            logger.error(f"Error generating admin portal link: {str(e)}")
            raise Exception(f"Failed to generate admin portal link: {str(e)}")

# Global instance
scalekit_service = ScaleKitService()
