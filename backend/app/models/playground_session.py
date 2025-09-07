"""
Pydantic models for playground session management.
Supports session lifecycle: create → manage → archive → restore → duplicate → clear
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal, List
from uuid import UUID
from pydantic import BaseModel, Field


class PlaygroundSessionCreate(BaseModel):
    """Request model for creating a new playground session."""
    title: Optional[str] = Field(None, description="Session title (auto-generated if not provided)")
    provider: str = Field(..., description="AI provider name (openai, anthropic)")
    model: str = Field(..., description="Model ID in provider/model format (e.g., openai/gpt-4o-mini)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session metadata")


class PlaygroundSessionUpdate(BaseModel):
    """Request model for updating an existing playground session."""
    title: Optional[str] = Field(None, description="Updated session title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated session metadata (partial merge)")
    
    # Allow direct provider/model updates for picker convenience
    provider: Optional[str] = Field(None, description="Updated provider (will be stored in metadata)")
    model: Optional[str] = Field(None, description="Updated model in provider/model format (will be stored in metadata)")
    default_params: Optional[Dict[str, Any]] = Field(None, description="Updated default parameters (will be stored in metadata)")


class PlaygroundSessionRead(BaseModel):
    """Response model for playground session data."""
    id: UUID = Field(..., description="Session identifier")
    title: str = Field(..., description="Session title")
    provider: str = Field(..., description="AI provider name")
    model: str = Field(..., description="Model ID in provider/model format")
    is_archived: bool = Field(default=False, description="Whether session is archived")
    message_count: int = Field(default=0, description="Number of messages in session")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class PlaygroundSessionList(BaseModel):
    """Response model for paginated session listing."""
    sessions: List[PlaygroundSessionRead] = Field(..., description="List of sessions")
    total_count: int = Field(..., description="Total number of sessions")
    has_more: bool = Field(..., description="Whether more sessions are available")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")


class PlaygroundSessionArchive(BaseModel):
    """Response model for archive/restore operations."""
    id: UUID = Field(..., description="Session identifier")
    is_archived: bool = Field(..., description="New archive status")
    message: str = Field(..., description="Operation result message")


class PlaygroundSessionDuplicate(BaseModel):
    """Response model for session duplication."""
    original_id: UUID = Field(..., description="Original session identifier")
    new_session: PlaygroundSessionRead = Field(..., description="Newly created session")
    messages_copied: int = Field(..., description="Number of messages copied")


class PlaygroundSessionClear(BaseModel):
    """Response model for session clearing."""
    id: UUID = Field(..., description="Session identifier")
    messages_deleted: int = Field(..., description="Number of messages deleted")
    usage_records_deleted: int = Field(..., description="Number of token usage records deleted")
    message: str = Field(..., description="Operation result message")


class MessageDraft(BaseModel):
    """Draft message for batch insertion with indexing."""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message metadata")


def _default_params():
    """Default model parameters factory function."""
    return {"temperature": 0.7, "max_tokens": 512}


class SessionMetadata(BaseModel):
    """Structured session metadata with server-controlled defaults."""
    request_source: Literal["gateway", "direct"] = Field(default="gateway", description="Request routing mode")
    default_params: Dict[str, Any] = Field(
        default_factory=_default_params,
        description="Default model parameters"
    )
    system_prompt: Optional[str] = Field(None, description="Pinned system message for session")
    client_session_id: Optional[str] = Field(None, description="Frontend reconciliation ID")
    
    class Config:
        extra = "allow"  # Allow additional metadata fields
