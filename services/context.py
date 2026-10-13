"""Ссылка на экземпляр Bot для использования в планировщике.

Джобы APScheduler выполняются вне хендлеров, поэтому им нужен
доступ к Bot. Храним его здесь, а не в аргументах джобы — так
аргументы остаются сериализуемыми (важно для будущего перехода
на постоянный jobstore/Celery).
"""
from __future__ import annotations

from aiogram import Bot

bot: Bot | None = None


def set_bot(instance: Bot) -> None:
    global bot
    bot = instance


def get_bot() -> Bot:
    assert bot is not None, "Bot не инициализирован"
    return bot
