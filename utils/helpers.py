"""Хелперы общего назначения: форматирование, прогресс-бары, время."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.relativedelta import relativedelta


def now_tz(timezone: str) -> datetime:
    """Текущее время в указанном часовом поясе."""
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def safe_tz(timezone: str) -> ZoneInfo:
    """Возвращает ZoneInfo с фолбэком на UTC."""
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def progress_bar(percent: float, length: int = 10) -> str:
    """Текстовый прогресс-бар: ▰▰▰▱▱▱▱▱ 30%."""
    percent = max(0.0, min(100.0, percent))
    filled = round(percent / 100 * length)
    return f"{'▰' * filled}{'▱' * (length - filled)} {int(percent)}%"


def plural(n: int, forms: tuple[str, str, str]) -> str:
    """Русская плюрализация: plural(3, ("день", "дня", "дней"))."""
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return forms[1]
    return forms[2]


def days_between(start: datetime, end: datetime | None = None) -> int:
    """Число полных дней между датами (для «дней вместе»)."""
    end = end or now_tz("UTC")
    return max(0, (end.date() - start.date()).days)


def next_occurrence(remind_at: datetime, repeat_rule: str) -> datetime:
    """Следующая дата срабатывания для повторяющегося напоминания.

    repeat_rule: ``daily`` | ``weekly`` | ``monthly``.
    """
    if repeat_rule == "daily":
        return remind_at + relativedelta(days=1)
    if repeat_rule == "weekly":
        return remind_at + relativedelta(weeks=1)
    if repeat_rule == "monthly":
        return remind_at + relativedelta(months=1)
    return remind_at


def human_date(dt: datetime, timezone: str | None = None) -> str:
    """Читаемая дата: «14 февраля 2025, 21:00»."""
    if timezone:
        dt = dt.astimezone(safe_tz(timezone))
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    ]
    return f"{dt.day} {months[dt.month - 1]} {dt.year}, {dt:%H:%M}"


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
