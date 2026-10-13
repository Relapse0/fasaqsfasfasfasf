"""Репозиторий списка покупок."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ShoppingItem
from database.repositories.base import BaseRepository


class ShoppingRepository(BaseRepository):
    async def create(
        self, *, couple_id: int, item: str, category: str, added_by: int
    ) -> ShoppingItem:
        obj = ShoppingItem(
            couple_id=couple_id, item=item, category=category, added_by=added_by
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_active(self, couple_id: int) -> list[ShoppingItem]:
        stmt = (
            select(ShoppingItem)
            .where(ShoppingItem.couple_id == couple_id, ShoppingItem.done.is_(False))
            .order_by(ShoppingItem.created_at.asc())
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def list_all(self, couple_id: int, *, limit: int = 100) -> list[ShoppingItem]:
        stmt = (
            select(ShoppingItem)
            .where(ShoppingItem.couple_id == couple_id)
            .order_by(ShoppingItem.created_at.desc())
            .limit(limit)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def get_by_id(self, couple_id: int, item_id: int) -> ShoppingItem | None:
        return await self.first(ShoppingItem, id=item_id, couple_id=couple_id)

    async def toggle(self, item: ShoppingItem) -> ShoppingItem:
        item.done = not item.done
        await self.session.flush()
        return item

    async def remove(self, item: ShoppingItem) -> None:
        await self.delete(item)
