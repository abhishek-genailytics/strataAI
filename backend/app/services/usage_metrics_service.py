from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UsageMetrics, UsageMetricsCreate, UsageMetricsUpdate
from .base import BaseService


class UsageMetricsService(BaseService[UsageMetrics, UsageMetricsCreate, UsageMetricsUpdate]):
    def __init__(self):
        super().__init__(UsageMetrics)

    async def get_by_date(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        organization_id: UUID,
        provider_id: UUID,
        date: date
    ) -> Optional[UsageMetrics]:
        """Get usage metrics for a specific date."""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.organization_id == organization_id,
                    self.model.provider_id == provider_id,
                    self.model.date == date
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_date_range(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        start_date: date,
        end_date: date,
        organization_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None
    ) -> List[UsageMetrics]:
        """Get usage metrics within a date range."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.date >= start_date,
                self.model.date <= end_date
            )
        )
        
        if organization_id:
            query = query.where(self.model.organization_id == organization_id)
        if provider_id:
            query = query.where(self.model.provider_id == provider_id)
            
        result = await db.execute(query.order_by(self.model.date.desc()))
        return result.scalars().all()

    async def get_aggregated_metrics(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get aggregated metrics across all organizations and providers."""
        result = await db.execute(
            select(
                func.sum(self.model.total_requests).label('total_requests'),
                func.sum(self.model.successful_requests).label('successful_requests'),
                func.sum(self.model.failed_requests).label('failed_requests'),
                func.sum(self.model.total_tokens).label('total_tokens'),
                func.sum(self.model.total_cost_usd).label('total_cost_usd'),
                func.avg(self.model.avg_latency_ms).label('avg_latency_ms')
            ).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.date >= start_date,
                    self.model.date <= end_date
                )
            )
        )
        row = result.first()
        return {
            'total_requests': row.total_requests or 0,
            'successful_requests': row.successful_requests or 0,
            'failed_requests': row.failed_requests or 0,
            'total_tokens': row.total_tokens or 0,
            'total_cost_usd': float(row.total_cost_usd or 0),
            'avg_latency_ms': float(row.avg_latency_ms or 0)
        }


usage_metrics_service = UsageMetricsService()
