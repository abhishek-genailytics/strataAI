from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the API key")
    key_prefix: Optional[str] = None
    is_active: bool = True


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_id: UUID
    api_key_value: str = Field(..., min_length=10, description="The actual API key value")
    
    @validator('api_key_value')
    def validate_api_key_format(cls, v):
        """Basic validation for API key format."""
        if not v or len(v.strip()) < 10:
            raise ValueError('API key must be at least 10 characters long')
        return v.strip()


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class APIKey(APIKeyBase):
    id: UUID
    organization_id: UUID
    provider_id: UUID
    encrypted_key_value: str
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithProvider(APIKey):
    provider_name: str
    provider_display_name: str


class APIKeyDisplay(BaseModel):
    """API key model for display purposes with masked key."""
    id: UUID
    name: str
    provider_name: str
    provider_display_name: str
    key_prefix: Optional[str] = None
    masked_key: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyValidationResult(BaseModel):
    """Result of API key validation."""
    is_valid: bool
    provider_name: str
    error_message: Optional[str] = None
    key_info: Optional[dict] = None
