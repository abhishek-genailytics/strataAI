from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Project, ProjectCreate, ProjectUpdate
from .base import BaseService


class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(Project)

    async def get_by_name(self, db: AsyncSession, *, user_id: UUID, name: str) -> Optional[Project]:
        """Get project by name for a specific user."""
        result = await db.execute(
            select(self.model).where(
                self.model.user_id == user_id,
                self.model.name == name
            )
        )
        return result.scalar_one_or_none()

    async def get_active_projects(self, db: AsyncSession, *, user_id: UUID) -> List[Project]:
        """Get all active projects for a user."""
        return await self.get_by_user(db, user_id=user_id, is_active=True)


project_service = ProjectService()
