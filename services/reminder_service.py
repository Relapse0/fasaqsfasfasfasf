"""Сервис напоминаний: планирование, отправка, повтор.

Идемпотентность: ``job_id = "reminder:{id}"`` хранится в БД; повторная
регистрация с тем же id заменяет старую джобу (``replace_existing=True``).
"""
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Bot
from apscheduler.triggers.date import DateTrigger

from database.db import get_session_factory
from database.models import Reminder
from database.repositories.couples import CouplesRepository
from database.repositories.reminders import RemindersRepository
from scheduler.scheduler import scheduler
from services.context import get_bot
from utils import emoji as e
from utils.helpers import human_date, next_occurrence
from utils.logger import get_logger

log = get_logger("service.reminder")

REPEAT_LABELS = {
    "once": "разовое",
    "daily": "ежедневно",
    "weekly": "еженедельно",
    "monthly": "ежемесячно",
}


def _job_id(reminder_id: int) -> str:
    return f"reminder:{reminder_id}"


class ReminderService:
    """Тонкая обёртка над планировщиком и репозиторием напоминаний."""

    def schedule(self, reminder: Reminder) -> None:
        """Регистрирует джобу на дату напоминания (идемпотентно)."""
        if reminder.done or reminder.remind_at is None:
            return
        scheduler.add_job(
            fire_reminder,
            trigger=DateTrigger(run_date=reminder.remind_at),
            id=_job_id(reminder.id),
            args=[reminder.id],
            replace_existing=True,
            misfire_grace_time=3600,
        )
        reminder.job_id = _job_id(reminder.id)

    def unschedule(self, reminder: Reminder) -> None:
        jid = reminder.job_id or _job_id(reminder.id)
        if scheduler.get_job(jid):
            scheduler.remove_job(jid)
        reminder.job_id = None


async def fire_reminder(reminder_id: int) -> None:
    """Точка входа джобы: уведомляет и перепланирует/закрывает напоминание."""
    factory = get_session_factory()
    async with factory() as session:
        repo = RemindersRepository(session)
        reminder = await repo.get_by_id(reminder_id)
        if reminder is None or reminder.done:
            return

        await _notify(session, reminder)

        if reminder.repeat_rule != "once":
            # Повтор: сдвигаем дату и перепланируем
            reminder.remind_at = next_occurrence(reminder.remind_at, reminder.repeat_rule)
            scheduler.add_job(
                fire_reminder,
                trigger=DateTrigger(run_date=reminder.remind_at),
                id=_job_id(reminder.id),
                args=[reminder.id],
                replace_existing=True,
            )
        else:
            reminder.done = True

        await session.commit()
        log.info("reminder_fired", reminder_id=reminder.id)


async def _notify(session, reminder: Reminder) -> None:
    """Рассылает уведомление автору и (при notify_both) партнёру."""
    couples = CouplesRepository(session)
    couple = await couples.get_by_id(reminder.couple_id)
    if couple is None:
        return

    recipients: set[int] = {reminder.author_id}
    if reminder.notify_both and couple.user2_id:
        recipients.add(couple.user2_id)
        recipients.add(couple.user1_id)

    bot: Bot = get_bot()
    repeat = f"\n🔄 Повтор: {REPEAT_LABELS.get(reminder.repeat_rule, reminder.repeat_rule)}"
    for uid in recipients:
        try:
            await bot.send_message(
                uid,
                f"{e.BELL} <b>Напоминание</b>\n\n"
                f"{reminder.text}\n\n"
                f"{e.CLOCK} {human_date(reminder.remind_at)}{repeat}",
            )
        except Exception:  # noqa: BLE001 — не даём одной ошибке убить рассылку
            log.warning("reminder_send_failed", reminder_id=reminder.id, user_id=uid)


async def restore_reminders() -> None:
    """Восстанавливает все будущие напоминания после рестарта."""
    factory = get_session_factory()
    async with factory() as session:
        repo = RemindersRepository(session)
        now = datetime.now(timezone.utc)
        pending = await repo.list_pending(now=now)
        for r in pending:
            scheduler.add_job(
                fire_reminder,
                trigger=DateTrigger(run_date=r.remind_at),
                id=_job_id(r.id),
                args=[r.id],
                replace_existing=True,
            )
    log.info("reminders_restored", count=len(pending))
