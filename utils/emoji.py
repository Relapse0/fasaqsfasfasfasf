"""Единая палитра эмодзи — источник истины для всего интерфейса.

Правило: НИКОГДА не пишем эмодзи в хендлерах напрямую — только отсюда,
чтобы стиль оставался целостным во всех модулях.
"""
from __future__ import annotations

# ── Ядро ───────────────────────────────────────────────
HEART = "❤️"
SPARKLES = "✨"
FIRE = "🔥"
COUPLE = "💑"
HOME = "🏠"

# ── Навигация ──────────────────────────────────────────
BACK = "◀️"
NEXT = "▶️"
MENU = "🏠"
SETTINGS = "⚙️"
CHECK = "✅"
CROSS = "❌"
PLUS = "➕"
EDIT = "✏️"

# ── Модули ─────────────────────────────────────────────
BELL = "🔔"
CART = "🛒"
WALLET = "💳"
CHART = "📊"
MOOD = "🌤️"
CALENDAR = "📅"
GIFT = "🎁"
GAME = "🎮"
STAR = "⭐"
TROPHY = "🏆"
LOCK = "🔒"
UNLOCK = "🔓"
CLOCK = "⏰"
HOURGLASS = "⏳"
PHOTO = "🖼️"
CAMERA = "📷"
LETTER = "💌"
BOOK = "📖"
TARGET = "🎯"
COINS = "🪙"
SECRET = "🤫"
QUESTION = "❓"
DICE = "🎲"
CAPSULE = "🕰️"
SCROLL = "📜"
GRAPH_UP = "📈"
GRAPH_DOWN = "📉"
PARTY = "🎉"
PIN = "📍"
ROBOT = "🤖"
WARNING = "⚠️"
INFO = "ℹ️"
LINK = "🔗"

# ── Настроение (1..5) ──────────────────────────────────
MOOD_SCALE = {
    1: "😞",
    2: "😕",
    3: "😐",
    4: "🙂",
    5: "😍",
}

# ── Категории трат ─────────────────────────────────────
CATEGORY_EMOJI = {
    "food": "🍕",
    "transport": "🚕",
    "home": "🏠",
    "health": "💊",
    "fun": "🎬",
    "gifts": "🎁",
    "travel": "✈️",
    "other": "🧾",
}

# ── Уровни (геймификация) ──────────────────────────────
LEVEL_EMOJI = ["🌱", "🌿", "🌳", "💎", "👑", "🌟", "🚀", "🌈"]


def mood(m: int) -> str:
    """Эмодзи настроения с безопасным дефолтом."""
    return MOOD_SCALE.get(m, MOOD_SCALE[3])


def category(cat: str) -> str:
    return CATEGORY_EMOJI.get(cat, CATEGORY_EMOJI["other"])


def level(n: int) -> str:
    return LEVEL_EMOJI[min(n, len(LEVEL_EMOJI) - 1)]
