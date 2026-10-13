"""Репозиторий финансовых операций."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Transaction
from database.repositories.base import BaseRepository


class TransactionsRepository(BaseRepository):
    async def create(
        self, *, couple_id: int, user_id: int, amount: Decimal, category: str, comment: str | None
    ) -> Transaction:
        tx = Transaction(
            couple_id=couple_id,
            user_id=user_id,
            amount=amount,
            category=category,
            comment=comment,
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def list_for_couple(
        self, couple_id: int, *, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.couple_id == couple_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.scalars(stmt)
        return list(res.all())

    async def total_since(self, couple_id: int, since: datetime) -> Decimal:
        """Сумма трат пары за период."""
        val = await self.session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.couple_id == couple_id,
                Transaction.created_at >= since,
            )
        )
        return Decimal(val or 0)

    async def totals_by_category(
        self, couple_id: int, since: datetime
    ) -> list[tuple[str, Decimal]]:
        stmt = (
            select(Transaction.category, func.sum(Transaction.amount))
            .where(
                Transaction.couple_id == couple_id,
                Transaction.created_at >= since,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        )
        rows = await self.session.execute(stmt)
        return [(r[0], Decimal(r[1] or 0)) for r in rows.all()]

    async def count_since(self, couple_id: int, since: datetime) -> int:
        val = await self.session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.couple_id == couple_id,
                Transaction.created_at >= since,
            )
        )
        return int(val or 0)
