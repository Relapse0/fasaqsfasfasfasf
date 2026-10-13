"""Фасад генерации карточек: собирает данные и вызывает Pillow/matplotlib.

Все тяжёлые функции рендера выполняются в потоке через ``asyncio.to_thread``,
чтобы не блокировать event loop.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

from config import get_settings
from database.models import Couple
from database.repositories.achievements import PointsRepository
from database.repositories.analytics import AnalyticsRepository
from database.repositories.couples import CouplesRepository
from database.repositories.moods import MoodsRepository
from database.repositories.transactions import TransactionsRepository
from database.repositories.users import UsersRepository
from presentation.cards.budget_card import render_budget_card
from presentation.cards.mood_chart import render_mood_chart
from presentation.cards.profile_card import render_profile_card
from presentation.cards.stats_card import render_stats_card
from presentation.cards.wrapped_card import render_wrapped_card
from utils import emoji as e


class CardService:
    def __init__(self) -> None:
        settings = get_settings()
        self.generated_dir = settings.generated_dir
        os.makedirs(self.generated_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        return os.path.join(self.generated_dir, name)

    # ── Карточка статистики ───────────────────────────────
    async def stats_card(self, session, couple: Couple) -> str:
        users = await UsersRepository(session).get_by_couple(couple.couple_id)
        names = [u.first_name or "Партнёр" for u in users]
        name1 = names[0] if len(names) > 0 else "Партнёр 1"
        name2 = names[1] if len(names) > 1 else "Партнёр 2"

        points = await PointsRepository(session).balance(couple.couple_id)
        since = datetime.now(timezone.utc) - timedelta(days=30)
        totals = await AnalyticsRepository(session).totals_since(couple.couple_id, since)
        tx_repo = TransactionsRepository(session)
        cats = await tx_repo.totals_by_category(couple.couple_id, since)
        top = [(f"{e.category(c)} {c}", float(amount)) for c, amount in cats[:4]]

        act_map = await AnalyticsRepository(session).activity_by_day(
            couple.couple_id, since=since, limit=14
        )
        activity = [
            act_map.get(
                (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"), 0
            )
            for i in range(13, -1, -1)
        ]

        days_together = max(1, (datetime.now(timezone.utc) - couple.created_at).days)
        out = self._path(f"stats_{couple.couple_id}.png")
        return await asyncio.to_thread(
            render_stats_card,
            couple_name=couple.name,
            days_together=days_together,
            user1_name=name1,
            user2_name=name2,
            points=points,
            stats=totals,
            top_categories=top,
            activity=activity,
            out_path=out,
        )

    # ── График настроения ─────────────────────────────────
    async def mood_chart(self, session, couple: Couple) -> str:
        users = await UsersRepository(session).get_by_couple(couple.couple_id)
        moods_repo = MoodsRepository(session)
        series: dict[str, list[tuple]] = {}
        for u in users:
            rows = await moods_repo.recent_for_user(u.user_id, limit=30)
            series[u.first_name or str(u.user_id)] = [
                (m.created_at, m.mood) for m in reversed(rows)
            ]
        out = self._path(f"mood_{couple.couple_id}.png")
        return await asyncio.to_thread(render_mood_chart, series=series, out_path=out)

    # ── Карточка профиля ──────────────────────────────────
    async def profile_card(self, session, couple: Couple) -> str:
        users = await UsersRepository(session).get_by_couple(couple.couple_id)
        name1 = users[0].first_name if len(users) > 0 else "Партнёр 1"
        name2 = users[1].first_name if len(users) > 1 else "Партнёр 2"

        modules = (couple.settings or {}).get("modules", {})
        active = sum(1 for v in modules.values() if v)
        total = len(modules)
        days_together = max(1, (datetime.now(timezone.utc) - couple.created_at).days)

        out = self._path(f"profile_{couple.couple_id}.png")
        return await asyncio.to_thread(
            render_profile_card,
            couple_name=couple.name,
            user1_name=name1,
            user2_name=name2,
            days_together=days_together,
            invite_code=couple.invite_code,
            active_modules=active,
            total_modules=total,
            out_path=out,
        )

    # ── Карточка бюджета ──────────────────────────────────
    async def budget_card(self, session, couple: Couple) -> str:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tx_repo = TransactionsRepository(session)
        total = await tx_repo.total_since(couple.couple_id, month_start)
        cats = await tx_repo.totals_by_category(couple.couple_id, month_start)
        top = [(f"{e.category(c)} {c}", amount) for c, amount in cats[:5]]
        limit = (couple.settings or {}).get("budget_limit")
        from decimal import Decimal

        limit = Decimal(str(limit)) if limit else None
        out = self._path(f"budget_{couple.couple_id}.png")
        return await asyncio.to_thread(
            render_budget_card,
            month_label=now.strftime("%B %Y"),
            total_spent=total,
            limit=limit,
            top_categories=top,
            out_path=out,
        )

    # ── Годовой Wrapped ───────────────────────────────────
    async def wrapped_card(self, session, couple: Couple, year: int) -> tuple[str, dict]:
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        totals = await AnalyticsRepository(session).totals_since(couple.couple_id, start)
        tx_repo = TransactionsRepository(session)
        cats = await tx_repo.totals_by_category(couple.couple_id, start)
        top_category = f"{e.category(cats[0][0])} {cats[0][0]}" if cats else "—"
        days_together = max(1, (end - couple.created_at).days) if couple.created_at < end else 365

        out = self._path(f"wrapped_{couple.couple_id}.png")
        path = await asyncio.to_thread(
            render_wrapped_card,
            year=year,
            couple_name=couple.name,
            days_together=days_together,
            facts=[
                (str(totals["transactions"]), "трат за год"),
                (str(totals["moods"]), "отметок настроения"),
                (str(totals["memories"]), "воспоминаний"),
            ],
            top_category=top_category,
            out_path=out,
        )
        return path, {"totals": totals, "top_category": top_category}
