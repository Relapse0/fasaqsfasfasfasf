"""Валидация пользовательского ввода."""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")
DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?$")


def parse_time(text: str) -> tuple[int, int] | None:
    """'21:00' -> (21, 0) или None."""
    m = TIME_RE.match(text.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return h, mi


def parse_date(text: str, year: int | None = None) -> datetime | None:
    """'14.02' или '14.02.2024' -> datetime (год по умолчанию текущий)."""
    m = DATE_RE.match(text.strip())
    if not m:
        return None
    day, month = int(m.group(1)), int(m.group(2))
    y = int(m.group(3)) if m.group(3) else (year or datetime.now().year)
    try:
        return datetime(y, month, day)
    except ValueError:
        return None


def parse_amount(text: str) -> Decimal | None:
    """'123.45' / '1 234,5' -> Decimal или None."""
    cleaned = text.replace(" ", "").replace(",", ".").replace("₽", "").replace("$", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def is_valid_timezone(tz: str) -> bool:
    try:
        ZoneInfo(tz)
        return True
    except ZoneInfoNotFoundError:
        return False


def mood_value(text: str) -> int | None:
    """Парсит оценку настроения 1..5 из строки."""
    try:
        v = int(text.strip())
    except ValueError:
        return None
    return v if 1 <= v <= 5 else None
