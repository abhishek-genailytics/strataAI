from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from app.core.database import get_supabase_client
from app.models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate,
    UserOrganization, UserOrganizationCreate, UserOrganizationUpdate,
    OrganizationWithRole, OrganizationMember, OrganizationStats
)
from app.services.scalekit_service import scalekit_service
import logging

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing organizations and user-organization relationships"""
    
    def __init__(self):
        self.supabase: Client = get_supabase_client()
    
    async def create_organization(
        self, 
        org_data: OrganizationCreate,
        creator_user_id: UUID
    ) -> Organization:
        """Create a new organization and add creator as admin"""
        try:
            # Create organization in database
            result = self.supabase.table("organizations").insert({
                "scalekit_organization_id": org_data.scalekit_organization_id,
                "name": org_data.name,
                "display_name": org_data.display_name,
                "domain": org_data.domain,
                "external_id": org_data.external_id,
                "metadata": org_data.metadata,
                "settings": org_data.settings
            }).execute()
            
            if not result.data:
                raise Exception("Failed to create organization")
            
            org_record = result.data[0]
            organization = Organization(**org_record)
            
            # Add creator as admin
            await self.add_user_to_organization(
                user_id=creator_user_id,
                organization_id=organization.id,
                role="admin",
                scalekit_user_id=None
            )
            
            logger.info(f"Created organization: {organization.id}")
            return organization
            
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}")
            raise Exception(f"Failed to create organization: {str(e)}")
    
    async def get_organization(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        try:
            result = self.supabase.table("organizations").select("*").eq("id", str(organization_id)).execute()
            
            if not result.data:
                return None
            
            return Organization(**result.data[0])
            
        except Exception as e:
            logger.error(f"Error getting organization: {str(e)}")
            return None
    
    async def get_organization_by_scalekit_id(self, scalekit_org_id: str) -> Optional[Organization]:
        """Get organization by ScaleKit organization ID"""
        try:
            result = self.supabase.table("organizations").select("*").eq("scalekit_organization_id", scalekit_org_id).execute()
            
            if not result.data:
                return None
            
            return Organization(**result.data[0])
            
        except Exception as e:
            logger.error(f"Error getting organization by ScaleKit ID: {str(e)}")
            return None
    
    async def update_organization(
        self, 
        organization_id: UUID, 
        org_data: OrganizationUpdate
    ) -> Optional[Organization]:
        """Update organization"""
        try:
            update_data = {k: v for k, v in org_data.dict(exclude_unset=True).items()}
            
            if not update_data:
                return await self.get_organization(organization_id)
            
            result = self.supabase.table("organizations").update(update_data).eq("id", str(organization_id)).execute()
            
            if not result.data:
                return None
            
            return Organization(**result.data[0])
            
        except Exception as e:
            logger.error(f"Error updating organization: {str(e)}")
            return None
    
    async def delete_organization(self, organization_id: UUID) -> bool:
        """Soft delete organization (set is_active to false)"""
        try:
            result = self.supabase.table("organizations").update({"is_active": False}).eq("id", str(organization_id)).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deleting organization: {str(e)}")
            return False
    
    async def get_user_organizations(self, user_id: UUID) -> List[OrganizationWithRole]:
        """Get all organizations for a user with their roles"""
        try:
            result = self.supabase.rpc("get_user_organizations", {"user_uuid": str(user_id)}).execute()
            
            organizations = []
            for record in result.data:
                org = await self.get_organization(UUID(record["organization_id"]))
                if org:
                    org_with_role = OrganizationWithRole(
                        **org.dict(),
                        user_role=record["user_role"],
                        user_joined_at=record.get("joined_at")
                    )
                    organizations.append(org_with_role)
            
            return organizations
            
        except Exception as e:
            logger.error(f"Error getting user organizations: {str(e)}")
            return []
    
    async def add_user_to_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str = "member",
        scalekit_user_id: Optional[str] = None
    ) -> Optional[UserOrganization]:
        """Add user to organization"""
        try:
            result = self.supabase.table("user_organizations").insert({
                "user_id": str(user_id),
                "organization_id": str(organization_id),
                "role": role,
                "scalekit_user_id": scalekit_user_id
            }).execute()
            
            if not result.data:
                return None
            
            return UserOrganization(**result.data[0])
            
        except Exception as e:
            logger.error(f"Error adding user to organization: {str(e)}")
            return None
    
    async def update_user_organization_role(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str
    ) -> Optional[UserOrganization]:
        """Update user's role in organization"""
        try:
            result = self.supabase.table("user_organizations").update({
                "role": role
            }).eq("user_id", str(user_id)).eq("organization_id", str(organization_id)).execute()
            
            if not result.data:
                return None
            
            return UserOrganization(**result.data[0])
            
        except Exception as e:
            logger.error(f"Error updating user organization role: {str(e)}")
            return None
    
    async def remove_user_from_organization(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Remove user from organization (soft delete)"""
        try:
            result = self.supabase.table("user_organizations").update({
                "is_active": False
            }).eq("user_id", str(user_id)).eq("organization_id", str(organization_id)).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error removing user from organization: {str(e)}")
            return False
    
    async def get_organization_members(self, organization_id: UUID) -> List[OrganizationMember]:
        """Get all members of an organization"""
        try:
            # Get user organizations with user details
            result = self.supabase.table("user_organizations").select(
                "*, auth.users(email)"
            ).eq("organization_id", str(organization_id)).eq("is_active", True).execute()
            
            members = []
            for record in result.data:
                member = OrganizationMember(
                    user_id=UUID(record["user_id"]),
                    email=record["users"]["email"] if record.get("users") else "",
                    role=record["role"],
                    scalekit_user_id=record.get("scalekit_user_id"),
                    is_active=record["is_active"],
                    joined_at=record["joined_at"]
                )
                members.append(member)
            
            return members
            
        except Exception as e:
            logger.error(f"Error getting organization members: {str(e)}")
            return []
    
    async def user_belongs_to_organization(
        self, 
        user_id: UUID, 
        organization_id: UUID
    ) -> bool:
        """Check if user belongs to organization"""
        try:
            result = self.supabase.rpc(
                "user_belongs_to_organization", 
                {"user_uuid": str(user_id), "org_id": str(organization_id)}
            ).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error checking user organization membership: {str(e)}")
            return False
    
    async def get_organization_stats(self, organization_id: UUID) -> OrganizationStats:
        """Get organization statistics"""
        try:
            # Get member count
            members_result = self.supabase.table("user_organizations").select(
                "id", count="exact"
            ).eq("organization_id", str(organization_id)).eq("is_active", True).execute()
            
            total_members = members_result.count or 0
            active_members = total_members  # All active members
            
            # Get API key count
            api_keys_result = self.supabase.table("api_keys").select(
                "id", count="exact"
            ).eq("organization_id", str(organization_id)).execute()
            
            total_api_keys = api_keys_result.count or 0
            
            # Get request count and cost
            requests_result = self.supabase.table("api_requests").select(
                "id, cost_usd", count="exact"
            ).eq("organization_id", str(organization_id)).execute()
            
            total_requests = requests_result.count or 0
            total_cost = sum(float(req.get("cost_usd", 0)) for req in requests_result.data) if requests_result.data else 0
            
            # Get last activity
            last_activity_result = self.supabase.table("api_requests").select(
                "created_at"
            ).eq("organization_id", str(organization_id)).order("created_at", desc=True).limit(1).execute()
            
            last_activity = None
            if last_activity_result.data:
                last_activity = last_activity_result.data[0]["created_at"]
            
            return OrganizationStats(
                total_members=total_members,
                active_members=active_members,
                total_api_keys=total_api_keys,
                total_requests=total_requests,
                total_cost=total_cost,
                last_activity=last_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting organization stats: {str(e)}")
            return OrganizationStats(
                total_members=0,
                active_members=0,
                total_api_keys=0,
                total_requests=0,
                total_cost=0.0
            )
    
    async def sync_with_scalekit(self, organization_id: UUID) -> bool:
        """Sync organization data with ScaleKit"""
        try:
            org = await self.get_organization(organization_id)
            if not org:
                return False
            
            # Get organization data from ScaleKit
            scalekit_org = scalekit_service.get_organization(org.scalekit_organization_id)
            
            # Update local organization with ScaleKit data
            update_data = OrganizationUpdate(
                display_name=scalekit_org.get("display_name"),
                domain=scalekit_org.get("domain"),
                metadata=scalekit_org.get("metadata", {}),
                settings=scalekit_org.get("settings", {})
            )
            
            await self.update_organization(organization_id, update_data)
            
            logger.info(f"Synced organization {organization_id} with ScaleKit")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing organization with ScaleKit: {str(e)}")
            return False

# Global instance
organization_service = OrganizationService()
