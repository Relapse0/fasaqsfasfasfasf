"""Мидлварь антиспама (throttling).

Использует Redis-лок с TTL; при отсутствии Redis — in-memory словарь.
Повторные сообщения в пределах окна отбрасываются без ответа.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import get_settings
from database.redis import get_redis
from middlewares.helpers import extract_user


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.rate: float = get_settings().throttle_rate
        self._memory: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = extract_user(event)
        if tg_user is None:
            return await handler(event, data)

        user_id = tg_user.id

        redis = get_redis()
        if redis is not None:
            key = f"throttle:{user_id}"
            # NX-лок: ставим ключ только если его ещё нет
            acquired = await redis.set(
                key, "1", px=max(1, int(self.rate * 1000)), nx=True
            )
            if not acquired:
                return None  # спам — молча отбрасываем
        else:
            now = time.monotonic()
            last = self._memory.get(user_id, 0.0)
            if now - last < self.rate:
                return None
            self._memory[user_id] = now

        return await handler(event, data)
