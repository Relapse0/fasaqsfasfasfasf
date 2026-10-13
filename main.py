"""Точка входа бота.

Запуск: ``python -m main`` (или ``python main.py``).
Собирает всё вместе: логирование, БД, Redis, Bot, Dispatcher,
мидлвари, роутеры, планировщик — и стартует long-polling или webhook.
"""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import get_settings
from database.db import create_all, dispose_db, init_db
from database.redis import close_redis, init_redis
from handlers import (
    achievements,
    analytics,
    budget,
    dates,
    games,
    gratitude,
    memories,
    menu,
    mood,
    reminders,
    romance,
    settings as settings_handlers,
    shopping,
    start,
)
from middlewares.auth import AuthMiddleware
from middlewares.i18n import I18nMiddleware
from middlewares.logging import LoggingMiddleware
from middlewares.throttling import ThrottlingMiddleware
from middlewares.message_cleanup import MessageCleanupMiddleware
from scheduler.jobs import start_scheduler, stop_scheduler
from services.context import set_bot
from utils.logger import configure_logging, get_logger

log = get_logger("main")


async def set_bot_commands(bot: Bot) -> None:
    """Регистрирует список команд в меню бота."""
    commands = [
        BotCommand(command="start", description="Начать / привязать пару"),
        BotCommand(command="menu", description="Главное меню"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main() -> None:
    configure_logging()
    settings = get_settings()

    init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    set_bot(bot)

    # FSM: Redis при наличии, иначе память (локальная разработка)
    redis = init_redis()
    storage = RedisStorage(redis=redis) if redis is not None else MemoryStorage()

    dp = Dispatcher(storage=storage)

    # Мидлвари (в aiogram последняя зарегистрированная — самая внешняя).
    # Throttling — внешняя (отсекает спам до БД), Auth — открывает сессию,
    # Logging — внутренняя.
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(I18nMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(ThrottlingMiddleware())
    dp.message.middleware(MessageCleanupMiddleware())
    dp.callback_query.middleware(MessageCleanupMiddleware())

    # Роутеры модулей
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(reminders.router)
    dp.include_router(shopping.router)
    dp.include_router(budget.router)
    dp.include_router(mood.router)
    dp.include_router(dates.router)
    dp.include_router(gratitude.router)
    dp.include_router(romance.router)
    dp.include_router(memories.router)
    dp.include_router(analytics.router)
    dp.include_router(achievements.router)
    dp.include_router(games.router)
    dp.include_router(settings_handlers.router)

    await set_bot_commands(bot)

    # Локальная разработка на SQLite: создаём таблицы автоматически.
    # В проде схему накатывает Alembic.
    if settings.is_sqlite:
        await create_all()

    await start_scheduler()

    try:
        if settings.webhook_enabled:
            await _run_webhook(bot, dp, settings)
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
    finally:
        await stop_scheduler()
        await close_redis()
        await dispose_db()
        await bot.session.close()
        log.info("bot_stopped")


async def _run_webhook(bot: Bot, dp: Dispatcher, settings) -> None:
    """Webhook-режим (для продакшена за обратным прокси)."""
    from aiohttp import web

    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)
    await site.start()

    await bot.set_webhook(
        f"{settings.webhook_url.rstrip('/')}{settings.webhook_path}",
        drop_pending_updates=True,
    )
    log.info("webhook_started", url=settings.webhook_url)

    # Держим приложение живым до остановки
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("bot_terminated")
