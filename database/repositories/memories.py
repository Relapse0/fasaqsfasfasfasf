"""Репозиторий воспоминаний (копилка моментов)."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Memory
from database.repositories.base import BaseRepository


class MemoriesRepository(BaseRepository):
    async def create(
        self,
        *,
        couple_id: int,
        author_id: int,
        type: str,
        content: str | None = None,
        media_url: str | None = None,
    ) -> Memory:
        m = Memory(
            couple_id=couple_id,
            author_id=author_id,
            type=type,
            content=content,
            media_url=media_url,
        )
        self.session.add(m)
        await self.session.flush()
        return m

    async def list_for_couple(
        self, couple_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[Memory]:
        stmt = (
            select(Memory)
            .where(Memory.couple_id == couple_id)
            .order_by(Memory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def get_random(self, couple_id: int) -> Memory | None:
        """Случайное воспоминание (для кнопки «вспомнить момент»)."""
        stmt = (
            select(Memory)
            .where(Memory.couple_id == couple_id)
            .order_by(func.random())
            .limit(1)
        )
        return await self.session.scalar(stmt)
