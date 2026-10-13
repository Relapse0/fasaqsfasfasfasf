"""Карточка бюджета (Pillow): итоги месяца, топ категорий, лимит."""
from __future__ import annotations

from decimal import Decimal

from PIL import Image, ImageDraw

from presentation.cards.base import (
    PALETTE,
    bar,
    center_text,
    load_font,
    rounded,
    vertical_gradient,
)

W, H = 1080, 1350
M = 56


def render_budget_card(
    *,
    month_label: str,
    total_spent: Decimal,
    limit: Decimal | None,
    top_categories: list[tuple[str, Decimal]],
    out_path: str,
) -> str:
    img = vertical_gradient(W, H, PALETTE["bg"], PALETTE["bg2"]).convert("RGBA")
    d = ImageDraw.Draw(img)

    f_title = load_font(54, bold=True)
    f_big = load_font(84, bold=True)
    f_sub = load_font(30)
    f_section = load_font(40, bold=True)
    f_small = load_font(24)

    center_text(d, W // 2, 70, f"Бюджет · {month_label}", f_title, PALETTE["text"])

    # Итог месяца
    total_txt = f"{total_spent:,.0f} ₽"
    center_text(d, W // 2, 170, total_txt, f_big, PALETTE["accent"])
    center_text(d, W // 2, 280, "потрачено за месяц", f_sub, PALETTE["muted"])

    # Лимит
    ly = 340
    if limit and limit > 0:
        ratio = float(total_spent / limit)
        over = ratio > 1.0
        color = PALETTE["danger"] if over else PALETTE["success"]
        rounded(d, [M, ly, W - M, ly + 120], 28, PALETTE["card"])
        d.text((M + 30, ly + 26), f"Лимит {limit:,.0f} ₽", font=f_sub, fill=PALETTE["text"])
        pct_txt = f"{int(ratio * 100)}%"
        pct_w = d.textlength(pct_txt, font=f_small)
        d.text((W - M - 30 - pct_w, ly + 30), pct_txt, font=f_small, fill=color)
        bar(d, M + 30, ly + 72, W - 2 * (M + 30), 18, min(1.0, ratio), color, PALETTE["line"])

    # Топ категорий
    sec_y = 500
    d.text((M, sec_y), "Топ категорий", font=f_section, fill=PALETTE["text"])
    by = sec_y + 66
    max_amount = max((a for _, a in top_categories), default=Decimal(1))
    for label, amount in top_categories[:5]:
        d.text((M, by), label, font=f_sub, fill=PALETTE["text"])
        amt_txt = f"{amount:,.0f} ₽"
        amt_w = d.textlength(amt_txt, font=f_small)
        d.text((W - M - amt_w, by + 6), amt_txt, font=f_small, fill=PALETTE["muted"])
        ratio = float(amount / max_amount)
        bar(d, M, by + 46, W - 2 * M, 16, ratio, PALETTE["accent2"], PALETTE["line"])
        by += 98

    center_text(d, W // 2, H - 78, "сделано с ❤️", f_small, PALETTE["muted"])
    img.convert("RGB").save(out_path, "PNG")
    return out_path
