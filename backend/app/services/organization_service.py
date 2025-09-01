from typing import Optional, List, Dict, Any
from uuid import UUID
from app.utils.supabase_client import supabase
from app.models.organization import (
    OrganizationCreate, 
    OrganizationUpdate, 
    Organization,
    UserOrganizationCreate,
    UserOrganizationUpdate,
    UserOrganization
)
import logging

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing organizations and user-organization relationships"""
    
    async def create_organization(self, org_data: OrganizationCreate, owner_id: UUID) -> Optional[Organization]:
        """
        Create a new organization and add the creator as owner.
        
        Args:
            org_data: Organization data
            owner_id: User ID of the organization owner
            
        Returns:
            Created Organization object or None if failed
        """
        try:
            # Create organization
            org_dict = org_data.model_dump()
            org_response = supabase.table("organizations").insert(org_dict).execute()
            
            if not org_response.data:
                return None
            
            org = Organization(**org_response.data[0])
            
            # Add creator as owner
            user_org_data = UserOrganizationCreate(
                user_id=owner_id,
                organization_id=org.id,
                role="owner"
            )
            
            await self.add_user_to_organization(user_org_data)
            
            return org
            
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return None
    
    async def get_organization(self, org_id: UUID) -> Optional[Organization]:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Organization object or None if not found
        """
        try:
            response = supabase.table("organizations").select("*").eq("id", str(org_id)).execute()
            
            if response.data:
                return Organization(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            return None
    
    async def get_organization_by_name(self, name: str) -> Optional[Organization]:
        """
        Get organization by name.
        
        Args:
            name: Organization name
            
        Returns:
            Organization object or None if not found
        """
        try:
            response = supabase.table("organizations").select("*").eq("name", name).execute()
            
            if response.data:
                return Organization(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting organization by name {name}: {e}")
            return None
    
    async def update_organization(self, org_id: UUID, org_data: OrganizationUpdate) -> Optional[Organization]:
        """
        Update organization.
        
        Args:
            org_id: Organization UUID
            org_data: Organization data to update
            
        Returns:
            Updated Organization object or None if failed
        """
        try:
            update_data = org_data.model_dump(exclude_unset=True)
            
            if not update_data:
                return await self.get_organization(org_id)
            
            response = supabase.table("organizations").update(update_data).eq("id", str(org_id)).execute()
            
            if response.data:
                return Organization(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating organization {org_id}: {e}")
            return None
    
    async def delete_organization(self, org_id: UUID) -> bool:
        """
        Delete organization (soft delete by setting is_active to False).
        
        Args:
            org_id: Organization UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = supabase.table("organizations").update({"is_active": False}).eq("id", str(org_id)).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error deleting organization {org_id}: {e}")
            return False
    
    async def get_user_organizations(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all organizations a user belongs to.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of user organizations
        """
        try:
            response = supabase.rpc("get_user_organizations", {"user_uuid": str(user_id)}).execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting user organizations for {user_id}: {e}")
            return []
    
    async def add_user_to_organization(self, user_org_data: UserOrganizationCreate) -> bool:
        """
        Add user to organization.
        
        Args:
            user_org_data: User-organization relationship data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user_org_dict = user_org_data.model_dump()
            response = supabase.table("user_organizations").upsert(
                user_org_dict, 
                on_conflict="user_id,organization_id"
            ).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error adding user to organization: {e}")
            return False
    
    async def remove_user_from_organization(self, user_id: UUID, org_id: UUID) -> bool:
        """
        Remove user from organization (soft delete).
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = supabase.table("user_organizations").update(
                {"is_active": False}
            ).eq("user_id", str(user_id)).eq("organization_id", str(org_id)).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error removing user from organization: {e}")
            return False
    
    async def update_user_role(self, user_id: UUID, org_id: UUID, role: str) -> bool:
        """
        Update user role in organization.
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
            role: New role
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = supabase.table("user_organizations").update(
                {"role": role}
            ).eq("user_id", str(user_id)).eq("organization_id", str(org_id)).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
    
    async def user_belongs_to_organization(self, user_id: UUID, org_id: UUID) -> bool:
        """
        Check if user belongs to organization.
        
        Args:
            user_id: User UUID
            org_id: Organization UUID
            
        Returns:
            True if user belongs to organization, False otherwise
        """
        try:
            response = supabase.rpc(
                "user_belongs_to_organization", 
                {"user_uuid": str(user_id), "org_id": str(org_id)}
            ).execute()
            
            return response.data[0] if response.data else False
            
        except Exception as e:
            logger.error(f"Error checking user organization membership: {e}")
            return False
    
    async def get_organization_members(self, org_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all members of an organization.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            List of organization members
        """
        try:
            response = supabase.table("user_organizations").select(
                "*, user_profiles(*), auth.users(email)"
            ).eq("organization_id", str(org_id)).eq("is_active", True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting organization members for {org_id}: {e}")
            return []

# Create service instance
organization_service = OrganizationService()
