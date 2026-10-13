"""Репозиторий челленджей (совместных заданий)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Challenge
from database.repositories.base import BaseRepository


class ChallengesRepository(BaseRepository):
    async def create(self, *, couple_id: int, text: str, day: date) -> Challenge:
        ch = Challenge(couple_id=couple_id, text=text, date=day)
        self.session.add(ch)
        await self.session.flush()
        return ch

    async def get_for_date(self, couple_id: int, day: date) -> Challenge | None:
        return await self.first(Challenge, couple_id=couple_id, date=day)

    async def list_for_couple(self, couple_id: int, *, limit: int = 30) -> list[Challenge]:
        stmt = (
            select(Challenge)
            .where(Challenge.couple_id == couple_id)
            .order_by(Challenge.date.desc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def mark_done(self, ch: Challenge, *, is_user1: bool) -> Challenge:
        if is_user1:
            ch.user1_done = True
        else:
            ch.user2_done = True
        await self.session.flush()
        return ch
