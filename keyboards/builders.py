"""Билдеры инлайн-клавиатур: пагинация и сетка кнопок."""
from __future__ import annotations

from collections.abc import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import emoji as e


def grid(
    buttons: Iterable[InlineKeyboardButton], *, row_width: int = 2
) -> InlineKeyboardMarkup:
    """Раскладывает кнопки сеткой по row_width в ряд."""
    btns = list(buttons)
    rows = [btns[i : i + row_width] for i in range(0, len(btns), row_width)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def paginate(
    *,
    page: int,
    total: int,
    page_size: int,
    prefix: str,
    extra: InlineKeyboardButton | None = None,
) -> InlineKeyboardMarkup:
    """Универсальная пагинация: «◀️ 2/5 ▶️» + опциональная доп. кнопка."""
    pages = max(1, (total + page_size - 1) // page_size)
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(text=f"{e.BACK}", callback_data=f"{prefix}:page:{page - 1}")
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{pages}", callback_data="noop"
        )
    )
    if page + 1 < pages:
        nav.append(
            InlineKeyboardButton(text=f"{e.NEXT}", callback_data=f"{prefix}:page:{page + 1}")
        )

    rows: list[list[InlineKeyboardButton]] = [nav]
    if extra is not None:
        rows.append([extra])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def inline(text: str, callback_data: str, style: str | None = None) -> InlineKeyboardButton:
    """Сокращённый конструктор кнопки."""
    return InlineKeyboardButton(text=text, callback_data=callback_data, style=style)
