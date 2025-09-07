from typing import Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.core.supabase import get_supabase_service
from app.models.openai_chat import ChatMessage, ChatCompletionUsage
from app.services.costing import CostBreakdown

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def ensure_session(
    *,
    organization_id: UUID,
    user_id: UUID,
    client_session_id: Optional[str],
    default_title: str = "Playground session",
) -> UUID:
    """
    Find or create a chat_session for this org+user+client_session_id.
    Stores client id in chat_sessions.metadata.client_session_id.
    """
    sb = get_supabase_service()

    if client_session_id:
        existing = sb.table("chat_sessions")\
            .select("id,metadata")\
            .eq("organization_id", str(organization_id))\
            .eq("user_id", str(user_id))\
            .contains("metadata", {"client_session_id": client_session_id})\
            .eq("is_active", True)\
            .limit(1).execute().data
        if existing:
            return UUID(existing[0]["id"])

    # create new
    meta = {"client_session_id": client_session_id} if client_session_id else {}
    row = sb.table("chat_sessions").insert({
        "organization_id": str(organization_id),
        "user_id": str(user_id),
        "title": default_title,
        "is_active": True,
        "metadata": meta,
    }).execute().data[0]
    return UUID(row["id"])

def _next_message_index(sb, session_id: UUID) -> int:
    r = sb.table("chat_messages")\
        .select("id", count="exact")\
        .eq("session_id", str(session_id))\
        .execute()
    # Supabase returns count separately; fallback to 0 if not present
    return int(getattr(r, "count", 0) or 0)

def append_turn(
    *,
    session_id: UUID,
    provider_id: UUID,
    model_id: UUID,
    last_user_message: ChatMessage,
    assistant_text: str,
    usage: ChatCompletionUsage,
    cost: Optional[CostBreakdown],
) -> Tuple[UUID, UUID]:
    """
    Appends user and assistant messages, then writes token_usage for assistant.
    Returns (user_msg_id, assistant_msg_id).
    """
    sb = get_supabase_service()
    base_idx = _next_message_index(sb, session_id)

    # 1) user message
    urow = sb.table("chat_messages").insert({
        "session_id": str(session_id),
        "role": "user",
        "content": last_user_message.content,
        "message_index": base_idx,
        "provider_id": str(provider_id),
        "model_id": str(model_id),
    }).execute().data[0]
    user_msg_id = UUID(urow["id"])

    # 2) assistant message
    arow = sb.table("chat_messages").insert({
        "session_id": str(session_id),
        "role": "assistant",
        "content": assistant_text,
        "message_index": base_idx + 1,
        "provider_id": str(provider_id),
        "model_id": str(model_id),
    }).execute().data[0]
    assistant_msg_id = UUID(arow["id"])

    # 3) token_usage (per assistant turn)
    sb.table("token_usage").insert({
        "message_id": str(assistant_msg_id),
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "currency": getattr(cost, "currency", "USD") if cost else "USD",
        "total_cost": str(getattr(cost, "total_cost", 0)) if cost else "0",
        "metadata": {},
    }).execute()

    return user_msg_id, assistant_msg_id
