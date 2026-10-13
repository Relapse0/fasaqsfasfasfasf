"""Годовой отчёт в стиле «Wrapped» (Pillow)."""
from __future__ import annotations

from PIL import Image, ImageDraw

from presentation.cards.base import (
    PALETTE,
    center_text,
    load_font,
    rounded,
    vertical_gradient,
)

W, H = 1080, 1350
M = 56


def render_wrapped_card(
    *,
    year: int,
    couple_name: str,
    days_together: int,
    facts: list[tuple[str, str]],  # (значение, подпись)
    top_category: str,
    out_path: str,
) -> str:
    img = vertical_gradient(W, H, PALETTE["bg"], PALETTE["bg2"]).convert("RGBA")
    d = ImageDraw.Draw(img)

    f_year = load_font(120, bold=True)
    f_title = load_font(48, bold=True)
    f_sub = load_font(28)
    f_fact_val = load_font(56, bold=True)
    f_fact_lbl = load_font(26)
    f_small = load_font(24)

    center_text(d, W // 2, 70, "Ваш год вместе", f_title, PALETTE["muted"])
    center_text(d, W // 2, 150, str(year), f_year, PALETTE["accent"])
    center_text(d, W // 2, 300, couple_name, f_title, PALETTE["text"])
    center_text(d, W // 2, 372, f"{days_together} дней вместе", f_sub, PALETTE["muted"])

    # Факты (сетка 1×2)
    y = 460
    for i, (value, label) in enumerate(facts[:4]):
        row, col = divmod(i, 2)
        tile_w = (W - 2 * M - 24) // 2
        tile_h = 160
        tx = M + col * (tile_w + 24)
        ty = y + row * (tile_h + 24)
        rounded(d, [tx, ty, tx + tile_w, ty + tile_h], 24, PALETTE["card"])
        d.text((tx + 28, ty + 30), value, font=f_fact_val, fill=PALETTE["accent2"])
        d.text((tx + 28, ty + 104), label, font=f_fact_lbl, fill=PALETTE["muted"])

    # Топ категория
    ty2 = y + 2 * (160 + 24) + 40
    rounded(d, [M, ty2, W - M, ty2 + 130], 28, PALETTE["card"])
    d.text((M + 30, ty2 + 30), "Любимая категория", font=f_sub, fill=PALETTE["muted"])
    d.text((M + 30, ty2 + 70), top_category, font=f_title, fill=PALETTE["text"])

    center_text(d, W // 2, H - 78, "сделано с ❤️", f_small, PALETTE["muted"])
    img.convert("RGB").save(out_path, "PNG")
    return out_path
