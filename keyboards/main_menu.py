"""Адаптивное главное меню (ReplyKeyboard).

Собирается из настроек пары: показываются только включённые модули.
2 кнопки в ряд, всего 8 ячеек.
"""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from utils import emoji as e

# Порядок модулей в меню и их эмодзи
MODULES: dict[str, str] = {
    "reminders": f"{e.BELL} Напоминания",
    "shopping": f"{e.CART} Покупки",
    "budget": f"{e.WALLET} Бюджет",
    "mood": f"{e.MOOD} Настроение",
    "dates": f"{e.CALENDAR} Даты",
    "gratitude": f"{e.LETTER} Спасибо",
    "romance": f"{e.FIRE} Романтика",
    "analytics": f"{e.CHART} Статистика",
    "memories": f"{e.PHOTO} Воспоминания",
    "games": f"{e.GAME} Игры",
    "achievements": f"{e.TROPHY} Уровни",
    "settings": f"{e.SETTINGS} Настройки",
}

# Всегда видимые служебные кнопки
ALWAYS_VISIBLE = ("settings",)


def build_main_menu(settings: dict | None, *, paired: bool = True) -> ReplyKeyboardMarkup:
    """Собирает Reply-меню из активных модулей.

    settings — словарь ``couple.settings`` (None для не привязанного пользователя).
    """
    modules: dict = (settings or {}).get("modules", {})
    active: list[str] = []

    # Сначала служебные модули, затем остальные в заданном порядке
    for code, label in MODULES.items():
        if code in ALWAYS_VISIBLE or modules.get(code, True):
            active.append(label)

    # Для не привязанного пользователя показываем только настройки
    if not paired:
        active = [MODULES["settings"]]

    # Раскладываем по 2 в ряд
    rows = [active[i : i + 2] for i in range(0, len(active), 2)]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in rows],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел",
    )
    return keyboard
