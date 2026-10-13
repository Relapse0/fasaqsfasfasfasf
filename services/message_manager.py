"""Сервис управления активным сообщением бота в чате.

Хранит ID последнего сообщения в FSM-хранилище (Redis/память).
При отправке нового — деактивирует предыдущее (удаляет или снимает кнопки).
Важные сообщения (напоминания, карточки) помечаются флагом pinned=True и не трогаются.
"""
from __future__ import annotations

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, ReplyKeyboardMarkup

# Ключ в FSM-хранилище для ID последнего сообщения бота
_FSM_KEY = "__last_bot_msg__"


class MessageManager:
    """Отправляет сообщения и управляет активным экраном бота."""

    def __init__(self, bot: Bot, state: FSMContext) -> None:
        self.bot = bot
        self.state = state

    async def send(
        self,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        pinned: bool = False,
        deactivate: str = "remove_kb",  # режим: "delete" | "remove_kb" | "none"
        **kwargs,
    ) -> Message:
        """Отправляет новое сообщение, деактивируя предыдущее.

        Args:
            chat_id:      ID чата.
            text:         Текст сообщения.
            reply_markup: Клавиатура (необязательно).
            pinned:       True = не удалять при следующем переходе.
            deactivate:   Что делать с предыдущим сообщением:
                          - "remove_kb": убрать кнопки (рекомендуется)
                          - "delete":    удалить сообщение
                          - "none":      оставить как есть
        """
        await self._deactivate_previous(chat_id, mode=deactivate)

        sent = await self.bot.send_message(
            chat_id, text, reply_markup=reply_markup, **kwargs
        )

        if not pinned:
            await self._remember(sent.message_id)

        return sent

    async def edit(
        self,
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
        pinned: bool = False,
        **kwargs,
    ) -> Message:
        """Редактирует существующее сообщение и обновляет ID в FSM."""
        edited = await message.edit_text(text, reply_markup=reply_markup, **kwargs)
        if not pinned and isinstance(edited, Message):
            await self._remember(edited.message_id)
        return edited

    async def _remember(self, message_id: int) -> None:
        """Запоминает ID сообщения в FSM."""
        data = await self.state.get_data()
        data[_FSM_KEY] = message_id
        await self.state.set_data(data)

    async def _deactivate_previous(self, chat_id: int, mode: str) -> None:
        """Деактивирует предыдущее активное сообщение."""
        if mode == "none":
            return

        data = await self.state.get_data()
        last_id: int | None = data.get(_FSM_KEY)
        if not last_id:
            return

        try:
            if mode == "delete":
                await self.bot.delete_message(chat_id, last_id)
            elif mode == "remove_kb":
                await self.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=last_id,
                    reply_markup=None,
                )
        except Exception:  # noqa: BLE001
            pass  # Уже удалено или слишком старое — не критично

        data.pop(_FSM_KEY, None)
        await self.state.set_data(data)

    @classmethod
    def from_handler(cls, bot: Bot, state: FSMContext) -> "MessageManager":
        """Удобный фабричный метод для создания в хендлерах."""
        return cls(bot=bot, state=state)
