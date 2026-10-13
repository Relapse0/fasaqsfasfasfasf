"""Единственный экземпляр APScheduler на всё приложение.

Джобы хранятся в памяти; после рестарта восстанавливаются из БД
(см. ``scheduler/jobs.py`` и ``*_service.restore_*``) — это и есть
гарантия идемпотентности: ``job_id`` уникален и привязан к id записи.
"""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_settings

scheduler = AsyncIOScheduler(timezone=get_settings().scheduler_timezone)
