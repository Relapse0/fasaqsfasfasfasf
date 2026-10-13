"""Сервис настроения: сохранение, серия «плохих дней», ежедневный опрос.

Сценарий «алерт партнёру»: если 3 дня подряд настроение ≤ 2 —
возвращаем партнёра, которому нужно отправить уведомление.
"""
from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger

from database.db import get_session_factory
from database.models import Couple, User
from database.repositories.couples import CouplesRepository
from database.repositories.moods import MoodsRepository
from database.repositories.users import UsersRepository
from scheduler.scheduler import scheduler
from services.context import get_bot
from utils import emoji as e
from utils.logger import get_logger

log = get_logger("service.mood")


class MoodService:
    def __init__(self, session) -> None:
        self.session = session

    async def save_mood(
        self, user: User, couple: Couple | None, mood: int, comment: str | None
    ) -> tuple:
        """Сохраняет настроение. Возвращает (запись, партнёр_для_алерта|None)."""
        repo = MoodsRepository(self.session)
        record = await repo.create(
            user_id=user.user_id,
            couple_id=user.couple_id or 0,
            mood=mood,
            comment=comment,
        )

        partner = None
        if await self._low_streak(user.user_id):
            users = UsersRepository(self.session)
            partner = await users.get_partner(user)
        return record, partner

    async def _low_streak(self, user_id: int) -> bool:
        """True, если 3 последних дня подряд настроение ≤ 2."""
        repo = MoodsRepository(self.session)
        now = datetime.now(timezone.utc)
        last = await repo.last_n_days(user_id, days=3, now=now)
        if len(last) < 3:
            return False
        return all(m.mood <= 2 for m in last)


def mood_alert_text(mood_owner: User) -> str:
    """Текст алерта партнёру."""
    return (
        f"{e.WARNING} <b>Кажется, {mood_owner.first_name or 'твоей половинке'} сейчас непросто.</b>\n\n"
        "Последние три дня настроение было низким. "
        "Стоит написать тёплое сообщение или просто обнять 🤍"
    )


async def send_mood_poll() -> None:
    """Ежедневный опрос настроения в 21:00 по TZ каждого пользователя.

    Вызывается cron-джобой каждый час; для пользователей, у которых
    сейчас 21:00, отправляет опрос (идемпотентно — раз в день).
    """
    factory = get_session_factory()
    async with factory() as session:
        users_repo = UsersRepository(session)
        moods_repo = MoodsRepository(session)

        # Простая и надёжная реализация: проверяем всех, у кого сейчас
        # наступил час опроса (по настройкам пары).
        from sqlalchemy import select

        rows = await session.execute(select(User))
        users = list(rows.scalars().all())

        bot = get_bot()
        from zoneinfo import ZoneInfo

        for u in users:
            try:
                tz = ZoneInfo(u.timezone)
            except Exception:  # noqa: BLE001
                continue
            now = datetime.now(tz)
            # Час опроса берём из настроек пары (по умолчанию 21)
            poll_hour = 21
            if u.couple_id:
                couple = await CouplesRepository(session).get_by_id(u.couple_id)
                if couple:
                    poll_hour = (couple.settings or {}).get("mood_poll_hour", 21)

            if now.hour != poll_hour:
                continue
            # Идемпотентность: пропускаем, если сегодня уже отмечался
            existing = await moods_repo.get_today(u.user_id, now=now)
            if existing is not None:
                continue

            try:
                from keyboards.inline import mood_keyboard

                await bot.send_message(
                    u.user_id,
                    f"{e.MOOD} Как твоё настроение сегодня, {u.first_name}?",
                    reply_markup=mood_keyboard(),
                )
            except Exception:  # noqa: BLE001
                log.warning("mood_poll_send_failed", user_id=u.user_id)


async def schedule_mood_polls() -> None:
    """Регистрирует cron-джобу, проверяющую опросы каждый час."""
    scheduler.add_job(
        send_mood_poll,
        trigger=CronTrigger(minute=0),  # в начале каждого часа
        id="mood_poll",
        replace_existing=True,
        misfire_grace_time=300,
    )
