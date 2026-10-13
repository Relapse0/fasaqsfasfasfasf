"""Репозиторий благодарностей."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Gratitude
from database.repositories.base import BaseRepository


class GratitudeRepository(BaseRepository):
    async def create(
        self, *, couple_id: int, from_user: int, text: str, visible_to_partner: bool = True
    ) -> Gratitude:
        g = Gratitude(
            couple_id=couple_id,
            from_user=from_user,
            text=text,
            visible_to_partner=visible_to_partner,
        )
        self.session.add(g)
        await self.session.flush()
        return g

    async def list_for_couple(
        self, couple_id: int, *, since: datetime | None = None, limit: int = 100
    ) -> list[Gratitude]:
        stmt = select(Gratitude).where(Gratitude.couple_id == couple_id)
        if since is not None:
            stmt = stmt.where(Gratitude.created_at >= since)
        stmt = stmt.order_by(Gratitude.created_at.desc()).limit(limit)
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def count_since(self, couple_id: int, since: datetime) -> int:
        val = await self.session.scalar(
            select(func.count(Gratitude.id)).where(
                Gratitude.couple_id == couple_id,
                Gratitude.created_at >= since,
            )
        )
        return int(val or 0)
