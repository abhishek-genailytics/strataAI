from fastapi import APIRouter, Depends, Path, Query
from uuid import UUID
from typing import Optional, List
from app.core.auth import require_pat
from app.core.deps import resolve_organization
from app.core.exceptions import NotFoundError, PermissionError_, InvalidRequestError
from app.core.supabase import get_supabase_service
from app.models.auth import CurrentCaller
from app.models.playground import PlaygroundSession, MessagesPage, PlaygroundMessage, PlaygroundMessageUsage, PlaygroundMessageCost, SessionMeta, SessionsPage

router = APIRouter(tags=["Playground"])

def _assert_owns_session(sb, session_id: str, organization_id: UUID, user_id: UUID):
    row = sb.table("chat_sessions")\
        .select("id, title, created_at, updated_at, metadata, provider, model")\
        .eq("id", session_id)\
        .eq("organization_id", str(organization_id))\
        .eq("user_id", str(user_id))\
        .eq("is_active", True)\
        .limit(1).execute().data
    if not row:
        # Do not leak existence across tenants/users
        raise NotFoundError("Session not found", code="session_not_found")
    return row[0]

@router.get("/playground/sessions/{session_id}", response_model=PlaygroundSession)
async def get_session(
    session_id: str = Path(..., description="UUID of the chat session"),
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
):
    sb = get_supabase_service()
    row = _assert_owns_session(sb, session_id, organization_id, caller.user_id)

    # count messages
    cnt = sb.table("chat_messages")\
        .select("id", count="exact")\
        .eq("session_id", session_id)\
        .execute()
    message_count = int(getattr(cnt, "count", 0) or 0)

    meta = row.get("metadata") or {}
    return PlaygroundSession(
        id=row["id"],
        title=row.get("title") or "Playground session",
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        message_count=message_count,
        metadata=SessionMeta(client_session_id=meta.get("client_session_id")),
        provider_id=row.get("provider"),
        model_id=row.get("model"),
    )

@router.get("/playground/sessions/{session_id}/messages", response_model=MessagesPage)
async def list_messages(
    session_id: str = Path(...),
    after_index: Optional[int] = Query(None, ge=-1, description="Return messages with index > after_index"),
    limit: int = Query(100, ge=1, le=200),
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
):
    sb = get_supabase_service()
    _ = _assert_owns_session(sb, session_id, organization_id, caller.user_id)

    q = sb.table("chat_messages")\
        .select("id, role, content, message_index, created_at")\
        .eq("session_id", session_id)\
        .order("message_index")

    if after_index is not None:
        q = q.gt("message_index", after_index)

    rows = q.limit(limit + 1).execute().data or []

    # Fetch token usage for assistant messages in this page
    ids = [r["id"] for r in rows[:limit]]
    tu = {}
    if ids:
        tus = sb.table("token_usage")\
            .select("message_id, prompt_tokens, completion_tokens, total_tokens, currency, total_cost")\
            .in_("message_id", ids)\
            .execute().data or []
        for u in tus:
            tu[u["message_id"]] = u

    messages: List[PlaygroundMessage] = []
    for r in rows[:limit]:
        usage = cost = None
        if r["role"] == "assistant" and r["id"] in tu:
            u = tu[r["id"]]
            usage = PlaygroundMessageUsage(
                prompt_tokens=int(u.get("prompt_tokens") or 0),
                completion_tokens=int(u.get("completion_tokens") or 0),
                total_tokens=int(u.get("total_tokens") or 0),
            )
            cost = PlaygroundMessageCost(
                currency=u.get("currency") or "USD",
                total_cost=str(u.get("total_cost") or "0"),
            )
        messages.append(PlaygroundMessage(
            id=r["id"],
            message_index=int(r["message_index"]),
            role=r["role"],
            content=r.get("content") or "",
            created_at=r["created_at"],
            usage=usage,
            cost=cost,
        ))

    next_after_index = None
    if len(rows) > limit:
        next_after_index = int(rows[limit - 1]["message_index"])

    return MessagesPage(session_id=session_id, messages=messages, next_after_index=next_after_index)

