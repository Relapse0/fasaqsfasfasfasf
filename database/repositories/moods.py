"""Репозиторий настроения."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Mood
from database.repositories.base import BaseRepository


class MoodsRepository(BaseRepository):
    async def create(
        self, *, user_id: int, couple_id: int, mood: int, comment: str | None
    ) -> Mood:
        obj = Mood(user_id=user_id, couple_id=couple_id, mood=mood, comment=comment)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_today(self, user_id: int, *, now: datetime) -> Mood | None:
        """Последняя отметка настроения за текущий день."""
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(Mood)
            .where(Mood.user_id == user_id, Mood.created_at >= day_start)
            .order_by(Mood.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def recent_for_user(self, user_id: int, *, limit: int = 30) -> list[Mood]:
        stmt = (
            select(Mood)
            .where(Mood.user_id == user_id)
            .order_by(Mood.created_at.desc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def recent_for_couple(self, couple_id: int, *, limit: int = 60) -> list[Mood]:
        stmt = (
            select(Mood)
            .where(Mood.couple_id == couple_id)
            .order_by(Mood.created_at.desc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def last_n_days(self, user_id: int, *, days: int, now: datetime) -> list[Mood]:
        """Одна запись на каждый из последних N дней (по последнему значению)."""
        since = now - timedelta(days=days - 1)
        since = since.replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(Mood)
            .where(Mood.user_id == user_id, Mood.created_at >= since)
            .order_by(Mood.created_at.desc())
        )
        res = await self.session.scalars(stmt)
        all_rows = list(res.all())

        # Оставляем самую позднюю запись каждого дня
        by_day: dict[str, Mood] = {}
        for m in all_rows:
            key = m.created_at.strftime("%Y-%m-%d")
            by_day.setdefault(key, m)
        return list(by_day.values())

    async def avg_for_user(self, user_id: int, *, since: datetime) -> float | None:
        val = await self.session.scalar(
            select(func.avg(Mood.mood)).where(
                Mood.user_id == user_id, Mood.created_at >= since
            )
        )
        return float(val) if val is not None else None
