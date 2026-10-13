"""Репозиторий капсул времени."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Capsule
from database.repositories.base import BaseRepository


class CapsulesRepository(BaseRepository):
    async def get_by_id(self, capsule_id: int) -> Capsule | None:
        return await self.get(Capsule, capsule_id)

    async def create(
        self, *, couple_id: int, author_id: int, text: str, open_at: datetime
    ) -> Capsule:
        c = Capsule(couple_id=couple_id, author_id=author_id, text=text, open_at=open_at)
        self.session.add(c)
        await self.session.flush()
        return c

    async def list_for_couple(self, couple_id: int) -> list[Capsule]:
        stmt = (
            select(Capsule)
            .where(Capsule.couple_id == couple_id)
            .order_by(Capsule.open_at.asc())
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def list_due(self, *, now: datetime) -> list[Capsule]:
        """Капсулы, которые пора открыть."""
        stmt = select(Capsule).where(
            Capsule.opened.is_(False), Capsule.open_at <= now
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def list_future(self, *, now: datetime) -> list[Capsule]:
        """Неоткрытые капсулы с датой в будущем (для восстановления джоб)."""
        stmt = select(Capsule).where(
            Capsule.opened.is_(False), Capsule.open_at > now
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def mark_opened(self, capsule: Capsule) -> None:
        capsule.opened = True
        await self.session.flush()
