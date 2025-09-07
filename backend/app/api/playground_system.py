"""
System prompt management endpoints for playground sessions.

Provides GET/PUT/DELETE operations for managing pinned system prompts
that are stored as chat_messages with role='system'.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.deps import get_current_user, CurrentUser
from ..services.system_prompt_svc import SystemPromptService
from ..errors.openai_envelope import (
    invalid_request_error,
    not_found_error,
    openai_error
)

router = APIRouter()

# Request/Response models
class SystemPromptContent(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000, description="System prompt content")

class SystemPromptResponse(BaseModel):
    content: Optional[str] = Field(None, description="System prompt content or null if none set")

class SystemPromptUpdateResponse(BaseModel):
    content: str = Field(..., description="Updated system prompt content")
    updated_at: datetime = Field(..., description="Timestamp when the system prompt was updated")

class SystemPromptDeleteResponse(BaseModel):
    deleted: bool = Field(True, description="Confirmation that system prompt was deleted")


@router.get("/sessions/{session_id}/system", response_model=SystemPromptResponse)
async def get_system_prompt(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get the pinned system prompt for a session.
    
    Returns the content of the most recent system message for this session,
    or null if no system prompt is set.
    """
    try:
        service = SystemPromptService(current_user.jwt_token)
        content = service.get(session_id)
        return SystemPromptResponse(content=content)
    except Exception as e:
        raise openai_error("server_error", f"Failed to retrieve system prompt: {str(e)}", 500)


@router.put("/sessions/{session_id}/system", response_model=SystemPromptUpdateResponse)
async def set_system_prompt(
    session_id: UUID,
    request: SystemPromptContent,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Set or update the pinned system prompt for a session.
    
    Upserts a system message for this session. Only one system prompt
    is maintained per session (previous ones are replaced).
    """
    # Validate content length
    if len(request.content.strip()) == 0:
        raise invalid_request_error("System prompt content cannot be empty")
    
    if len(request.content) > 32000:
        raise invalid_request_error("System prompt content exceeds maximum length of 32,000 characters")
    
    try:
        service = SystemPromptService(current_user.jwt_token)
        updated_at = service.upsert(session_id, request.content.strip())
        return SystemPromptUpdateResponse(
            content=request.content.strip(),
            updated_at=updated_at
        )
    except Exception as e:
        raise openai_error("server_error", f"Failed to update system prompt: {str(e)}", 500)


@router.delete("/sessions/{session_id}/system", response_model=SystemPromptDeleteResponse)
async def delete_system_prompt(
    session_id: UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Delete the pinned system prompt for a session.
    
    Removes all system messages for this session.
    """
    try:
        service = SystemPromptService(current_user.jwt_token)
        service.delete(session_id)
        return SystemPromptDeleteResponse(deleted=True)
    except Exception as e:
        raise openai_error("server_error", f"Failed to delete system prompt: {str(e)}", 500)
