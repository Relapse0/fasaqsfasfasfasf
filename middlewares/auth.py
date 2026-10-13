"""Мидлварь авторизации и контекста пары.

На каждый апдейт открывает сессию БД, загружает/создаёт пользователя,
подтягивает его пару и настройки, кладёт всё в ``data`` для хендлеров:
- ``data["session"]``  — AsyncSession (закрывается после хендлера)
- ``data["user"]``     — ORM User
- ``data["couple"]``   — ORM Couple | None
- ``data["settings"]`` — dict настроек пары (или {})
- ``data["language"]`` — нормализованный язык ('ru' | 'en')
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import get_settings
from database.db import get_session_factory
from database.repositories.couples import CouplesRepository
from database.repositories.users import UsersRepository
from middlewares.helpers import extract_user
from utils.logger import get_logger

log = get_logger("middleware.auth")


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Достаём отправителя из Message/CallbackQuery/etc.
        user_meta = self._extract_user(event)
        if user_meta is None:
            # Системные апдейты без пользователя (например, poll) пропускаем
            return await handler(event, data)

        user_id, username, first_name, lang = user_meta
        settings = get_settings()

        factory = get_session_factory()
        async with factory() as session:
            users = UsersRepository(session)
            user = await users.upsert(
                user_id,
                username=username,
                first_name=first_name,
                timezone=settings.default_timezone,
                language=lang or settings.default_language,
            )

            couple = None
            if user.couple_id:
                couples = CouplesRepository(session)
                couple = await couples.get_by_id(user.couple_id)

            data["session"] = session
            data["user"] = user
            data["couple"] = couple
            data["settings"] = couple.settings if couple else {}
            data["language"] = user.language

            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                log.exception("unhandled_error", user_id=user_id)
                raise

    def _extract_user(self, event: TelegramObject):
        """Возвращает (user_id, username, first_name, language) или None."""
        tg_user = extract_user(event)
        if tg_user is None:
            return None

        lang = tg_user.language_code or "ru"
        if lang not in ("ru", "en"):
            lang = "ru"
        return tg_user.id, tg_user.username, tg_user.first_name or "", lang
