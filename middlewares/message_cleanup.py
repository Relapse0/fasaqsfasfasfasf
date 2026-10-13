"""Мидлварь автоочистки сообщений.

Принцип: автоматически оборачивает message.answer / callback.message.answer,
запоминает ID отправленного сообщения и удаляет предыдущее активное сообщение
бота при следующем апдейте. Хендлеры не нужно менять.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from database.redis import get_redis
from utils.logger import get_logger

log = get_logger("middleware.cleanup")

TTL_SECONDS = 60 * 60 * 24  # 24 часа
_memory_store: dict[int, int] = {}  # chat_id -> last_bot_message_id


def _key(chat_id: int) -> str:
    return f"cleanup:{chat_id}"


async def _get_last(chat_id: int) -> int | None:
    redis = get_redis()
    if redis is not None:
        val = await redis.get(_key(chat_id))
        return int(val) if val else None
    return _memory_store.get(chat_id)


async def _set_last(chat_id: int, message_id: int) -> None:
    redis = get_redis()
    if redis is not None:
        await redis.set(_key(chat_id), message_id, ex=TTL_SECONDS)
    else:
        _memory_store[chat_id] = message_id


async def _clear(chat_id: int) -> None:
    redis = get_redis()
    if redis is not None:
        await redis.delete(_key(chat_id))
    else:
        _memory_store.pop(chat_id, None)


def _get_chat_id(event: TelegramObject) -> int | None:
    if isinstance(event, Message):
        return event.chat.id
    if isinstance(event, CallbackQuery) and event.message:
        return event.message.chat.id
    return None


def _wrap_answer(original_answer, chat_id: int):
    """0Борачивает message.answer, чтобы запоминать ID отправленного сообщения."""
    async def wrapped(*args, **kwargs):
        sent: Message = await original_answer(*args, **kwargs)
        if isinstance(sent, Message):
            await _set_last(chat_id, sent.message_id)
        return sent
    return wrapped


class MessageCleanupMiddleware(BaseMiddleware):
    """
    Автоматически удаляет предыдущее активное сообщение бота перед обработкой
    нового апдейта. Оборачивает message.answer автоматически —
    менять хендлеры не нужно.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        chat_id = _get_chat_id(event)

        if not chat_id or not bot:
            return await handler(event, data)

        # Удаляем предыдущее сообщение бота
        last_id = await _get_last(chat_id)
        if last_id:
            try:
                await bot.delete_message(chat_id, last_id)
            except Exception:  # noqa: BLE001
                pass  # уже удалено или слишком старое
            await _clear(chat_id)

        # Оборачиваем answer на Message или CallbackQuery.message
        msg = event if isinstance(event, Message) else (
            event.message if isinstance(event, CallbackQuery) else None
        )
        original_answer = None
        if msg is not None:
            original_answer = msg.answer
            msg.answer = _wrap_answer(original_answer, chat_id)

        try:
            result = await handler(event, data)
        finally:
            # Восстанавливаем оригинальный метод
            if msg is not None and original_answer is not None:
                msg.answer = original_answer

        return result
