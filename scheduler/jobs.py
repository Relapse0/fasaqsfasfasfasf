"""Старт/стоп планировщика и восстановление задач из БД.

Периодические задачи (опрос настроения, челлендж дня, открытие капсул)
регистрируются как cron-джобы. Разовые напоминания восстанавливаются
из таблицы reminders.
"""
from __future__ import annotations

from scheduler.scheduler import scheduler
from utils.logger import get_logger

log = get_logger("scheduler")


async def start_scheduler() -> None:
    """Запускает планировщик и восстанавливает активные задачи."""
    from services.reminder_service import restore_reminders
    from services.capsule_service import restore_capsules
    from services.mood_service import schedule_mood_polls

    scheduler.start()
    await restore_reminders()
    await restore_capsules()
    await schedule_mood_polls()
    log.info("scheduler_started")


async def stop_scheduler() -> None:
    """Graceful shutdown: корректно останавливает планировщик."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
    log.info("scheduler_stopped")
