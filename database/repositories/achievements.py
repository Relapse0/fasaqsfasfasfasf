"""Репозиторий достижений и очков."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Achievement, Point
from database.repositories.base import BaseRepository


class AchievementsRepository(BaseRepository):
    async def unlock(self, couple_id: int, code: str) -> bool:
        """Разблокирует достижение. Возвращает True, если оно новое (иначе дубль)."""
        existing = await self.first(Achievement, couple_id=couple_id, code=code)
        if existing is not None:
            return False
        ach = Achievement(couple_id=couple_id, code=code)
        self.session.add(ach)
        await self.session.flush()
        return True

    async def list_for_couple(self, couple_id: int) -> list[Achievement]:
        stmt = (
            select(Achievement)
            .where(Achievement.couple_id == couple_id)
            .order_by(Achievement.unlocked_at.desc())
        )
        res = await self.session.scalars(stmt)
        return list(res.all())


class PointsRepository(BaseRepository):
    async def add(
        self, *, couple_id: int, amount: int, reason: str, user_id: int | None = None
    ) -> Point:
        p = Point(couple_id=couple_id, user_id=user_id, amount=amount, reason=reason)
        self.session.add(p)
        await self.session.flush()
        return p

    async def balance(self, couple_id: int) -> int:
        from sqlalchemy import func

        val = await self.session.scalar(
            select(func.coalesce(func.sum(Point.amount), 0)).where(
                Point.couple_id == couple_id
            )
        )
        return int(val or 0)

    async def list_for_couple(self, couple_id: int, *, limit: int = 50) -> list[Point]:
        stmt = (
            select(Point)
            .where(Point.couple_id == couple_id)
            .order_by(Point.created_at.desc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())
