from datetime import datetime, timezone
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID
from app.core.supabase import get_supabase_service
from app.core.exceptions import AuthenticationError, PermissionError_
from app.models.auth import CurrentCaller
from app.utils.crypto import sha256_hex, token_prefix as get_prefix

security = HTTPBearer(auto_error=False)

def _parse_bearer(auth_header: Optional[str]) -> str:
    """Parse Bearer token from Authorization header."""
    if not auth_header:
        raise AuthenticationError("Missing Authorization header", code="missing_authorization")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AuthenticationError("Invalid Authorization header format", code="invalid_authorization")
    return parts[1].strip()

async def require_pat(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> CurrentCaller:
    """
    Dependency to require PAT authentication for /v1/* endpoints.
    
    Returns CurrentCaller with user_id, organization_id, and token metadata.
    Raises AuthenticationError for missing/invalid/expired tokens.
    """
    # Check for missing Authorization header
    if not authorization:
        raise AuthenticationError("Missing Authorization header", code="missing_authorization")
    
    # Check for malformed Authorization header (HTTPBearer returns None for invalid format)
    if not credentials:
        raise AuthenticationError("Invalid Authorization header format", code="invalid_authorization")
    
    raw = credentials.credentials
    prefix = get_prefix(raw)
    token_hash = sha256_hex(raw)

    sb = get_supabase_service()
    if not sb:
        raise AuthenticationError("Authentication service unavailable", code="service_unavailable")

    # 1) Lookup by hash directly (more reliable than prefix matching)
    resp = sb.table("personal_access_tokens")\
        .select("id,user_id,organization_id,token_prefix,token_hash,scopes,expires_at,is_active")\
        .eq("token_hash", token_hash)\
        .eq("is_active", True)\
        .limit(1)\
        .execute()
    rows = resp.data or []

    match = rows[0] if rows else None
    if not match:
        raise AuthenticationError("Invalid API token", code="invalid_token")

    # 2) Expiry check
    expires_at = match.get("expires_at")
    if expires_at is not None:
        # Supabase returns ISO8601 strings; compare in UTC
        expires_dt = datetime.fromisoformat(expires_at.replace("Z", "")).replace(tzinfo=timezone.utc)
        if expires_dt < datetime.now(timezone.utc):
            raise AuthenticationError("Token expired", code="token_expired")

    # 3) Build caller and attach to state in a dependency consumer
    caller = CurrentCaller(
        user_id=UUID(match["user_id"]),
        organization_id=UUID(match["organization_id"]),
        token_id=UUID(match["id"]),
        token_prefix=match["token_prefix"],
        scopes=match.get("scopes") or [],
    )

    # 4) Optional: update last_used_at (best-effort, non-blocking)
    try:
        sb.table("personal_access_tokens")\
          .update({"last_used_at": datetime.now(timezone.utc).isoformat()})\
          .eq("id", str(caller.token_id))\
          .execute()
    except Exception:
        pass

    return caller
