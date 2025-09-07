from uuid import UUID
from typing import Optional, Tuple, Dict, Any
from app.core.supabase import get_supabase_service


def find_prior_result(session_id: UUID, idempotency_key: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Returns (user_message_row, assistant_message_row) if a prior send with this idempotency_key was completed.
    
    Since we don't have metadata columns in chat_messages, we'll create a separate idempotency tracking table
    or for now, return None to disable idempotency until we can add proper schema support.
    
    Args:
        session_id: The chat session UUID
        idempotency_key: The idempotency key to search for
        
    Returns:
        Tuple of (user_message_dict, assistant_message_dict) if found, None otherwise
    """
    # TODO: Implement proper idempotency tracking table
    # For now, return None to disable idempotency feature until schema is updated
    return None


def find_existing_user_message(session_id: UUID, client_message_id: str) -> Optional[Dict[str, Any]]:
    """
    Find an existing user message by client_message_id to handle double-click protection.
    
    Since we don't have metadata columns, this feature is disabled for now.
    
    Args:
        session_id: The chat session UUID
        client_message_id: The client-generated message ID
        
    Returns:
        User message dict if found, None otherwise
    """
    # TODO: Implement proper client message ID tracking
    # For now, return None to disable double-click protection until schema is updated
    return None


def get_token_usage_for_message(message_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get token usage data for a specific message (typically assistant messages).
    
    Args:
        message_id: The message UUID
        
    Returns:
        Token usage dict if found, None otherwise
    """
    sb = get_supabase_service()
    
    result = sb.table("token_usage")\
        .select("input_tokens, output_tokens, total_tokens")\
        .eq("message_id", str(message_id))\
        .limit(1)\
        .execute()
    
    return result.data[0] if result.data else None
