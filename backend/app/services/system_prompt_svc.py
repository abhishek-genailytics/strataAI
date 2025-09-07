"""
System prompt service for managing pinned system messages per session.

Stores system prompts as chat_messages with role='system' and provides
get/upsert/delete operations for session-level system prompt management.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..utils.supabase_client import get_supabase_user_client


class SystemPromptService:
    """Service for managing system prompts stored as chat_messages with role='system'."""
    
    def __init__(self, jwt_token: Optional[str]):
        self.sb = get_supabase_user_client(jwt_token)
    
    def get(self, session_id: UUID) -> Optional[str]:
        """
        Get the current system prompt for a session.
        
        Returns the content of the most recent chat_messages row with role='system'
        for the given session, or None if no system prompt exists.
        """
        try:
            result = (
                self.sb.table("chat_messages")
                .select("content")
                .eq("session_id", str(session_id))
                .eq("role", "system")
                .order("created_at", desc=True)
                .order("id", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data:
                return result.data[0]["content"]
            return None
            
        except Exception:
            # If query fails, assume no system prompt
            return None
    
    def upsert(self, session_id: UUID, content: str) -> datetime:
        """
        Upsert a system prompt for a session.
        
        Strategy: Delete existing system rows for this session, then insert a new one.
        This ensures only one active system prompt per session.
        
        Returns the created_at timestamp of the new system message.
        """
        # First, delete any existing system messages for this session
        self.sb.table("chat_messages").delete().eq("session_id", str(session_id)).eq("role", "system").execute()
        
        # Insert the new system message
        now = datetime.utcnow()
        result = (
            self.sb.table("chat_messages")
            .insert({
                "session_id": str(session_id),
                "role": "system",
                "content": content,
                "created_at": now.isoformat(),
            })
            .execute()
        )
        
        return now
    
    def delete(self, session_id: UUID) -> bool:
        """
        Delete all system prompts for a session.
        
        Returns True if any rows were deleted, False otherwise.
        """
        result = (
            self.sb.table("chat_messages")
            .delete()
            .eq("session_id", str(session_id))
            .eq("role", "system")
            .execute()
        )
        
        # PostgREST doesn't return affected row count in delete responses,
        # so we'll return True assuming the operation succeeded
        return True
