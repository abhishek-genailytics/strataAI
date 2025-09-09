from typing import Tuple
from uuid import UUID
from app.core.supabase import get_supabase_service
from app.core.exceptions import InvalidRequestError, NotFoundError, PermissionError_
from app.core.encryption import encryption_service

def get_active_api_key(organization_id: UUID, provider_id: UUID) -> Tuple[UUID, str]:
    """
    Returns (api_key_id, plaintext_key) for the active org+provider key.
    Exactly one active key per provider per org is expected by schema.
    """
    sb = get_supabase_service()
    # 1) Fetch candidate keys (active only), prefer most recently updated
    cols = "id,encrypted_key_value,is_active,updated_at"
    data = sb.table("api_keys")\
        .select(cols)\
        .eq("organization_id", str(organization_id))\
        .eq("provider_id", str(provider_id))\
        .eq("is_active", True)\
        .order("updated_at", desc=True)\
        .limit(2)\
        .execute().data or []

    if not data:
        # Config error on the caller side — use 400 invalid_request_error
        # (you asked to treat "no key configured" as a client config issue in MVP)
        raise InvalidRequestError("Provider API key not configured for this organization",
                                  code="provider_key_missing")

    if len(data) > 1:
        # Defensive: schema note says one key per provider per org; duplicates imply admin error
        # Prefer explicit signal so it can be fixed quickly.
        raise PermissionError_("Multiple active keys found for this provider",
                               code="provider_key_ambiguous")

    row = data[0]
    try:
        plaintext = encryption_service.decrypt_api_key(row["encrypted_key_value"])
    except ValueError:
        # The envelope middleware will shape this as server_error on /v1/*
        raise PermissionError_("Provider key decryption failed", code="provider_key_decrypt_failed")

    # 2) Best-effort last_used_at update
    try:
        sb.table("api_keys").update({"last_used_at": "now()"}).eq("id", row["id"]).execute()
    except Exception:
        pass

    return UUID(row["id"]), plaintext
