"""
Playground HUD (Heads-Up Display) API endpoints.

Provides comprehensive session analytics in a single endpoint including:
- Session totals (tokens, cost, request count)
- Per-model breakdown
- Recent activity
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user, get_organization_context
from app.models.auth import CurrentCaller
from app.models.playground_hud import HudResponse, HudTotals, HudBreakdownItem, HudRecentItem
from app.services.playground_usage_svc import PlaygroundUsageService
from app.utils.supabase_client import get_supabase_user_client
from app.errors.openai_envelope import not_found_error

router = APIRouter(prefix="/playground", tags=["playground-hud"])


@router.get("/sessions/{session_id}/hud", response_model=HudResponse)
async def get_session_hud(
    session_id: str,
    window: Annotated[str, Query(description="Time window: all|24h|7d|30d")] = "all",
    recent_limit: Annotated[int, Query(description="Number of recent requests", ge=1, le=50)] = 10,
    current_user: CurrentCaller = Depends(get_current_user),
    organization_id: str = Depends(get_organization_context)
):
    """
    Get comprehensive HUD analytics for a playground session.
    
    Returns session totals, per-model breakdown, and recent activity
    in a single response optimized for dashboard display.
    """
    
    # Get user-scoped Supabase client for RLS
    supabase_client = get_supabase_user_client(current_user.jwt_token)
    
    # Verify session exists and user has access (RLS will handle this)
    session_response = supabase_client.table("chat_sessions").select("id").eq("id", session_id).execute()
    
    if not session_response.data:
        raise HTTPException(
            status_code=404,
            detail=not_found_error("Session not found", "session_not_found")
        )
    
    # Initialize usage service
    usage_service = PlaygroundUsageService(supabase_client)
    
    # Calculate time window
    from_time, to_time = usage_service._get_time_window(window, session_id)
    
    # Get session totals
    session_usage = await usage_service.get_session_usage(
        session_id=session_id,
        window=window,
        include_breakdown=True
    )
    
    # Get recent requests
    recent_requests = await usage_service.get_recent_requests(
        session_id=session_id,
        from_time=from_time,
        to_time=to_time,
        limit=recent_limit
    )
    
    # Build HUD response
    return HudResponse(
        session_id=session_id,
        window=window,
        totals=HudTotals(
            prompt_tokens=session_usage.totals.prompt_tokens,
            completion_tokens=session_usage.totals.completion_tokens,
            total_tokens=session_usage.totals.total_tokens,
            cost=session_usage.totals.cost,
            currency=session_usage.totals.currency,
            request_count=session_usage.totals.request_count
        ),
        breakdown=[
            HudBreakdownItem(
                provider=item.provider,
                model=item.model,
                requests=item.requests,
                prompt_tokens=item.prompt_tokens,
                completion_tokens=item.completion_tokens,
                total_tokens=item.total_tokens,
                cost=item.cost
            )
            for item in session_usage.breakdown
        ],
        recent=recent_requests,
        generated_at=datetime.utcnow()
    )
