"""Базовые примитивы для генерации PNG-карточек.

Единая палитра и типографика — источник целостного визуального стиля.
Карточки тёмные (читаются и на светлом, и на тёмном фоне Telegram).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # безголовый бэкенд, до импорта pyplot
from matplotlib import font_manager  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

# ── Палитра ──────────────────────────────────────────────
PALETTE = {
    "bg": (24, 28, 36),          # фон
    "bg2": (30, 36, 46),         # фон (градиент к низу)
    "card": (36, 42, 54),        # подложка-карточка
    "accent": (255, 94, 131),    # розовый акцент
    "accent2": (255, 176, 71),   # янтарный
    "text": (245, 246, 250),     # основной текст
    "muted": (150, 158, 175),    # приглушённый
    "success": (94, 211, 128),
    "danger": (255, 99, 99),
    "line": (60, 68, 86),
}

ASSETS = Path(__file__).resolve().parents[2] / "assets"
FONTS_DIR = ASSETS / "fonts"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Шрифт: сначала кастомный из assets/fonts, затем DejaVuSans из matplotlib."""
    names = (
        ["Inter-Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["Inter-Regular.ttf", "DejaVuSans.ttf"]
    )
    for name in names:
        path = FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)

    # Fallback: DejaVuSans, который поставляется вместе с matplotlib
    try:
        path = font_manager.findfont("DejaVu Sans", fallback_to_default=True)
        return ImageFont.truetype(path, size)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default(size)


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    """Вертикальный градиентный фон."""
    base = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        base.putpixel((0, y), color)
    return base.resize((width, height), Image.Resampling.NEAREST)


def rounded(draw: ImageDraw.ImageDraw, box: list[int], radius: int, fill: tuple) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def circle_avatar(size: int, initials: str, bg: tuple, fg: tuple, font) -> Image.Image:
    """Круглый аватар с инициалами."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, size - 1, size - 1], fill=bg)
    d.text((size / 2, size / 2), initials, font=font, fill=fg, anchor="mm")
    return img


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Перенос текста по словам под заданную ширину."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def center_text(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str, font, fill) -> None:
    """Текст, отцентрированный по горизонтали относительно cx."""
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def bar(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    ratio: float,
    fill: tuple,
    track: tuple,
) -> None:
    """Горизонтальный прогресс-бар (заполнение ratio 0..1)."""
    rounded(draw, [x, y, x + w, y + h], radius=h // 2, fill=track)
    fill_w = max(h, int(w * ratio))
    rounded(draw, [x, y, x + fill_w, y + h], radius=h // 2, fill=fill)