@router.get("/playground/sessions", response_model=SessionsPage)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination (session ID)"),
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
):
    """List the caller's recent chat sessions with cursor-based pagination."""
    sb = get_supabase_service()
    
    # Build query with organization and user filtering
    q = sb.table("chat_sessions")\
        .select("id, title, created_at, updated_at, metadata, provider, model")\
        .eq("organization_id", str(organization_id))\
        .eq("user_id", str(caller.user_id))\
        .eq("is_active", True)\
        .order("updated_at", desc=True)
    
    # Apply cursor pagination if provided
    if cursor:
        # Get the cursor session's updated_at timestamp for comparison
        cursor_row = sb.table("chat_sessions")\
            .select("updated_at")\
            .eq("id", cursor)\
            .eq("organization_id", str(organization_id))\
            .eq("user_id", str(caller.user_id))\
            .limit(1).execute().data
        
        if cursor_row:
            cursor_timestamp = cursor_row[0]["updated_at"]
            q = q.lt("updated_at", cursor_timestamp)
    
    # Fetch limit + 1 to determine if there are more results
    rows = q.limit(limit + 1).execute().data or []
    
    # Get message counts for each session
    session_ids = [r["id"] for r in rows[:limit]]
    message_counts = {}
    if session_ids:
        for session_id in session_ids:
            cnt = sb.table("chat_messages")\
                .select("id", count="exact")\
                .eq("session_id", session_id)\
                .execute()
            message_counts[session_id] = int(getattr(cnt, "count", 0) or 0)
    
    # Build session objects
    sessions: List[PlaygroundSession] = []
    for r in rows[:limit]:
        meta = r.get("metadata") or {}
        sessions.append(PlaygroundSession(
            id=r["id"],
            title=r.get("title") or "Playground session",
            created_at=r["created_at"],
            updated_at=r.get("updated_at"),
            message_count=message_counts.get(r["id"], 0),
            metadata=SessionMeta(client_session_id=meta.get("client_session_id")),
            provider_id=r.get("provider"),
            model_id=r.get("model"),
        ))
    
    # Determine next cursor
    next_cursor = None
    if len(rows) > limit:
        next_cursor = rows[limit - 1]["id"]
    
    return SessionsPage(sessions=sessions, next_cursor=next_cursor)

@router.get("/playground/sessions/by-client-id/{client_session_id}", response_model=PlaygroundSession)
async def get_session_by_client_id(
    client_session_id: str = Path(..., description="Client-side session ID from metadata"),
    caller: CurrentCaller = Depends(require_pat),
    organization_id: UUID = Depends(resolve_organization),
):
    """Get a session by client_session_id from metadata (single-row fetch)."""
    sb = get_supabase_service()
    
    # Query using JSONB metadata filter
    rows = sb.table("chat_sessions")\
        .select("id, title, created_at, updated_at, metadata, provider, model")\
        .eq("organization_id", str(organization_id))\
        .eq("user_id", str(caller.user_id))\
        .eq("is_active", True)\
        .contains("metadata", {"client_session_id": client_session_id})\
        .limit(1).execute().data
    
    if not rows:
        raise NotFoundError("Session not found", code="session_not_found")
    
    row = rows[0]
    
    # Get message count
    cnt = sb.table("chat_messages")\
        .select("id", count="exact")\
        .eq("session_id", row["id"])\
        .execute()
    message_count = int(getattr(cnt, "count", 0) or 0)
    
    meta = row.get("metadata") or {}
    return PlaygroundSession(
        id=row["id"],
        title=row.get("title") or "Playground session",
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        message_count=message_count,
        metadata=SessionMeta(client_session_id=meta.get("client_session_id")),
        provider_id=row.get("provider"),
        model_id=row.get("model"),
    )
