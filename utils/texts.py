"""Тексты и i18n.

Лёгкая схема «словарь на язык + интерполяция». Русский — основной,
английский — задел на будущее (структура уже готова к расширению).
"""
from __future__ import annotations

from utils.emoji import BACK, MENU, SETTINGS, SPARKLES, STAR, WARNING

RU = {
    "menu.main": "🏠 Главное меню",
    "menu.settings": "⚙️ Настройки",
    "back": "◀️ Назад",
    "cancel": "❌ Отмена",
    "hello.couple": (
        "Привет, {name}!\n\n"
        "Это ваша личная операционная система для двоих. "
        "Здесь можно планировать, считать бюджет, делиться настроением "
        "и беречь воспоминания — всё в одном месте."
    ),
    "hello.single": (
        "Привет, {name}! {sparkles}\n\n"
        "Я — бот для пар: бюджет, напоминания, настроение, даты и воспоминания.\n\n"
        "Чтобы начать, пригласи партнёра по коду или deep-link."
    ),
    "not.paired": "Вы пока не в паре. Используйте /start или меню, чтобы привязаться.",
    "err.unknown": "Что-то пошло не так. Попробуйте ещё раз.",
    "err.permission": "Это действие доступно только в личном чате с ботом.",
    "loading": "⏳ Считаю...",
    "choose.action": "Выберите действие:",
}

EN = {
    "menu.main": "🏠 Main menu",
    "menu.settings": "⚙️ Settings",
    "back": "◀️ Back",
    "cancel": "❌ Cancel",
    "hello.couple": "Hi {name}!\n\nThis is your personal OS for two.",
    "hello.single": "Hi {name}! {sparkles}\n\nI'm a bot for couples.",
    "not.paired": "You're not paired yet.",
    "err.unknown": "Something went wrong. Try again.",
    "loading": "⏳ Calculating...",
    "choose.action": "Choose an action:",
}

DICTS = {"ru": RU, "en": EN}


def t(language: str, key: str, **fmt) -> str:
    """Перевод с интерполяцией. Неизвестный ключ возвращается как есть."""
    table = DICTS.get(language, RU)
    text = table.get(key) or RU.get(key) or key
    if fmt:
        text = text.format(**fmt)
    return text


# ── Общие кнопки меню (эмодзи отсюда) ───────────────────
MAIN_MENU_LABEL = "🏠 Меню"
SETTINGS_LABEL = f"{SETTINGS} Настройки"
BACK_LABEL = f"{BACK} Назад"
