"""Мидлварь логирования входящих апдейтов."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from middlewares.helpers import extract_user
from utils.logger import get_logger

log = get_logger("middleware.logging")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_type = event.__class__.__name__
        tg_user = extract_user(event)
        log.info(
            "incoming_update",
            event_type=event_type,
            user_id=getattr(tg_user, "id", None),
        )
        return await handler(event, data)
