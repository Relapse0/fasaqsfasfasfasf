"""Модуль «Уровни»: очки, уровень, достижения, прогресс."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.gamification_service import GamificationService
from utils import emoji as e
from utils.helpers import progress_bar

router = Router(name="achievements")


async def show_menu(message: Message, session, user, couple, settings, language: str) -> None:
    if couple is None:
        await message.answer("Сначала создайте пару 👉 /start")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.TROPHY} Достижения", callback_data="ach:list", style="primary")],
            [InlineKeyboardButton(text=f"{e.COINS} Баланс очков", callback_data="ach:balance")],
            [InlineKeyboardButton(text=f"{e.HOME} В меню", callback_data="menu:main")],
        ]
    )
    await message.answer(f"{e.TROPHY} <b>Уровни пары</b>\n\nВыберите:", reply_markup=kb)


@router.callback_query(F.data == "ach:balance")
async def ach_balance(callback: CallbackQuery, session, couple) -> None:
    svc = GamificationService(session)
    points = await svc.balance(couple.couple_id)
    level, in_level, _ = await svc.level(couple.couple_id)
    bar = progress_bar(in_level, length=10)
    await callback.message.edit_text(
        f"{e.level(level)} <b>Уровень {level}</b>\n\n"
        f"Очков: <b>{points}</b>\n"
        f"До следующего уровня: {bar}"
    )
    await callback.answer()


@router.callback_query(F.data == "ach:list")
async def ach_list(callback: CallbackQuery, session, couple) -> None:
    svc = GamificationService(session)
    items = await svc.list_achievements(couple.couple_id)
    lines = [f"{e.TROPHY} <b>Достижения</b>\n"]
    for it in items:
        icon = "✅" if it["unlocked"] else "🔒"
        lines.append(f"{icon} <b>{it['title']}</b> — {it['desc']}")
    await callback.message.edit_text("\n".join(lines))
    await callback.answer()
