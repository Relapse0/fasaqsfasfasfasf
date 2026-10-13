"""Сервис бюджета: операции, лимиты, сводки."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from database.repositories.couples import CouplesRepository
from database.repositories.transactions import TransactionsRepository


class BudgetService:
    def __init__(self, session) -> None:
        self.session = session

    async def add_transaction(
        self, *, couple_id: int, user_id: int, amount: Decimal, category: str, comment: str | None
    ):
        repo = TransactionsRepository(self.session)
        return await repo.create(
            couple_id=couple_id,
            user_id=user_id,
            amount=amount,
            category=category,
            comment=comment,
        )

    async def month_summary(self, couple_id: int) -> dict:
        """Итоги текущего месяца: сумма, по категориям, число операций."""
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        repo = TransactionsRepository(self.session)
        total = await repo.total_since(couple_id, start)
        cats = await repo.totals_by_category(couple_id, start)
        count = await repo.count_since(couple_id, start)
        return {"total": total, "categories": cats, "count": count}

    async def set_limit(self, couple_id: int, limit: Decimal) -> None:
        couples = CouplesRepository(self.session)
        couple = await couples.get_by_id(couple_id)
        if couple is None:
            return
        await couples.set_setting(couple, "budget_limit", float(limit))

    def limit(self, couple) -> Decimal | None:
        raw = (couple.settings or {}).get("budget_limit")
        return Decimal(str(raw)) if raw else None
