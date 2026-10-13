"""Модуль «Статистика»: карточка пары, график, Wrapped, экспорт."""
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.analytics_service import AnalyticsService
from services.card_service import CardService
from utils import emoji as e

router = Router(name="analytics")


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.STAR} Карточка пары", callback_data="analytics:stats", style="primary")],
            [InlineKeyboardButton(text=f"{e.CHART} График настроения", callback_data="analytics:mood")],
            [InlineKeyboardButton(text=f"{e.PARTY} Годовой Wrapped", callback_data="analytics:wrapped")],
            [InlineKeyboardButton(text=f"{e.SCROLL} Экспорт CSV", callback_data="analytics:csv")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.CHART} <b>Статистика</b>\n\nЧто показать?", reply_markup=kb)


@router.callback_query(F.data == "analytics:stats")
async def analytics_stats(callback: CallbackQuery, session, couple) -> None:
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().stats_card(session, couple)
    await callback.message.answer_photo(FSInputFile(path), caption=f"{e.SPARKLES} Ваша пара в цифрах")
    await callback.answer()


@router.callback_query(F.data == "analytics:mood")
async def analytics_mood(callback: CallbackQuery, session, couple) -> None:
    await callback.message.answer_chat_action("upload_photo")
    path = await CardService().mood_chart(session, couple)
    await callback.message.answer_photo(FSInputFile(path), caption=f"{e.CHART} Настроение")
    await callback.answer()


@router.callback_query(F.data == "analytics:wrapped")
async def analytics_wrapped(callback: CallbackQuery, session, couple) -> None:
    year = datetime.now(timezone.utc).year
    await callback.message.answer_chat_action("upload_photo")
    card = CardService()
    path, _ = await card.wrapped_card(session, couple, year)
    text = await AnalyticsService(session).wrapped_text(couple, year)
    await callback.message.answer_photo(FSInputFile(path), caption=text)
    await callback.answer()


@router.callback_query(F.data == "analytics:csv")
async def analytics_csv(callback: CallbackQuery, session, couple) -> None:
    buf = await AnalyticsService(session).export_transactions_csv(couple.couple_id)
    await callback.message.answer_document(
        BufferedInputFile(buf.getvalue(), filename="transactions.csv"),
        caption=f"{e.SCROLL} Экспорт трат",
    )
    await callback.answer()
