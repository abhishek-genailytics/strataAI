from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., description="Organization name")
    display_name: Optional[str] = None
    domain: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(OrganizationBase):
    name: Optional[str] = None
    display_name: Optional[str] = None
    domain: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserOrganizationBase(BaseModel):
    role: str = "member"
    is_active: bool = True


class UserOrganizationCreate(UserOrganizationBase):
    user_id: UUID
    organization_id: UUID


class UserOrganizationUpdate(UserOrganizationBase):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserOrganization(UserOrganizationBase):
    id: UUID
    user_id: UUID
    organization_id: UUID
    joined_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationWithMembers(Organization):
    members: List[UserOrganization] = Field(default_factory=list)

    class Config:
        from_attributes = True


class OrganizationInvite(BaseModel):
    email: str
    role: str = "member"
    organization_id: UUID
