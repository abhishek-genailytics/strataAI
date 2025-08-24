from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class OrganizationBase(BaseModel):
    name: str = Field(..., description="Organization name")
    display_name: Optional[str] = Field(None, description="Human-readable display name")
    domain: Optional[str] = Field(None, description="Organization domain")
    external_id: Optional[str] = Field(None, description="External identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization settings")

class OrganizationCreate(OrganizationBase):
    scalekit_organization_id: str = Field(..., description="ScaleKit organization ID")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    domain: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None

class Organization(OrganizationBase):
    id: UUID
    scalekit_organization_id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserOrganizationBase(BaseModel):
    role: str = Field(default="member", description="User role in organization")
    scalekit_user_id: Optional[str] = Field(None, description="ScaleKit user ID")

class UserOrganizationCreate(UserOrganizationBase):
    user_id: UUID
    organization_id: UUID

class UserOrganizationUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserOrganization(UserOrganizationBase):
    id: UUID
    user_id: UUID
    organization_id: UUID
    is_active: bool = True
    joined_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrganizationWithRole(Organization):
    """Organization with user's role"""
    user_role: str
    user_joined_at: datetime

class OrganizationMember(BaseModel):
    """Organization member information"""
    user_id: UUID
    email: str
    role: str
    scalekit_user_id: Optional[str] = None
    is_active: bool = True
    joined_at: datetime

class OrganizationInvite(BaseModel):
    """Organization invitation"""
    email: str
    role: str = "member"
    organization_id: UUID

class ScaleKitUserProfile(BaseModel):
    """ScaleKit user profile from authentication"""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    organization_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScaleKitAuthResult(BaseModel):
    """Result from ScaleKit authentication"""
    user: ScaleKitUserProfile
    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"

class OrganizationStats(BaseModel):
    """Organization statistics"""
    total_members: int
    active_members: int
    total_api_keys: int
    total_requests: int
    total_cost: float
    last_activity: Optional[datetime] = None
