from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user, get_organization_context, CurrentUser
from app.models.playground_usage import SessionUsageResponse, SessionSeriesPoint
from app.services.playground_usage_svc import PlaygroundUsageService
from app.utils.supabase_client import get_supabase_user_client
from app.errors.openai_envelope import session_not_found_error


router = APIRouter(prefix="/playground/sessions", tags=["playground-usage"])


@router.get("/{session_id}/usage", response_model=SessionUsageResponse)
async def get_session_usage(
    session_id: str,
    window: str = Query("all", regex="^(all|24h|7d|30d)$"),
    include_breakdown: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Get usage totals and breakdown for a session.
    
    Args:
        session_id: The session ID to get usage for
        window: Time window filter (all, 24h, 7d, 30d)
        include_breakdown: Whether to include per-provider/model breakdown
    
    Returns:
        SessionUsageResponse with totals and optional breakdown
    """
    
    # Get user-scoped Supabase client for RLS
    supabase_client = get_supabase_user_client(current_user.jwt_token)
    
    # Verify session exists and user owns it
    session_response = supabase_client.table("chat_sessions").select("id").eq(
        "id", session_id
    ).eq("user_id", current_user.user_id).single().execute()
    
    if not session_response.data:
        raise session_not_found_error(session_id)
    
    # Get usage data
    usage_service = PlaygroundUsageService(supabase_client)
    return await usage_service.get_session_usage(
        session_id=session_id,
        window=window,
        include_breakdown=include_breakdown
    )


@router.get("/{session_id}/usage/series", response_model=List[SessionSeriesPoint])
async def get_session_usage_series(
    session_id: str,
    bucket: str = Query("day", regex="^(hour|day)$"),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Get usage time series data for charting.
    
    Args:
        session_id: The session ID to get series data for
        bucket: Time bucket size (hour, day)
        since: Start time (defaults to session creation)
        until: End time (defaults to session last update)
    
    Returns:
        List of SessionSeriesPoint for time series charts
    """
    
    # Get user-scoped Supabase client for RLS
    supabase_client = get_supabase_user_client(current_user.jwt_token)
    
    # Verify session exists and user owns it
    session_response = supabase_client.table("chat_sessions").select("id").eq(
        "id", session_id
    ).eq("user_id", current_user.user_id).single().execute()
    
    if not session_response.data:
        raise session_not_found_error(session_id)
    
    # Get series data
    usage_service = PlaygroundUsageService(supabase_client)
    return await usage_service.get_session_usage_series(
        session_id=session_id,
        bucket=bucket,
        since=since,
        until=until
    )
