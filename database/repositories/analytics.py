"""Репозиторий агрегатной аналитики (сводные SQL-запросы).

Собирает данные для карточек статистики и отчётов: дни вместе,
активность по дням, топ категорий трат.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Memory, Mood, Transaction
from database.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    async def activity_by_day(
        self, couple_id: int, *, since: datetime, limit: int = 30
    ) -> dict[str, int]:
        """Число действий (записей) пары по дням. Ключ — 'YYYY-MM-DD'.

        Реализация без ``to_char`` — переносима между PostgreSQL и SQLite.
        """
        result: dict[str, int] = {}
        for model in (Transaction, Mood):
            stmt = select(model.created_at).where(
                model.couple_id == couple_id, model.created_at >= since
            )
            res = await self.session.scalars(stmt)
            for dt in res:
                day = dt.strftime("%Y-%m-%d")
                result[day] = result.get(day, 0) + 1
        return result

    async def totals_since(self, couple_id: int, since: datetime) -> dict:
        """Число трат и отметок настроения за период."""
        tx_count = await self.session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.couple_id == couple_id, Transaction.created_at >= since
            )
        )
        mood_count = await self.session.scalar(
            select(func.count(Mood.id)).where(
                Mood.couple_id == couple_id, Mood.created_at >= since
            )
        )
        memory_count = await self.session.scalar(
            select(func.count(Memory.id)).where(
                Memory.couple_id == couple_id, Memory.created_at >= since
            )
        )
        return {
            "transactions": int(tx_count or 0),
            "moods": int(mood_count or 0),
            "memories": int(memory_count or 0),
        }
