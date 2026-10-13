"""Модуль «Настроение»: опрос, запись, алерт партнёру, график."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.repositories.moods import MoodsRepository
from keyboards.inline import mood_keyboard
from services.card_service import CardService
from services.mood_service import MoodService, mood_alert_text
from utils import emoji as e

router = Router(name="mood")


class MoodStates(StatesGroup):
    comment = State()


# ── Меню модуля ──────────────────────────────────────────
async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.MOOD} Отметить настроение", callback_data="mood:ask", style="primary")],
            [InlineKeyboardButton(text=f"{e.CHART} График за неделю", callback_data="mood:chart")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(
        f"{e.MOOD} <b>Настроение</b>\n\nКак ты себя чувствуешь сегодня?",
        reply_markup=kb,
    )


@router.callback_query(F.data == "mood:ask")
async def mood_ask(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        f"{e.MOOD} Как твоё настроение?",
        reply_markup=mood_keyboard(),
    )
    await callback.answer()


# ── Запись настроения (инлайн) ───────────────────────────
@router.callback_query(F.data.startswith("mood:"))
async def mood_choose(callback: CallbackQuery, session, user, couple) -> None:
    value = callback.data.split(":")[1]
    if value == "skip":
        await callback.message.edit_text(f"{e.INFO} Ок, пропускаем 🙂")
        await callback.answer()
        return
    if value == "chart":
        await _mood_chart(callback, session, couple)
        return

    mood_val = int(value)
    service = MoodService(session)
    record, partner = await service.save_mood(
        user, couple, mood_val, comment=None
    )
    await session.flush()

    await callback.message.edit_text(
        f"{e.mood(mood_val)} Записал! Настроение: <b>{mood_val}/5</b>",
        reply_markup=None,
    )

    # Алерт партнёру при 3 днях ≤ 2 подряд
    if partner is not None:
        await callback.message.bot.send_message(partner.user_id, mood_alert_text(user))
    await callback.answer()


async def _mood_chart(callback: CallbackQuery, session, couple) -> None:
    if couple is None:
        await callback.message.edit_text("Сначала создайте пару 👉 /start")
        return
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().mood_chart(session, couple)
    from aiogram.types import FSInputFile

    await callback.message.answer_photo(
        FSInputFile(path),
        caption=f"{e.CHART} Настроение за последние 30 отметок",
    )
