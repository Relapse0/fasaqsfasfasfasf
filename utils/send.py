"""Утилита для отправки сообщений с автоочисткой.

Используйте `send` и `edit` вместо прямого message.answer / message.edit_text.
Тогда ID отправленного сообщения запоминается для авточистки.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup


async def send(
    message: Message,
    text: str,
    remember_message: Callable[[int], Awaitable[None]] | None = None,
    reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    **kwargs: Any,
) -> Message:
    """Отправляет сообщение и запоминает его ID для автоочистки."""
    sent = await message.answer(text, reply_markup=reply_markup, **kwargs)
    if remember_message:
        await remember_message(sent.message_id)
    return sent


async def edit(
    message: Message,
    text: str,
    remember_message: Callable[[int], Awaitable[None]] | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
    **kwargs: Any,
) -> Message:
    """Редактирует сообщение и запоминает новый ID."""
    edited = await message.edit_text(text, reply_markup=reply_markup, **kwargs)
    if remember_message and isinstance(edited, Message):
        await remember_message(edited.message_id)
    return edited
