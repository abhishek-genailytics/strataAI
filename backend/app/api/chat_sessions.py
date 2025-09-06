from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from ..utils.supabase_client import supabase_service
from ..core.deps import get_current_user, CurrentUser

router = APIRouter()

# Pydantic models for request/response
class ChatSessionCreate(BaseModel):
    provider: str
    model: str
    session_name: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    provider: str
    model: str
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

class ChatSessionConfigResponse(BaseModel):
    id: str
    provider: str
    model: str
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    # Model configuration details
    model_display_name: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_streaming: Optional[bool] = None
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None

class ChatMessageCreate(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    token_usage: Optional[dict] = None

class TokenUsageCreate(BaseModel):
    message_id: str
    provider: str
    model: str
    token_count: int
    token_type: str  # 'input' or 'output'

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new chat session"""
    supabase = supabase_service
    
    try:
        # Create new session
        session_insert = {
            "user_id": str(current_user.id),
            "provider": session_data.provider,
            "model": session_data.model,
            "session_name": session_data.session_name or "New Chat"
        }
        
        result = supabase.table("chat_sessions").insert(session_insert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session"
            )
        
        session = result.data[0]
        return ChatSessionResponse(
            id=session["id"],
            provider=session["provider"],
            model=session["model"],
            session_name=session["session_name"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating chat session: {str(e)}"
        )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_chat_sessions(
    limit: int = 5,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all chat sessions for the current user"""
    supabase = supabase_service
    
    try:
        # Get sessions with pagination, ordered by most recent first
        result = supabase.table("chat_sessions").select(
            "*"
        ).eq("user_id", str(current_user.id)).order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Get message counts separately
        sessions = []
        for session in result.data:
            message_count_result = supabase.table("chat_messages").select(
                "id", count="exact"
            ).eq("session_id", session["id"]).execute()
            
            message_count = message_count_result.count if message_count_result.count is not None else 0
            
            session_data = {
                "id": session["id"],
                "user_id": session["user_id"],
                "provider": session["provider"],
                "model": session["model"],
                "session_name": session["session_name"],
                "message_count": message_count,
                "created_at": session["created_at"],
                "updated_at": session["updated_at"]
            }
            sessions.append(session_data)
            print(f"DEBUG: Session {session['id']}: {session['session_name']} ({message_count} messages)")
        
        print(f"DEBUG: Returning {len(sessions)} sessions")
        return [ChatSessionResponse(
            id=session["id"],
            provider=session["provider"],
            model=session["model"],
            session_name=session["session_name"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=session["message_count"]
        ) for session in sessions]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chat sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a specific chat session"""
    supabase = supabase_service
    
    try:
        result = supabase.table("chat_sessions").select(
            "*"
        ).eq("id", session_id).eq("user_id", str(current_user.id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        session = result.data[0]
        
        # Get message count separately
        message_count_result = supabase.table("chat_messages").select(
            "id", count="exact"
        ).eq("session_id", session_id).execute()
        
        count = message_count_result.count if message_count_result.count is not None else 0
        
        return ChatSessionResponse(
            id=session["id"],
            provider=session["provider"],
            model=session["model"],
            session_name=session["session_name"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching chat session: {str(e)}"
        )

@router.put("/sessions/{session_id}/name")
async def update_session_name(
    session_id: str,
    session_name: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update chat session name"""
    supabase = supabase_service
    
    try:
        result = supabase.table("chat_sessions").update({
            "session_name": session_name,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", session_id).eq("user_id", str(current_user.id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {"message": "Session name updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating session name: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete a chat session and all its messages"""
    supabase = supabase_service
    
    try:
        result = supabase.table("chat_sessions").delete().eq(
            "id", session_id
        ).eq("user_id", str(current_user.id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting chat session: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all messages for a specific chat session"""
    supabase = supabase_service
    
    try:
        # First verify session belongs to user
        session_result = supabase.table("chat_sessions").select("id").eq(
            "id", session_id
        ).eq("user_id", str(current_user.id)).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Get messages with token usage
        result = supabase.table("chat_messages").select(
            "*, token_usage(*)"
        ).eq("session_id", session_id).order("created_at").execute()
        
        messages = []
        for message in result.data:
            token_usage = None
            if message.get("token_usage"):
                token_data = message["token_usage"][0] if message["token_usage"] else None
                if token_data:
                    token_usage = {
                        "provider": token_data["provider"],
                        "model": token_data["model"],
                        "token_count": token_data["token_count"],
                        "token_type": token_data["token_type"]
                    }
            
            messages.append(ChatMessageResponse(
                id=message["id"],
                session_id=message["session_id"],
                role=message["role"],
                content=message["content"],
                created_at=message["created_at"],
                token_usage=token_usage
            ))
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching session messages: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def add_message_to_session(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add a message to a chat session"""
    supabase = supabase_service
    
    try:
        # Verify session belongs to user
        session_result = supabase.table("chat_sessions").select("id").eq(
            "id", session_id
        ).eq("user_id", str(current_user.id)).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Insert message
        message_insert = {
            "session_id": session_id,
            "role": message_data.role,
            "content": message_data.content
        }
        
        result = supabase.table("chat_messages").insert(message_insert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add message"
            )
        
        # Update session timestamp
        supabase.table("chat_sessions").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", session_id).execute()
        
        message = result.data[0]
        return ChatMessageResponse(
            id=message["id"],
            session_id=message["session_id"],
            role=message["role"],
            content=message["content"],
            created_at=message["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding message: {str(e)}"
        )

@router.post("/messages/{message_id}/token-usage")
async def add_token_usage(
    message_id: str,
    token_data: TokenUsageCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add token usage data for a message"""
    supabase = supabase_service
    
    try:
        # Verify message belongs to user's session
        message_result = supabase.table("chat_messages").select(
            "id, session_id, chat_sessions!inner(user_id)"
        ).eq("id", message_id).execute()
        
        if not message_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        message = message_result.data[0]
        if message["chat_sessions"]["user_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Insert token usage
        token_insert = {
            "message_id": message_id,
            "provider": token_data.provider,
            "model": token_data.model,
            "token_count": token_data.token_count,
            "token_type": token_data.token_type
        }
        
        result = supabase.table("token_usage").insert(token_insert).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add token usage"
            )
        
        return {"message": "Token usage added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding token usage: {str(e)}"
        )

@router.get("/sessions/{session_id}/config", response_model=ChatSessionConfigResponse)
async def get_session_config(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get session details with model configuration for restoring playground settings"""
    supabase = supabase_service
    
    try:
        # Get session details
        session_result = supabase.table("chat_sessions").select(
            "*"
        ).eq("id", session_id).eq("user_id", str(current_user.id)).execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        session = session_result.data[0]
        
        # Get message count
        message_count_result = supabase.table("chat_messages").select(
            "id", count="exact"
        ).eq("session_id", session_id).execute()
        
        message_count = message_count_result.count if message_count_result.count is not None else 0
        
        # Get model configuration details
        model_result = supabase.table("ai_models").select(
            """
            display_name,
            max_tokens,
            supports_streaming,
            model_pricing(pricing_type, price_per_unit)
            """
        ).eq("model_name", session["model"]).eq("is_active", True).execute()
        
        model_display_name = None
        max_tokens = None
        supports_streaming = None
        input_cost = None
        output_cost = None
        
        if model_result.data:
            model_data = model_result.data[0]
            model_display_name = model_data.get("display_name")
            max_tokens = model_data.get("max_tokens")
            supports_streaming = model_data.get("supports_streaming")
            
            # Extract pricing information
            if model_data.get('model_pricing'):
                for pricing in model_data['model_pricing']:
                    if pricing['pricing_type'] == 'input':
                        input_cost = float(pricing['price_per_unit'])
                    elif pricing['pricing_type'] == 'output':
                        output_cost = float(pricing['price_per_unit'])
        
        return ChatSessionConfigResponse(
            id=session["id"],
            provider=session["provider"],
            model=session["model"],
            session_name=session["session_name"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=message_count,
            model_display_name=model_display_name,
            max_tokens=max_tokens,
            supports_streaming=supports_streaming,
            cost_per_1k_input_tokens=input_cost,
            cost_per_1k_output_tokens=output_cost
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching session config: {str(e)}"
        )
