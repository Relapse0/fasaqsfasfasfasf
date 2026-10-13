"""Карточка профиля пары (Pillow). Формат 1080×1080."""
from __future__ import annotations

from PIL import Image, ImageDraw

from presentation.cards.base import (
    PALETTE,
    center_text,
    circle_avatar,
    load_font,
    rounded,
    vertical_gradient,
)
from presentation.cards.stats_card import initials, short

W = H = 1080


def render_profile_card(
    *,
    couple_name: str,
    user1_name: str,
    user2_name: str,
    days_together: int,
    invite_code: str,
    active_modules: int,
    total_modules: int,
    out_path: str,
) -> str:
    img = vertical_gradient(W, H, PALETTE["bg"], PALETTE["bg2"]).convert("RGBA")
    d = ImageDraw.Draw(img)

    f_title = load_font(64, bold=True)
    f_sub = load_font(32)
    f_avatar = load_font(68, bold=True)
    f_name = load_font(38, bold=True)
    f_big = load_font(88, bold=True)
    f_small = load_font(26)

    center_text(d, W // 2, 80, couple_name, f_title, PALETTE["text"])
    center_text(d, W // 2, 176, f"Вместе {days_together} дней", f_sub, PALETTE["muted"])

    # Аватары
    size = 180
    gap = 56
    total = size * 2 + gap
    x1 = (W - total) // 2
    x2 = x1 + size + gap
    cy = 300
    av1 = circle_avatar(size, initials(user1_name), PALETTE["accent"], PALETTE["text"], f_avatar)
    av2 = circle_avatar(size, initials(user2_name), PALETTE["accent2"], PALETTE["text"], f_avatar)
    img.paste(av1, (x1, cy - size // 2), av1)
    img.paste(av2, (x2, cy - size // 2), av2)
    center_text(d, x1 + size // 2, cy + size // 2 + 20, short(user1_name), f_name, PALETTE["text"])
    center_text(d, x2 + size // 2, cy + size // 2 + 20, short(user2_name), f_name, PALETTE["text"])

    # Модули
    mod_y = 520
    rounded(d, [64, mod_y, W - 64, mod_y + 150], 28, PALETTE["card"])
    d.text((108, mod_y + 34), f"Модули {active_modules}/{total_modules}", font=f_sub, fill=PALETTE["muted"])
    mod_ratio = active_modules / max(1, total_modules)
    from presentation.cards.base import bar

    bar(d, 108, mod_y + 88, W - 216, 18, mod_ratio, PALETTE["accent"], PALETTE["line"])

    # Код приглашения
    code_y = 720
    rounded(d, [64, code_y, W - 64, code_y + 180], 28, PALETTE["card"])
    d.text((108, code_y + 40), "Код приглашения", font=f_sub, fill=PALETTE["muted"])
    center_text(d, W // 2, code_y + 96, invite_code, f_big, PALETTE["accent2"])

    center_text(d, W // 2, H - 76, "сделано с ❤️", f_small, PALETTE["muted"])

    img.convert("RGB").save(out_path, "PNG")
    return out_path
