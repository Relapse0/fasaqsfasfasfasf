"""Мидлварь i18n: нормализует язык и кладёт его в контекст логгера.

Сам язык уже определён в AuthMiddleware из ``from_user.language_code``;
здесь он прокидывается в structlog для трассировки.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        language = data.get("language", "ru")
        structlog.contextvars.bind_contextvars(language=language)
        try:
            return await handler(event, data)
        finally:
            structlog.contextvars.unbind_contextvars("language")
