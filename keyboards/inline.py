"""Готовые инлайн-клавиатуры для модулей.

Все кнопки используют цветовые стили Bot API 9.x:
``primary`` — основное действие, ``success`` — подтверждение,
``danger`` — отмена/удаление.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import emoji as e

# ── Callback-префиксы (см. handlers) ────────────────────
CB = {
    "menu": "menu",
    "back": "back",
    "cancel": "cancel",
    "mood": "mood",
    "reminder": "rem",
    "shopping": "shop",
    "budget": "budget",
    "dates": "dates",
    "challenge": "challenge",
    "gratitude": "gratitude",
    "capsule": "capsule",
    "memory": "memory",
    "quiz": "quiz",
    "settings": "settings",
    "analytics": "analytics",
}


def _btn(text: str, callback_data: str, style: str | None = None) -> InlineKeyboardButton:
    """Создаёт инлайн-кнопку со стилем (если передан)."""
    return InlineKeyboardButton(text=text, callback_data=callback_data, style=style)


def back_row(callback: str = "menu:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn(f"{e.BACK} Назад", callback)]])


def mood_keyboard(prefix: str = CB["mood"]) -> InlineKeyboardMarkup:
    """Клавиатура опроса настроения (1..5)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(f"{e.mood(1)} 1", f"{prefix}:1"),
                _btn(f"{e.mood(2)} 2", f"{prefix}:2"),
                _btn(f"{e.mood(3)} 3", f"{prefix}:3"),
                _btn(f"{e.mood(4)} 4", f"{prefix}:4"),
                _btn(f"{e.mood(5)} 5", f"{prefix}:5"),
            ],
            [_btn(f"{e.CROSS} Пропустить", f"{prefix}:skip", "danger")],
        ]
    )


def confirm_keyboard(
    confirm_cb: str, cancel_cb: str = "cancel", confirm_text: str = "Да"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn(f"{e.CHECK} {confirm_text}", confirm_cb, "success"),
                _btn(f"{e.CROSS} Отмена", cancel_cb, "danger"),
            ]
        ]
    )
