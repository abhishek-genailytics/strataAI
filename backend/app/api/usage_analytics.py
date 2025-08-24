from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.deps import get_current_user, get_organization_context, CurrentUser
from ..models import APIRequest, UsageMetrics
from ..models.organization import Organization
from ..services.api_request_service import api_request_service
from ..services.usage_metrics_service import usage_metrics_service
from ..services.usage_tracking_service import usage_tracking_service

router = APIRouter()


@router.get("/usage-metrics", response_model=List[UsageMetrics])
async def get_usage_metrics(
    start_date: Optional[date] = Query(None, description="Start date for metrics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for metrics (YYYY-MM-DD)"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get usage metrics with optional filtering in organization context."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    metrics = await usage_metrics_service.get_date_range(
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
        start_date=start_date,
        end_date=end_date,
        provider_id=provider_id
    )
    
    return metrics


@router.get("/usage-summary")
async def get_usage_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for summary (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get aggregated usage summary in organization context."""
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    summary = await usage_metrics_service.get_aggregated_metrics(
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
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
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get usage trends over specified number of days in organization context."""
    trends = await usage_tracking_service.get_usage_trends(
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
        days=days,
        provider_id=provider_id
    )
    
    return {
        "trends": trends,
        "days": days,
        "organization_id": organization.id if organization else None,
        "provider_id": provider_id
    }


@router.get("/current-usage")
async def get_current_usage(
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get current day usage summary in organization context."""
    summary = await usage_tracking_service.get_current_usage_summary(
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
        provider_id=provider_id
    )
    
    return summary


@router.get("/api-requests", response_model=List[APIRequest])
async def get_api_requests(
    start_date: Optional[date] = Query(None, description="Start date for requests (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for requests (YYYY-MM-DD)"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of requests to return"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get API request logs with optional filtering in organization context."""
    if start_date and end_date:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        requests = await api_request_service.get_by_date_range(
            user_id=current_user.id,
            organization_id=organization.id if organization else None,
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id
        )
        
        # Apply limit
        return requests[:limit]
    else:
        # Get recent requests
        requests = await api_request_service.get_recent_requests(
            user_id=current_user.id,
            organization_id=organization.id if organization else None,
            limit=limit
        )
        
        # Apply additional filters if provided
        if provider_id:
            requests = [r for r in requests if r.provider_id == provider_id]
        
        return requests


@router.get("/failed-requests", response_model=List[APIRequest])
async def get_failed_requests(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get failed API requests from the last N hours in organization context."""
    failed_requests = await api_request_service.get_failed_requests(
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
        hours=hours
    )
    
    return failed_requests


@router.get("/cost-analysis")
async def get_cost_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analysis (YYYY-MM-DD)"),
    group_by: str = Query("day", regex="^(day|provider|organization)$", description="Group results by day, provider, or organization"),
    current_user: CurrentUser = Depends(get_current_user),
    organization: Optional[Organization] = Depends(get_organization_context)
):
    """Get cost analysis with grouping options in organization context."""
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
        user_id=current_user.id,
        organization_id=organization.id if organization else None,
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
    
    elif group_by == "organization":
        # Group by organization
        org_costs = {}
        for metric in metrics:
            org_id = str(metric.organization_id) if metric.organization_id else "personal"
            if org_id not in org_costs:
                org_costs[org_id] = {
                    "organization_id": org_id,
                    "total_cost_usd": 0,
                    "total_requests": 0,
                    "total_tokens": 0
                }
            org_costs[org_id]["total_cost_usd"] += float(metric.total_cost_usd)
            org_costs[org_id]["total_requests"] += metric.total_requests
            org_costs[org_id]["total_tokens"] += metric.total_tokens
        
        return {
            "group_by": group_by,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": list(org_costs.values())
        }
