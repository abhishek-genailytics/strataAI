from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UsageMetrics, UsageMetricsCreate, UsageMetricsUpdate
from .usage_metrics_service import usage_metrics_service


class UsageTrackingService:
    """Service for real-time usage tracking and metrics updates."""
    
    async def update_usage_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_id: UUID,
        provider_id: UUID,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        latency_ms: Optional[int],
        is_successful: bool,
        request_date: Optional[date] = None
    ) -> UsageMetrics:
        """Update or create usage metrics for the given date."""
        if request_date is None:
            request_date = date.today()
        
        # Try to get existing metrics for the date
        existing_metrics = await usage_metrics_service.get_by_date(
            db,
            user_id=user_id,
            project_id=project_id,
            provider_id=provider_id,
            date=request_date
        )
        
        total_tokens = input_tokens + output_tokens
        
        if existing_metrics:
            # Update existing metrics
            current_total_requests = existing_metrics.total_requests
            current_successful = existing_metrics.successful_requests
            current_failed = existing_metrics.failed_requests
            current_tokens = existing_metrics.total_tokens
            current_cost = existing_metrics.total_cost_usd
            current_avg_latency = existing_metrics.avg_latency_ms or Decimal('0')
            
            # Calculate new values
            new_total_requests = current_total_requests + 1
            new_successful = current_successful + (1 if is_successful else 0)
            new_failed = current_failed + (0 if is_successful else 1)
            new_total_tokens = current_tokens + total_tokens
            new_total_cost = current_cost + cost_usd
            
            # Calculate new average latency
            if latency_ms is not None:
                if current_avg_latency > 0:
                    # Weighted average: (old_avg * old_count + new_value) / new_count
                    new_avg_latency = (
                        (current_avg_latency * current_total_requests + Decimal(str(latency_ms))) 
                        / new_total_requests
                    )
                else:
                    new_avg_latency = Decimal(str(latency_ms))
            else:
                new_avg_latency = current_avg_latency
            
            update_data = UsageMetricsUpdate(
                total_requests=new_total_requests,
                successful_requests=new_successful,
                failed_requests=new_failed,
                total_tokens=new_total_tokens,
                total_cost_usd=new_total_cost,
                avg_latency_ms=new_avg_latency
            )
            
            updated_metrics = await usage_metrics_service.update(
                db, db_obj=existing_metrics, obj_in=update_data
            )
            return updated_metrics
        else:
            # Create new metrics entry
            create_data = UsageMetricsCreate(
                user_id=user_id,
                project_id=project_id,
                provider_id=provider_id,
                date=request_date,
                total_requests=1,
                successful_requests=1 if is_successful else 0,
                failed_requests=0 if is_successful else 1,
                total_tokens=total_tokens,
                total_cost_usd=cost_usd,
                avg_latency_ms=Decimal(str(latency_ms)) if latency_ms is not None else None
            )
            
            new_metrics = await usage_metrics_service.create(db, obj_in=create_data)
            return new_metrics
    
    async def get_current_usage_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None
    ) -> dict:
        """Get current usage summary for today."""
        today = date.today()
        
        if project_id and provider_id:
            # Get specific metrics
            metrics = await usage_metrics_service.get_by_date(
                db,
                user_id=user_id,
                project_id=project_id,
                provider_id=provider_id,
                date=today
            )
            
            if metrics:
                return {
                    "date": today.isoformat(),
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "total_tokens": metrics.total_tokens,
                    "total_cost_usd": float(metrics.total_cost_usd),
                    "avg_latency_ms": float(metrics.avg_latency_ms or 0)
                }
        
        # Get aggregated metrics for today
        aggregated = await usage_metrics_service.get_aggregated_metrics(
            db,
            user_id=user_id,
            start_date=today,
            end_date=today
        )
        
        return {
            "date": today.isoformat(),
            **aggregated
        }
    
    async def get_usage_trends(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 7,
        project_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None
    ) -> list:
        """Get usage trends over the specified number of days."""
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        metrics_list = await usage_metrics_service.get_date_range(
            db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            provider_id=provider_id
        )
        
        # Convert to list of dictionaries for easy consumption
        trends = []
        for metrics in metrics_list:
            trends.append({
                "date": metrics.date.isoformat(),
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "total_tokens": metrics.total_tokens,
                "total_cost_usd": float(metrics.total_cost_usd),
                "avg_latency_ms": float(metrics.avg_latency_ms or 0)
            })
        
        return trends


usage_tracking_service = UsageTrackingService()
