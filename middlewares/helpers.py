"""Общие хелперы для мидлварей."""
from __future__ import annotations

from aiogram.types import TelegramObject, User

# Атрибуты объекта Update, внутри которых лежит from_user
_USER_EVENT_ATTRS = (
    "message",
    "edited_message",
    "callback_query",
    "inline_query",
    "chosen_inline_result",
)


def extract_user(event: TelegramObject) -> User | None:
    """Достаёт Telegram-User из Update (или напрямую из события).

    Мидлвари зарегистрированы на ``dp.update``, поэтому получают объект
    ``Update``, у которого нет собственного ``from_user`` — пользователь
    лежит внутри ``update.message`` / ``update.callback_query`` и т.п.
    """
    tg_user = getattr(event, "from_user", None)
    if tg_user is not None:
        return tg_user

    for attr in _USER_EVENT_ATTRS:
        nested = getattr(event, attr, None)
        if nested is not None:
            tg_user = getattr(nested, "from_user", None)
            if tg_user is not None:
                return tg_user
    return None
