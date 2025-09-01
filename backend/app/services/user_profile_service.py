from typing import Optional, Dict, Any, List
from uuid import UUID
from app.utils.supabase_client import supabase
from app.models.user import UserProfileCreate, UserProfileUpdate, UserProfile
import logging

logger = logging.getLogger(__name__)

class UserProfileService:
    """Service for managing user profiles"""
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            UserProfile object or None if not found
        """
        try:
            response = supabase.table("user_profiles").select("*").eq("id", str(user_id)).execute()
            
            if response.data:
                return UserProfile(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
    
    async def get_user_profile_with_organizations(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user profile with organizations using database function.
        
        Args:
            user_id: User UUID
            
        Returns:
            User profile with organizations or None if not found
        """
        try:
            response = supabase.rpc(
                "get_user_profile_with_organizations",
                {"user_uuid": str(user_id)}
            ).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile with organizations for {user_id}: {e}")
            return None
    
    async def create_user_profile(self, user_id: UUID, profile_data: UserProfileCreate) -> Optional[UserProfile]:
        """
        Create user profile.
        
        Args:
            user_id: User UUID
            profile_data: Profile data
            
        Returns:
            Created UserProfile object or None if failed
        """
        try:
            profile_dict = profile_data.model_dump()
            profile_dict["id"] = str(user_id)
            
            response = supabase.table("user_profiles").insert(profile_dict).execute()
            
            if response.data:
                return UserProfile(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error creating user profile for {user_id}: {e}")
            return None
    
    async def update_user_profile(self, user_id: UUID, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """
        Update user profile.
        
        Args:
            user_id: User UUID
            profile_data: Profile data to update
            
        Returns:
            Updated UserProfile object or None if failed
        """
        try:
            update_data = profile_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_user_profile(user_id)
            
            response = supabase.table("user_profiles").update(update_data).eq("id", str(user_id)).execute()
            
            if response.data:
                return UserProfile(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {e}")
            return None
    
    async def delete_user_profile(self, user_id: UUID) -> bool:
        """
        Delete user profile (soft delete by setting is_active to False).
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = supabase.table("user_profiles").update({"is_active": False}).eq("id", str(user_id)).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error deleting user profile for {user_id}: {e}")
            return False
    
    async def get_user_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User UUID
            
        Returns:
            User preferences dictionary
        """
        try:
            profile = await self.get_user_profile(user_id)
            return profile.preferences if profile else {}
            
        except Exception as e:
            logger.error(f"Error getting user preferences for {user_id}: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: UUID, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User UUID
            preferences: Preferences to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = supabase.table("user_profiles").update({"preferences": preferences}).eq("id", str(user_id)).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating user preferences for {user_id}: {e}")
            return False

# Create service instance
user_profile_service = UserProfileService()
