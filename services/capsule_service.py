"""Сервис капсул времени: создание и открытие в будущем.

Капсула планируется как разовая джоба APScheduler (аналог напоминаний),
а при рестарте все будущие капсулы восстанавливаются из БД.
"""
from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.triggers.date import DateTrigger

from database.db import get_session_factory
from database.models import Capsule
from database.repositories.capsules import CapsulesRepository
from database.repositories.couples import CouplesRepository
from scheduler.scheduler import scheduler
from services.context import get_bot
from utils import emoji as e
from utils.logger import get_logger

log = get_logger("service.capsule")


def _job_id(capsule_id: int) -> str:
    return f"capsule:{capsule_id}"


class CapsuleService:
    def schedule_open(self, capsule: Capsule) -> None:
        scheduler.add_job(
            fire_capsule,
            trigger=DateTrigger(run_date=capsule.open_at),
            id=_job_id(capsule.id),
            args=[capsule.id],
            replace_existing=True,
            misfire_grace_time=3600,
        )


async def fire_capsule(capsule_id: int) -> None:
    """Открывает капсулу: шлёт текст обоим участникам пары."""
    factory = get_session_factory()
    async with factory() as session:
        repo = CapsulesRepository(session)
        capsule = await repo.get_by_id(capsule_id)
        if capsule is None or capsule.opened:
            return

        couple = await CouplesRepository(session).get_by_id(capsule.couple_id)
        if couple is None:
            return

        bot = get_bot()
        text = (
            f"{e.CAPSULE} <b>Капсула времени открылась!</b>\n\n"
            f"{capsule.text}\n\n"
            f"✉️ Написано {capsule.created_at:%d.%m.%Y}"
        )
        recipients = {couple.user1_id}
        if couple.user2_id:
            recipients.add(couple.user2_id)

        for uid in recipients:
            try:
                await bot.send_message(uid, text)
            except Exception:  # noqa: BLE001
                log.warning("capsule_send_failed", capsule_id=capsule.id, user_id=uid)

        await repo.mark_opened(capsule)
        await session.commit()
        log.info("capsule_opened", capsule_id=capsule.id)


async def restore_capsules() -> None:
    """Восстанавливает все будущие капсулы после рестарта."""
    factory = get_session_factory()
    async with factory() as session:
        repo = CapsulesRepository(session)
        now = datetime.now(timezone.utc)
        future = await repo.list_future(now=now)
        for capsule in future:
            scheduler.add_job(
                fire_capsule,
                trigger=DateTrigger(run_date=capsule.open_at),
                id=_job_id(capsule.id),
                args=[capsule.id],
                replace_existing=True,
            )
    log.info("capsules_restored", count=len(future))
