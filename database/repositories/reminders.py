"""Репозиторий напоминаний."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Reminder
from database.repositories.base import BaseRepository


class RemindersRepository(BaseRepository):
    async def get_by_id(self, reminder_id: int) -> Reminder | None:
        return await self.get(Reminder, reminder_id)

    async def create(self, **kwargs) -> Reminder:
        reminder = Reminder(**kwargs)
        self.session.add(reminder)
        await self.session.flush()
        return reminder

    async def list_for_couple(
        self, couple_id: int, *, only_active: bool = False, limit: int = 50
    ) -> list[Reminder]:
        stmt = select(Reminder).where(Reminder.couple_id == couple_id)
        if only_active:
            stmt = stmt.where(Reminder.done.is_(False))
        stmt = stmt.order_by(Reminder.remind_at.asc()).limit(limit)
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def list_visible_for(
        self, couple_id: int, user_id: int, *, limit: int = 50
    ) -> list[Reminder]:
        """Напоминания, видимые пользователю: общие + свои приватные."""
        stmt = (
            select(Reminder)
            .where(
                Reminder.couple_id == couple_id,
                Reminder.done.is_(False),
                (Reminder.visible_to_partner.is_(True))
                | (Reminder.author_id == user_id),
            )
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def mark_done(self, reminder: Reminder) -> None:
        reminder.done = True
        await self.session.flush()

    async def set_job_id(self, reminder: Reminder, job_id: str | None) -> None:
        reminder.job_id = job_id
        await self.session.flush()

    async def set_remind_at(self, reminder: Reminder, remind_at: datetime) -> None:
        reminder.remind_at = remind_at
        await self.session.flush()

    async def delete(self, reminder: Reminder) -> None:
        await super().delete(reminder)

    async def list_pending(self, *, now: datetime, limit: int = 1000) -> list[Reminder]:
        """Все невыполненные напоминания с будущим временем (для восстановления)."""
        stmt = (
            select(Reminder)
            .where(Reminder.done.is_(False), Reminder.remind_at > now)
            .order_by(Reminder.remind_at.asc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())
