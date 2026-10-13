"""Репозиторий событий и дат (годовщины, дни рождения)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event
from database.repositories.base import BaseRepository


class EventsRepository(BaseRepository):
    async def create(
        self,
        *,
        couple_id: int,
        title: str,
        event_date: date,
        repeat_yearly: bool = True,
        notify_days_before: int = 3,
    ) -> Event:
        event = Event(
            couple_id=couple_id,
            title=title,
            event_date=event_date,
            repeat_yearly=repeat_yearly,
            notify_days_before=notify_days_before,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_for_couple(self, couple_id: int) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.couple_id == couple_id)
            .order_by(Event.event_date.asc())
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, couple_id: int, event_id: int) -> Event | None:
        return await self.first(Event, id=event_id, couple_id=couple_id)

    async def remove(self, event: Event) -> None:
        await self.delete(event)
