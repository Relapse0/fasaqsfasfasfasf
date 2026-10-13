"""Сервис аналитики: сводки, отчёты, экспорт.

Использует репозитории агрегации и рендереры текстов/карточек.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from database.repositories.analytics import AnalyticsRepository
from database.repositories.couples import CouplesRepository
from database.repositories.gratitude import GratitudeRepository
from database.repositories.transactions import TransactionsRepository
from database.repositories.users import UsersRepository
from presentation.renderers import render_template
from utils import emoji as e
from utils.helpers import plural


class AnalyticsService:
    def __init__(self, session) -> None:
        self.session = session

    async def month_report_text(self, couple: "Couple") -> str:
        """Текстовый отчёт за месяц."""
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        totals = await AnalyticsRepository(self.session).totals_since(couple.couple_id, start)
        tx = await TransactionsRepository(self.session).total_since(couple.couple_id, start)
        return (
            f"{e.CHART} <b>Отчёт за {now:%B %Y}</b>\n\n"
            f"• Трат: <b>{totals['transactions']}</b> на сумму <b>{tx:,.0f} ₽</b>\n"
            f"• Отметок настроения: <b>{totals['moods']}</b>\n"
            f"• Воспоминаний: <b>{totals['memories']}</b>\n\n"
            f"{e.SPARKLES} Вы молодцы!"
        )

    async def wrapped_text(self, couple: "Couple", year: int) -> str:
        """Текст годового отчёта (Wrapped)."""
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        totals = await AnalyticsRepository(self.session).totals_since(couple.couple_id, start)
        tx = await TransactionsRepository(self.session).totals_by_category(couple.couple_id, start)
        top = f"{e.category(tx[0][0])} {tx[0][0]}" if tx else "—"
        days = max(1, (datetime.now(timezone.utc) - couple.created_at).days)
        return render_template(
            "wrapped_text.j2",
            year=year,
            next_year=year + 1,
            couple_name=couple.name,
            days_together=days,
            days_word=plural(days, ("день", "дня", "дней")),
            transactions=totals["transactions"],
            moods=totals["moods"],
            memories=totals["memories"],
            top_category=top,
        )

    async def export_transactions_csv(self, couple_id: int) -> io.BytesIO:
        """Экспорт трат в CSV."""
        repo = TransactionsRepository(self.session)
        rows = await repo.list_for_couple(couple_id, limit=10_000)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "user_id", "amount", "category", "comment", "created_at"])
        for t in rows:
            writer.writerow([t.id, t.user_id, t.amount, t.category, t.comment, t.created_at.isoformat()])
        return io.BytesIO(buf.getvalue().encode("utf-8"))

    async def export_json(self, couple_id: int) -> io.BytesIO:
        """Экспорт основных данных пары в JSON (для резервной копии)."""
        users = await UsersRepository(self.session).get_by_couple(couple_id)
        tx = await TransactionsRepository(self.session).list_for_couple(couple_id, limit=10_000)
        gr = await GratitudeRepository(self.session).list_for_couple(couple_id)
        payload = {
            "users": [{"user_id": u.user_id, "first_name": u.first_name} for u in users],
            "transactions": [
                {"amount": str(t.amount), "category": t.category, "created_at": t.created_at.isoformat()}
                for t in tx
            ],
            "gratitude": [
                {"from_user": g.from_user, "text": g.text, "created_at": g.created_at.isoformat()}
                for g in gr
            ],
        }
        return io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
