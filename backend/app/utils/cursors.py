"""
Cursor helpers for URL-safe base64 encoding/decoding of pagination cursors.

Cursor payload schema:
{
  "ca": "<ISO timestamp>",
  "id": "<uuid>"
}
"""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Tuple
from uuid import UUID


def encode_cursor(created_at: datetime, id: UUID) -> str:
    """Encode a cursor as URL-safe base64 JSON.

    Args:
        created_at: Message created_at timestamp
        id: Message UUID

    Returns:
        URL-safe base64-encoded JSON string
    """
    payload = {"ca": created_at.isoformat(), "id": str(id)}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(s: str) -> Tuple[datetime, UUID]:
    """Decode a cursor from URL-safe base64 JSON.

    Args:
        s: Encoded cursor string

    Returns:
        Tuple of (created_at, id)
    """
    # Add padding back if removed
    padding = "=" * (-len(s) % 4)
    raw = base64.urlsafe_b64decode((s + padding).encode("utf-8"))
    obj = json.loads(raw.decode("utf-8"))
    ca = obj.get("ca")
    id_str = obj.get("id")
    if not ca or not id_str:
        raise ValueError("Invalid cursor payload")
    # Support both Z-suffixed and offset timestamps
    ca_dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
    return ca_dt, UUID(id_str)

