"""Адаптивное главное меню и маршрутизация между модулями.

Reply-кнопки главного меню маппятся на ``show_menu`` соответствующего
модуля; сам модуль отвечает инлайн-клавиатурой (edit-in-place).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards.main_menu import MODULES, build_main_menu
from utils import emoji as e

router = Router(name="menu")

# Маппинг «код модуля -> функция показа меню» (заполняется импортами)
from handlers import achievements as achievements_mod  # noqa: E402
from handlers import analytics as analytics_mod  # noqa: E402
from handlers import budget as budget_mod  # noqa: E402
from handlers import dates as dates_mod  # noqa: E402
from handlers import games as games_mod  # noqa: E402
from handlers import gratitude as gratitude_mod  # noqa: E402
from handlers import memories as memories_mod  # noqa: E402
from handlers import mood as mood_mod  # noqa: E402
from handlers import reminders as reminders_mod  # noqa: E402
from handlers import romance as romance_mod  # noqa: E402
from handlers import settings as settings_mod  # noqa: E402
from handlers import shopping as shopping_mod  # noqa: E402

MODULE_ROUTERS = {
    "reminders": reminders_mod.show_menu,
    "shopping": shopping_mod.show_menu,
    "budget": budget_mod.show_menu,
    "mood": mood_mod.show_menu,
    "dates": dates_mod.show_menu,
    "gratitude": gratitude_mod.show_menu,
    "romance": romance_mod.show_menu,
    "analytics": analytics_mod.show_menu,
    "memories": memories_mod.show_menu,
    "games": games_mod.show_menu,
    "achievements": achievements_mod.show_menu,
    "settings": settings_mod.show_menu,
}


@router.message(Command("menu"))
async def cmd_menu(message: Message, couple, settings) -> None:
    """Показывает главное Reply-меню."""
    kb = build_main_menu(couple.settings if couple else None, paired=couple is not None)
    await message.answer(f"{e.HOME} Главное меню", reply_markup=kb)


@router.callback_query(F.data == "menu:main")
async def cb_menu_main(callback: CallbackQuery, couple, settings) -> None:
    kb = build_main_menu(couple.settings if couple else None, paired=couple is not None)
    await callback.message.answer(f"{e.HOME} Главное меню", reply_markup=kb)
    await callback.answer()


@router.message(F.text.in_(list(MODULES.values())))
async def route_module(message: Message, session, user, couple, settings, language: str) -> None:
    """Направляет нажатие Reply-кнопки в соответствующий модуль."""
    for code, label in MODULES.items():
        if message.text == label:
            func = MODULE_ROUTERS.get(code)
            if func is not None:
                await func(
                    message,
                    session=session,
                    user=user,
                    couple=couple,
                    settings=settings,
                    language=language,
                )
            return
