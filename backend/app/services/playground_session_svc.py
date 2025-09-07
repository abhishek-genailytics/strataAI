"""
Playground session service for Supabase orchestration.
Handles CRUD operations, archiving, duplication, and clearing.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from ..utils.supabase_client import supabase_service
from ..models.playground_session import (
    PlaygroundSessionCreate,
    PlaygroundSessionUpdate,
    PlaygroundSessionRead,
    PlaygroundSessionList,
    PlaygroundSessionArchive,
    PlaygroundSessionDuplicate,
    PlaygroundSessionClear,
    SessionMetadata
)
from .message_indexer import (
    get_message_count,
    clear_session_messages,
    copy_session_messages
)
from ..services.key_preflight import get_provider_status


class PlaygroundSessionService:
    """Service for managing playground sessions."""
    
    def __init__(self):
        self.sb = supabase_service
    
    async def create_session(
        self,
        user_id: UUID,
        organization_id: UUID,
        data: PlaygroundSessionCreate
    ) -> PlaygroundSessionRead:
        """Create a new playground session with defaults."""
        
        # Prepare metadata with server-controlled defaults
        metadata = {
            "request_source": "gateway",
            "default_params": {"temperature": 0.7, "max_tokens": 512}
        }
        
        # Merge user-provided metadata
        if data.metadata:
            metadata.update(data.metadata)
        
        # Auto-generate title if not provided
        title = data.title or f"New {data.provider.title()} Chat"
        
        # Create session record
        session_data = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "title": title,
            "provider": data.provider,
            "model": data.model,
            "is_archived": False,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = self.sb.table("chat_sessions").insert(session_data).execute()
        
        if not result.data:
            raise Exception("Failed to create session")
        
        session_record = result.data[0]
        
        return PlaygroundSessionRead(
            id=UUID(session_record["id"]),
            title=session_record["title"],
            provider=session_record["provider"],
            model=session_record["model"],
            is_archived=session_record.get("is_archived", False),
            message_count=0,
            created_at=datetime.fromisoformat(session_record["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(session_record["updated_at"].replace('Z', '+00:00')),
            metadata=session_record.get("metadata", {})
        )
    
    async def get_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[PlaygroundSessionRead]:
        """Get a single session by ID."""
        
        result = self.sb.table("chat_sessions").select(
            "id, title, provider, model, is_archived, created_at, updated_at, metadata"
        ).eq("id", str(session_id)).eq(
            "user_id", str(user_id)
        ).eq("organization_id", str(organization_id)).execute()
        
        if not result.data:
            return None
        
        session = result.data[0]
        message_count = await get_message_count(session_id)
        
        return PlaygroundSessionRead(
            id=UUID(session["id"]),
            title=session["title"],
            provider=session["provider"],
            model=session["model"],
            is_archived=session.get("is_archived", False),
            message_count=message_count,
            created_at=datetime.fromisoformat(session["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00')),
            metadata=session.get("metadata", {})
        )
    
    async def list_sessions(
        self,
        user_id: UUID,
        organization_id: UUID,
        archived: str = "false",
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> PlaygroundSessionList:
        """List sessions with pagination."""
        
        # Build base query
        query = self.sb.table("chat_sessions").select(
            "id, title, provider, model, is_archived, created_at, updated_at, metadata"
        ).eq("user_id", str(user_id)).eq("organization_id", str(organization_id))
        
        # Apply archive filter
        if archived == "true":
            query = query.eq("is_archived", True)
        elif archived == "false":
            query = query.eq("is_archived", False)
        # "all" shows both archived and non-archived
        
        # Apply cursor pagination
        if cursor:
            cursor_result = self.sb.table("chat_sessions").select(
                "updated_at"
            ).eq("id", cursor).eq("user_id", str(user_id)).eq(
                "organization_id", str(organization_id)
            ).execute()
            
            if cursor_result.data:
                cursor_timestamp = cursor_result.data[0]["updated_at"]
                query = query.lt("updated_at", cursor_timestamp)
        
        # Execute with limit + 1 to check for more results
        query = query.order("updated_at", desc=True).limit(limit + 1)
        result = query.execute()
        
        sessions_data = result.data or []
        has_more = len(sessions_data) > limit
        
        # Remove extra record if present
        if has_more:
            sessions_data = sessions_data[:limit]
        
        # Convert to response models
        sessions = []
        for session in sessions_data:
            message_count = await get_message_count(UUID(session["id"]))
            
            sessions.append(PlaygroundSessionRead(
                id=UUID(session["id"]),
                title=session["title"] or "Untitled Session",
                provider=session["provider"] or "unknown",
                model=session["model"] or "unknown/model",
                is_archived=session.get("is_archived", False),
                message_count=message_count,
                created_at=datetime.fromisoformat(session["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(session["updated_at"].replace('Z', '+00:00')),
                metadata=session.get("metadata", {})
            ))
        
        # Get total count for metadata
        count_query = self.sb.table("chat_sessions").select(
            "id", count="exact"
        ).eq("user_id", str(user_id)).eq("organization_id", str(organization_id))
        
        if archived == "true":
            count_query = count_query.eq("is_archived", True)
        elif archived == "false":
            count_query = count_query.eq("is_archived", False)
        
        count_result = count_query.execute()
        total_count = count_result.count or 0
        
        next_cursor = sessions[-1].id if has_more and sessions else None
        
        return PlaygroundSessionList(
            sessions=sessions,
            total_count=total_count,
            has_more=has_more,
            next_cursor=str(next_cursor) if next_cursor else None
        )
    
    async def update_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        data: PlaygroundSessionUpdate
    ) -> Optional[PlaygroundSessionRead]:
        """Update session title and/or metadata."""
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if data.title is not None:
            update_data["title"] = data.title
        
        if data.metadata is not None:
            # Get current metadata for partial merge
            current_result = self.sb.table("chat_sessions").select(
                "metadata"
            ).eq("id", str(session_id)).eq("user_id", str(user_id)).eq(
                "organization_id", str(organization_id)
            ).execute()
            
            if not current_result.data:
                return None
            
            current_metadata = current_result.data[0].get("metadata", {})
            
            # Merge metadata (preserve system fields, allow user fields)
            system_fields = ["request_source", "default_params"]
            
            # Merge all user-provided metadata
            for key, value in data.metadata.items():
                current_metadata[key] = value
            
            update_data["metadata"] = current_metadata
        
        # Execute update
        result = self.sb.table("chat_sessions").update(update_data).eq(
            "id", str(session_id)
        ).eq("user_id", str(user_id)).eq(
            "organization_id", str(organization_id)
        ).execute()
        
        if not result.data:
            return None
        
        # Return updated session
        return await self.get_session(session_id, user_id, organization_id)
    
    async def archive_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[PlaygroundSessionArchive]:
        """Archive a session (soft delete)."""
        
        result = self.sb.table("chat_sessions").update({
            "is_archived": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(session_id)).eq("user_id", str(user_id)).eq(
            "organization_id", str(organization_id)
        ).execute()
        
        if not result.data:
            return None
        
        return PlaygroundSessionArchive(
            id=session_id,
            is_archived=True,
            message="Session archived successfully"
        )
    
    async def restore_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[PlaygroundSessionArchive]:
        """Restore an archived session."""
        
        result = self.sb.table("chat_sessions").update({
            "is_archived": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(session_id)).eq("user_id", str(user_id)).eq(
            "organization_id", str(organization_id)
        ).execute()
        
        if not result.data:
            return None
        
        return PlaygroundSessionArchive(
            id=session_id,
            is_archived=False,
            message="Session restored successfully"
        )
    
    async def duplicate_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[PlaygroundSessionDuplicate]:
        """Duplicate a session with all messages (no usage records)."""
        
        # Get original session
        original_session = await self.get_session(session_id, user_id, organization_id)
        if not original_session:
            return None
        
        # Create new session with copied data
        new_title = f"{original_session.title} (copy)"
        
        create_data = PlaygroundSessionCreate(
            title=new_title,
            provider=original_session.provider,
            model=original_session.model,
            metadata=original_session.metadata
        )
        
        new_session = await self.create_session(user_id, organization_id, create_data)
        
        # Copy messages
        messages_copied = await copy_session_messages(session_id, new_session.id)
        
        return PlaygroundSessionDuplicate(
            original_id=session_id,
            new_session=new_session,
            messages_copied=messages_copied
        )
    
    async def clear_session(
        self,
        session_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> Optional[PlaygroundSessionClear]:
        """Clear all messages from a session (keep session metadata)."""
        
        # Verify session ownership
        session = await self.get_session(session_id, user_id, organization_id)
        if not session:
            return None
        
        # Clear messages and usage records
        deletion_result = await clear_session_messages(session_id)
        
        # Update session timestamp
        self.sb.table("chat_sessions").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(session_id)).execute()
        
        return PlaygroundSessionClear(
            id=session_id,
            messages_deleted=deletion_result["messages_deleted"],
            usage_records_deleted=deletion_result["usage_records_deleted"],
            message="Session cleared successfully"
        )
    
    async def get_preflight_warning(
        self,
        organization_id: UUID,
        provider: str,
        jwt_token: str
    ) -> Optional[Dict[str, Any]]:
        """Get preflight warning for provider key status."""
        
        try:
            status = await get_provider_status(organization_id, provider, jwt_token)
            
            if not status.get("has_org_api_key") or not status.get("is_active"):
                return {
                    "warning": f"No active API key configured for {provider}",
                    "provider": provider,
                    "has_key": status.get("has_org_api_key", False),
                    "is_active": status.get("is_active", False)
                }
            
            return None
            
        except Exception:
            # Don't fail session creation on preflight check errors
            return {
                "warning": f"Could not verify API key status for {provider}",
                "provider": provider
            }
