"""
Message indexer service for reliable message ordering and conflict retry.
Ensures chronological order for audit logs and analytics.
"""

import asyncio
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..utils.supabase_client import supabase_service
from ..models.playground_session import MessageDraft


class MessageIndexingError(Exception):
    """Raised when message indexing fails after retries."""
    pass


async def next_index(session_id: UUID) -> int:
    """
    Get the next available message index for a session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Next sequential message index (0-based)
    """
    sb = supabase_service
    
    result = sb.table("chat_messages").select(
        "message_index"
    ).eq("session_id", str(session_id)).order(
        "message_index", desc=True
    ).limit(1).execute()
    
    if result.data:
        return result.data[0]["message_index"] + 1
    return 0


async def append_messages(
    session_id: UUID,
    items: List[MessageDraft],
    max_retries: int = 3
) -> List[dict]:
    """
    Append messages to a session with reliable indexing.
    
    Args:
        session_id: Session UUID
        items: List of message drafts to append
        max_retries: Maximum retry attempts on conflict
        
    Returns:
        List of inserted message records
        
    Raises:
        MessageIndexingError: If insertion fails after retries
    """
    if not items:
        return []
    
    sb = supabase_service
    
    for attempt in range(max_retries + 1):
        try:
            # Get starting index
            start_index = await next_index(session_id)
            
            # Prepare batch insert with sequential indices
            insert_data = []
            for i, message in enumerate(items):
                insert_data.append({
                    "id": str(uuid4()),
                    "session_id": str(session_id),
                    "role": message.role,
                    "content": message.content,
                    "message_index": start_index + i,
                    "created_at": datetime.utcnow().isoformat()
                })
                
                # Skip metadata since chat_messages table doesn't have metadata column
                    
            
            # Batch insert
            result = sb.table("chat_messages").insert(insert_data).execute()
            
            if result.data:
                return result.data
            else:
                raise Exception("Insert returned no data")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a unique constraint violation (race condition)
            if "unique" in error_msg or "duplicate" in error_msg:
                if attempt < max_retries:
                    # Wait briefly and retry with new indices
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    raise MessageIndexingError(
                        f"Failed to insert messages after {max_retries} retries due to index conflicts"
                    )
            else:
                # Non-conflict error, don't retry
                raise MessageIndexingError(f"Message insertion failed: {str(e)}")
    
    raise MessageIndexingError("Unexpected error in message indexing")


async def get_message_count(session_id: UUID) -> int:
    """
    Get the total number of messages in a session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Message count
    """
    sb = supabase_service
    
    result = sb.table("chat_messages").select(
        "id", count="exact"
    ).eq("session_id", str(session_id)).execute()
    
    return result.count or 0


async def clear_session_messages(session_id: UUID) -> dict:
    """
    Clear all messages and associated token usage for a session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Dictionary with deletion counts
    """
    sb = supabase_service
    
    # First get message IDs for token usage cleanup
    messages_result = sb.table("chat_messages").select(
        "id"
    ).eq("session_id", str(session_id)).execute()
    
    message_ids = [msg["id"] for msg in messages_result.data] if messages_result.data else []
    
    # Delete token usage records for these messages
    usage_deleted = 0
    if message_ids:
        usage_result = sb.table("token_usage").delete().in_(
            "message_id", message_ids
        ).execute()
        usage_deleted = len(usage_result.data) if usage_result.data else 0
    
    # Delete messages
    messages_result = sb.table("chat_messages").delete().eq(
        "session_id", str(session_id)
    ).execute()
    
    messages_deleted = len(messages_result.data) if messages_result.data else 0
    
    return {
        "messages_deleted": messages_deleted,
        "usage_records_deleted": usage_deleted
    }


async def copy_session_messages(
    source_session_id: UUID,
    target_session_id: UUID
) -> int:
    """
    Copy all messages from source session to target session.
    Does not copy token usage records (for clean analytics).
    
    Args:
        source_session_id: Source session UUID
        target_session_id: Target session UUID
        
    Returns:
        Number of messages copied
    """
    sb = supabase_service
    
    # Get source messages in order
    source_result = sb.table("chat_messages").select(
        "role, content"
    ).eq("session_id", str(source_session_id)).order(
        "message_index", desc=False
    ).execute()
    
    if not source_result.data:
        return 0
    
    # Convert to MessageDraft objects
    message_drafts = []
    for msg in source_result.data:
        draft = MessageDraft(
            role=msg["role"],
            content=msg["content"],
            metadata={}
        )
        message_drafts.append(draft)
    
    # Insert into target session
    await append_messages(target_session_id, message_drafts)
    
    return len(message_drafts)
