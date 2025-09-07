"""
Playground messages listing service with cursor-based pagination.

Ordering is deterministic by (created_at ASC, id ASC).
Supports forward/backward pages, since polling, and around-window fetches.
"""
from __future__ import annotations

from datetime import datetime
from math import floor
from typing import List, Optional, Tuple
from uuid import UUID

from app.models.playground_message import (
    PlaygroundMessageRead,
    PlaygroundTokenUsage,
    MessagesPage,
    PageInfo,
)
from app.utils.cursors import encode_cursor, decode_cursor
from app.utils.supabase_client import get_supabase_user_client


def _postgrest_tuple_gt_filters(ca: datetime, id: UUID) -> str:
    """Return PostgREST OR filter for (created_at,id) > (ca,id)."""
    ca_iso = ca.isoformat()
    return f"and(created_at.gt.{ca_iso}),and(created_at.eq.{ca_iso},id.gt.{id})"


def _postgrest_tuple_lt_filters(ca: datetime, id: UUID) -> str:
    """Return PostgREST OR filter for (created_at,id) < (ca,id)."""
    ca_iso = ca.isoformat()
    return f"and(created_at.lt.{ca_iso}),and(created_at.eq.{ca_iso},id.lt.{id})"


class PlaygroundMessagesService:
    def __init__(self, jwt_token: Optional[str]):
        self.sb = get_supabase_user_client(jwt_token)  # RLS-scoped (currently service client under the hood)

    def _row_to_message(self, row: dict, usage_map: Optional[dict] = None) -> PlaygroundMessageRead:
        usage_obj = None
        if usage_map is not None:
            tu = usage_map.get(row["id"]) if row.get("id") else None
            if tu:
                usage_obj = PlaygroundTokenUsage(
                    input_tokens=int(tu.get("input_tokens", tu.get("prompt_tokens", 0) or 0)),
                    output_tokens=int(tu.get("output_tokens", tu.get("completion_tokens", 0) or 0)),
                    total_tokens=int(tu.get("total_tokens", 0)),
                )
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return PlaygroundMessageRead(
            id=UUID(row["id"]),
            role=row["role"],
            content=row["content"],
            created_at=created_at,
            usage=usage_obj,
        )

    def _fetch_usage_map(self, message_ids: List[str]) -> dict:
        if not message_ids:
            return {}
        r = self.sb.table("token_usage").select(
            "message_id,input_tokens,output_tokens,total_tokens,prompt_tokens,completion_tokens"
        ).in_("message_id", message_ids).execute()
        rows = r.data or []
        return {row["message_id"]: row for row in rows}

    def _verify_session_access(self, session_id: UUID, user_id: UUID) -> bool:
        # Ensure the session exists and belongs to the caller
        s = self.sb.table("chat_sessions").select("id,user_id").eq("id", str(session_id)).limit(1).execute()
        if not s.data:
            return False
        return s.data[0].get("user_id") == str(user_id)

    def _get_anchor_from_id(self, session_id: UUID, message_id: UUID) -> Optional[Tuple[datetime, UUID]]:
        r = self.sb.table("chat_messages").select("id,created_at,session_id").eq("id", str(message_id)).limit(1).execute()
        if not r.data:
            return None
        row = r.data[0]
        if row.get("session_id") != str(session_id):
            return None
        ca = row["created_at"]
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca.replace("Z", "+00:00"))
        return ca, UUID(row["id"])

    def _has_any_before(self, session_id: UUID, first_ca: datetime, first_id: UUID) -> bool:
        q = self.sb.table("chat_messages").select("id").eq("session_id", str(session_id))
        q = q.or_(_postgrest_tuple_lt_filters(first_ca, first_id)).order("created_at", desc=False).order("id", desc=False).limit(1)
        r = q.execute()
        return bool(r.data)

    def _has_any_after(self, session_id: UUID, last_ca: datetime, last_id: UUID) -> bool:
        q = self.sb.table("chat_messages").select("id").eq("session_id", str(session_id))
        q = q.or_(_postgrest_tuple_gt_filters(last_ca, last_id)).order("created_at", desc=True).order("id", desc=True).limit(1)
        r = q.execute()
        return bool(r.data)

    def _base_select(self):
        return self.sb.table("chat_messages").select("id,session_id,role,content,created_at")

    def list_messages(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
        limit: int = 50,
        cursor: Optional[str] = None,
        direction: str = "forward",
        since: Optional[datetime] = None,
        around: Optional[UUID] = None,
        include_usage: bool = True,
    ) -> MessagesPage:
        # Verify access early for better UX (RLS would also enforce)
        if not self._verify_session_access(session_id, user_id):
            from app.errors.openai_envelope import session_not_found_error
            session_not_found_error(str(session_id))

        if limit < 1:
            limit = 1
        if limit > 200:
            limit = 200

        if cursor and since:
            from app.errors.openai_envelope import openai_error
            openai_error(400, "Provide only one of 'cursor' or 'since'", code="invalid_pagination_params")
        if around and (cursor or since):
            from app.errors.openai_envelope import openai_error
            openai_error(400, "'around' cannot be combined with 'cursor' or 'since'", code="invalid_pagination_params")

        usage_map: Optional[dict] = None
        messages: List[PlaygroundMessageRead] = []
        has_next = False
        has_prev = False
        next_cursor: Optional[str] = None
        prev_cursor: Optional[str] = None

        # A) Around-window fetch
        if around:
            anchor = self._get_anchor_from_id(session_id, around)
            if not anchor:
                from app.errors.openai_envelope import openai_error
                openai_error(404, "Anchor message not found in session", code="message_not_found")
            anchor_ca, anchor_id = anchor

            back_count = floor(limit / 2)
            fwd_count = limit - back_count

            # Backward slice (< anchor)
            qb = self._base_select().eq("session_id", str(session_id))
            qb = qb.or_(_postgrest_tuple_lt_filters(anchor_ca, anchor_id)).order("created_at", desc=True).order("id", desc=True).limit(back_count)
            back_rows = qb.execute().data or []

            # Forward slice (>= anchor)
            qf = self._base_select().eq("session_id", str(session_id))
            # include anchor in the forward slice
            qf = qf.or_(f"and(created_at.gt.{anchor_ca.isoformat()}),and(created_at.eq.{anchor_ca.isoformat()},id.gte.{anchor_id})")
            qf = qf.order("created_at", desc=False).order("id", desc=False).limit(fwd_count + 1)  # +1 to check has_next
            fwd_rows = qf.execute().data or []

            # Compose in ascending order
            back_rows.reverse()
            rows = back_rows + fwd_rows[:fwd_count]

            # Compute has_prev/has_next using extra checks
            if rows:
                first = rows[0]
                last = rows[-1]
                first_ca = datetime.fromisoformat(first["created_at"].replace("Z", "+00:00")) if isinstance(first["created_at"], str) else first["created_at"]
                last_ca = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00")) if isinstance(last["created_at"], str) else last["created_at"]
                has_prev = self._has_any_before(session_id, first_ca, UUID(first["id"]))
                # We already fetched one extra forward row
                has_next = len(fwd_rows) > fwd_count
                next_cursor = encode_cursor(last_ca, UUID(last["id"])) if has_next else None
                prev_cursor = encode_cursor(first_ca, UUID(first["id"])) if has_prev else None
            else:
                rows = []
                has_prev = False
                has_next = False

        # B) Cursor-based fetch
        else:
            q = self._base_select().eq("session_id", str(session_id))

            if since:
                q = q.gt("created_at", since.isoformat())

            if cursor:
                ca, cid = decode_cursor(cursor)
                if direction == "backward":
                    q = q.or_(_postgrest_tuple_lt_filters(ca, cid)).order("created_at", desc=True).order("id", desc=True).limit(limit + 1)
                else:
                    q = q.or_(_postgrest_tuple_gt_filters(ca, cid)).order("created_at", desc=False).order("id", desc=False).limit(limit + 1)
            else:
                # First page
                if direction == "backward":
                    # Start from the end
                    q = q.order("created_at", desc=True).order("id", desc=True).limit(limit + 1)
                else:
                    q = q.order("created_at", desc=False).order("id", desc=False).limit(limit + 1)

            rows = q.execute().data or []

            # Normalize orientation to ascending for response
            reverse_result = False
            if direction == "backward":
                reverse_result = True
                # We fetched DESC; keep one extra for has_prev in that direction
                has_prev = len(rows) > limit
                if has_prev:
                    rows = rows[:limit]
                rows.reverse()
            else:
                has_next = len(rows) > limit
                if has_next:
                    rows = rows[:limit]

            # Compute prev/next cursors by probing the ends
            if rows:
                first = rows[0]
                last = rows[-1]
                first_ca = datetime.fromisoformat(first["created_at"].replace("Z", "+00:00")) if isinstance(first["created_at"], str) else first["created_at"]
                last_ca = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00")) if isinstance(last["created_at"], str) else last["created_at"]
                # Quick extra check for the other side
                if direction == "backward":
                    # After reversing, rows are ASC. Determine has_next by probing after 'last'
                    has_next = self._has_any_after(session_id, last_ca, UUID(last["id"]))
                else:
                    # We already determined has_next via limit+1; check has_prev via probe
                    has_prev = self._has_any_before(session_id, first_ca, UUID(first["id"])) if cursor or since else False
                next_cursor = encode_cursor(last_ca, UUID(last["id"])) if has_next else None
                prev_cursor = encode_cursor(first_ca, UUID(first["id"])) if has_prev else None

        # Map usage if requested
        if include_usage and rows:
            usage_map = self._fetch_usage_map([r["id"] for r in rows])

        # Build response data
        messages = [self._row_to_message(r, usage_map) for r in rows]

        page = PageInfo(
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=bool(has_next),
            has_prev=bool(has_prev),
        )

        return MessagesPage(
            data=messages,
            page=page,
            meta={"session_id": str(session_id), "count": len(messages)},
        )

