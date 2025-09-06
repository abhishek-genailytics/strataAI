"""
Authentication models - MVP stubs.
"""
from typing import Optional
from pydantic import BaseModel

class CurrentCaller(BaseModel):
    """Carries user_id, organization_id for authenticated requests"""
    user_id: str
    organization_id: str
    email: Optional[str] = None
