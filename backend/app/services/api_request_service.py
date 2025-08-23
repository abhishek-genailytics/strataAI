from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import APIRequest, APIRequestCreate
from .base import BaseService


class APIRequestService(BaseService[APIRequest, APIRequestCreate, None]):
    def __init__(self):
        super().__init__(APIRequest)

    async def get_by_date_range(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        start_date: date,
        end_date: date,
        project_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None
    ) -> List[APIRequest]:
        """Get API requests within a date range."""
        query = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                func.date(self.model.created_at) >= start_date,
                func.date(self.model.created_at) <= end_date
            )
        )
        
        if project_id:
            query = query.where(self.model.project_id == project_id)
        if provider_id:
            query = query.where(self.model.provider_id == provider_id)
            
        result = await db.execute(query.order_by(self.model.created_at.desc()))
        return result.scalars().all()

    async def get_recent_requests(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        limit: int = 50
    ) -> List[APIRequest]:
        """Get recent API requests for a user."""
        result = await db.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_failed_requests(
        self, 
        db: AsyncSession, 
        *, 
        user_id: UUID,
        hours: int = 24
    ) -> List[APIRequest]:
        """Get failed requests within the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.status_code >= 400,
                    self.model.created_at >= cutoff_time
                )
            ).order_by(self.model.created_at.desc())
        )
        return result.scalars().all()


api_request_service = APIRequestService()
