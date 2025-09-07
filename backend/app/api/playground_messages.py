"""
Playground messages API: paginated fetch with cursors.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, get_current_user, get_organization_context
from app.models.playground_message import MessagesPage
from app.services.playground_messages_svc import PlaygroundMessagesService
from app.errors.openai_envelope import openai_error


router = APIRouter(prefix="/playground/sessions", tags=["Playground Sessions"])


@router.get("/{session_id}/messages", response_model=MessagesPage)
def get_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    cursor: Optional[str] = Query(None, description="Opaque cursor (URL-safe base64 JSON)"),
    direction: str = Query("forward", regex="^(forward|backward)$", description="Page direction"),
    since: Optional[datetime] = Query(None, description="Return messages created after this timestamp"),
    around: Optional[UUID] = Query(None, description="Center window around this message ID"),
    include_usage: bool = Query(True, description="Include per-message token usage"),
    current_user: CurrentUser = Depends(get_current_user),
    organization_id: UUID = Depends(get_organization_context),
) -> MessagesPage:
    try:
        svc = PlaygroundMessagesService(jwt_token=current_user.jwt_token)

        return svc.list_messages(
            session_id=session_id,
            user_id=current_user.id,
            limit=limit,
            cursor=cursor,
            direction=direction,
            since=since,
            around=around,
            include_usage=include_usage,
        )
    except Exception as e:
        # Convert to OpenAI envelope if not already
        if hasattr(e, "status_code"):
            raise
        openai_error(500, f"Failed to fetch messages: {str(e)}", code="messages_fetch_failed")

