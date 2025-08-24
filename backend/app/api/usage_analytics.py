from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.deps import get_current_user
from ..models import APIRequest, UsageMetrics, UserProfile
from ..services.api_request_service import api_request_service
from ..services.usage_metrics_service import usage_metrics_service
from ..services.usage_tracking_service import usage_tracking_service

router = APIRouter()


@router.get("/usage-metrics", response_model=List[UsageMetrics])
async def get_usage_metrics(
    start_date: Optional[date] = Query(None, description="Start date for metrics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for metrics (YYYY-MM-DD)"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage metrics with optional filtering."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    metrics = await usage_metrics_service.get_date_range(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        project_id=project_id,
        provider_id=provider_id
    )
    
    return metrics


@router.get("/usage-summary")
async def get_usage_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for summary (YYYY-MM-DD)"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated usage summary."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    summary = await usage_metrics_service.get_aggregated_metrics(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Add date range info
    summary["start_date"] = start_date.isoformat()
    summary["end_date"] = end_date.isoformat()
    summary["days_count"] = (end_date - start_date).days + 1
    
    return summary


@router.get("/usage-trends")
async def get_usage_trends(
    days: int = Query(7, ge=1, le=365, description="Number of days for trend analysis"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage trends over specified number of days."""
    trends = await usage_tracking_service.get_usage_trends(
        db,
        user_id=current_user.id,
        days=days,
        project_id=project_id,
        provider_id=provider_id
    )
    
    return {
        "trends": trends,
        "days": days,
        "project_id": project_id,
        "provider_id": provider_id
    }


@router.get("/current-usage")
async def get_current_usage(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current day usage summary."""
    summary = await usage_tracking_service.get_current_usage_summary(
        db,
        user_id=current_user.id,
        project_id=project_id,
        provider_id=provider_id
    )
    
    return summary


@router.get("/api-requests", response_model=List[APIRequest])
async def get_api_requests(
    start_date: Optional[date] = Query(None, description="Start date for requests (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for requests (YYYY-MM-DD)"),
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of requests to return"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get API request logs with optional filtering."""
    if start_date and end_date:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        requests = await api_request_service.get_by_date_range(
            db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            provider_id=provider_id
        )
        
        # Apply limit
        return requests[:limit]
    else:
        # Get recent requests
        requests = await api_request_service.get_recent_requests(
            db,
            user_id=current_user.id,
            limit=limit
        )
        
        # Apply additional filters if provided
        if project_id:
            requests = [r for r in requests if r.project_id == project_id]
        if provider_id:
            requests = [r for r in requests if r.provider_id == provider_id]
        
        return requests


@router.get("/failed-requests", response_model=List[APIRequest])
async def get_failed_requests(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get failed API requests from the last N hours."""
    failed_requests = await api_request_service.get_failed_requests(
        db,
        user_id=current_user.id,
        hours=hours
    )
    
    return failed_requests


@router.get("/cost-analysis")
async def get_cost_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    group_by: str = Query("day", regex="^(day|provider|project)$", description="Group results by day, provider, or project"),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cost analysis with grouping options."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    # Get all metrics for the date range
    metrics = await usage_metrics_service.get_date_range(
        db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Group and aggregate based on group_by parameter
    if group_by == "day":
        # Group by date
        daily_costs = {}
        for metric in metrics:
            date_str = metric.date.isoformat()
            if date_str not in daily_costs:
                daily_costs[date_str] = {
                    "date": date_str,
                    "total_cost_usd": 0,
                    "total_requests": 0,
                    "total_tokens": 0
                }
            daily_costs[date_str]["total_cost_usd"] += float(metric.total_cost_usd)
            daily_costs[date_str]["total_requests"] += metric.total_requests
            daily_costs[date_str]["total_tokens"] += metric.total_tokens
        
        return {
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": list(daily_costs.values())
        }
    
    elif group_by == "provider":
        # Group by provider
        provider_costs = {}
        for metric in metrics:
            provider_id = str(metric.provider_id)
            if provider_id not in provider_costs:
                provider_costs[provider_id] = {
                    "provider_id": provider_id,
                    "total_cost_usd": 0,
                    "total_requests": 0,
                    "total_tokens": 0
                }
            provider_costs[provider_id]["total_cost_usd"] += float(metric.total_cost_usd)
            provider_costs[provider_id]["total_requests"] += metric.total_requests
            provider_costs[provider_id]["total_tokens"] += metric.total_tokens
        
        return {
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": list(provider_costs.values())
        }
    
    elif group_by == "project":
        # Group by project
        project_costs = {}
        for metric in metrics:
            project_id = str(metric.project_id)
            if project_id not in project_costs:
                project_costs[project_id] = {
                    "project_id": project_id,
                    "total_cost_usd": 0,
                    "total_requests": 0,
                    "total_tokens": 0
                }
            project_costs[project_id]["total_cost_usd"] += float(metric.total_cost_usd)
            project_costs[project_id]["total_requests"] += metric.total_requests
            project_costs[project_id]["total_tokens"] += metric.total_tokens
        
        return {
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": list(project_costs.values())
        }
