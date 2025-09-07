"""
Request logging service for API telemetry and usage tracking.
Persists detailed request logs to api_requests table and optional rollups to usage_metrics.
"""
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict
from app.core.supabase import get_supabase_service


def _day_bounds(ts: datetime):
    """Get UTC day boundaries for a given timestamp."""
    start = ts.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def persist_from_request_context(
    request,
    *,
    status_code: int,
    duration_ms: Optional[int],
    request_size: Optional[int],
    response_size: Optional[int],
) -> None:
    """
    Persist API request details from FastAPI request context.
    
    Reads context assembled by prior tasks:
    - request.state.caller (PAT authentication)
    - request.state.organization_id (organization resolution)
    - request.state.provider_id (model validation)
    - request.state.model_id (model validation)
    - request.state.cost_breakdown (cost computation)
    - request.state.api_key_id (provider key lookup)
    - request.state.usage (response usage)
    - request.state.error_info (error handling)
    """
    sb = get_supabase_service()
    now = datetime.now(timezone.utc)

    # Pull context assembled by prior tasks
    caller = getattr(request.state, "caller", None)
    org_id = getattr(request.state, "organization_id", None)
    provider_id = getattr(request.state, "provider_id", None)
    model_id = getattr(request.state, "model_id", None)
    cost = getattr(request.state, "cost_breakdown", None)
    api_key_id = getattr(request.state, "api_key_id", None)
    error_info = getattr(request.state, "error_info", None)
    usage = getattr(request.state, "usage", None)

    # Build metadata JSON
    md: Dict[str, Any] = {
        "organization_id": str(org_id) if org_id else None,
        "user_id": str(caller.user_id) if caller else None,
        "model_id": str(model_id) if model_id else None,
        "usage": usage.model_dump() if usage else None,
        "cost": {
            "currency": getattr(cost, "currency", None),
            "input_cost": str(getattr(cost, "input_cost", 0)),
            "output_cost": str(getattr(cost, "output_cost", 0)),
            "request_cost": str(getattr(cost, "request_cost", 0)),
            "total_cost": str(getattr(cost, "total_cost", 0)),
        } if cost else None,
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": {"content-type": request.headers.get("content-type")},
        "feature_flags": {"force_echo_adapter": getattr(request.app.state, "force_echo", False)},
        "error": error_info,
    }

    # 1) api_requests row (authoritative audit log)
    try:
        sb.table("api_requests").insert({
            "api_key_id": str(api_key_id) if api_key_id else None,
            "provider_id": str(provider_id) if provider_id else None,
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "request_size": request_size,
            "response_size": response_size,
            "duration_ms": duration_ms,
            "error_message": error_info["message"] if error_info else None,
            "metadata": md,
        }).execute()
    except Exception as e:
        # Log but don't fail the request
        import structlog
        logger = structlog.get_logger()
        logger.error("failed_to_log_api_request", error=str(e))

    # 2) usage_metrics (optional rollups)
    if usage and provider_id and caller:
        try:
            period_start, period_end = _day_bounds(now)
            totals = [
                ("requests", 1.0),
                ("tokens", float(usage.total_tokens or 0)),
                ("cost", float(getattr(cost, "total_cost", 0) or 0)),
            ]
            
            for metric_type, metric_value in totals:
                # Use upsert pattern for daily rollups
                sb.table("usage_metrics").upsert({
                    "user_id": str(caller.user_id),
                    "provider_id": str(provider_id),
                    "metric_type": metric_type,
                    "metric_value": metric_value,
                    "time_period": "day",
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "metadata": {
                        "organization_id": str(org_id) if org_id else None,
                        "model_id": str(model_id) if model_id else None,
                    },
                }, on_conflict="user_id,provider_id,metric_type,time_period,period_start").execute()
        except Exception as e:
            # Log but don't fail the request
            import structlog
            logger = structlog.get_logger()
            logger.error("failed_to_log_usage_metrics", error=str(e))


async def log_api_request(
    *,
    api_key_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    endpoint: str,
    method: str,
    status_code: int,
    request_size: Optional[int] = None,
    response_size: Optional[int] = None,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Direct API request logging function.
    Alternative to persist_from_request_context for manual logging.
    """
    sb = get_supabase_service()
    
    try:
        sb.table("api_requests").insert({
            "api_key_id": str(api_key_id) if api_key_id else None,
            "provider_id": str(provider_id) if provider_id else None,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "request_size": request_size,
            "response_size": response_size,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "metadata": metadata or {},
        }).execute()
    except Exception as e:
        # Log but don't fail the request
        import structlog
        logger = structlog.get_logger()
        logger.error("failed_to_log_api_request_direct", error=str(e))
