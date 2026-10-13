"""Карточка статистики пары (Pillow).

Собирает «витрину» пары: дни вместе, аватары, ключевые метрики,
топ категорий трат и график активности за 14 дней. Формат 1080×1350 (4:5).
"""
from __future__ import annotations

from datetime import datetime

from PIL import Image, ImageDraw

from presentation.cards.base import (
    PALETTE,
    bar,
    center_text,
    circle_avatar,
    load_font,
    rounded,
    vertical_gradient,
    wrap_text,
)

W, H = 1080, 1350
M = 52  # внешний отступ


def render_stats_card(
    *,
    couple_name: str,
    days_together: int,
    user1_name: str,
    user2_name: str,
    points: int,
    stats: dict,                     # {"transactions", "moods", "memories"}
    top_categories: list[tuple[str, float]],  # (метка, сумма)
    activity: list[int],             # 14 значений активности по дням
    out_path: str,
) -> str:
    bg = vertical_gradient(W, H, PALETTE["bg"], PALETTE["bg2"])
    img = bg.convert("RGBA")
    d = ImageDraw.Draw(img)

    f_title = load_font(56, bold=True)
    f_sub = load_font(30)
    f_avatar = load_font(64, bold=True)
    f_name = load_font(36, bold=True)
    f_value = load_font(52, bold=True)
    f_label = load_font(26)
    f_section = load_font(40, bold=True)
    f_small = load_font(24)

    # ── Шапка ─────────────────────────────────────────────
    center_text(d, W // 2, 72, couple_name, f_title, PALETTE["text"])
    center_text(d, W // 2, 156, f"{days_together} дней вместе", f_sub, PALETTE["muted"])

    # ── Аватары ───────────────────────────────────────────
    avatar_size = 168
    gap = 40
    total = avatar_size * 2 + gap
    x1 = (W - total) // 2
    x2 = x1 + avatar_size + gap
    cy = 250

    av1 = circle_avatar(
        avatar_size, initials(user1_name), PALETTE["accent"], PALETTE["text"], f_avatar
    )
    av2 = circle_avatar(
        avatar_size, initials(user2_name), PALETTE["accent2"], PALETTE["text"], f_avatar
    )
    img.paste(av1, (x1, cy - avatar_size // 2), av1)
    img.paste(av2, (x2, cy - avatar_size // 2), av2)

    center_text(d, x1 + avatar_size // 2, cy + avatar_size // 2 + 18, short(user1_name), f_name, PALETTE["text"])
    center_text(d, x2 + avatar_size // 2, cy + avatar_size // 2 + 18, short(user2_name), f_name, PALETTE["text"])

    # ── Плитки метрик (2×2) ───────────────────────────────
    tiles_y = 400
    tile_h = 150
    tile_gap = 20
    tile_w = (W - 2 * M - tile_gap) // 2
    tiles = [
        (str(stats.get("transactions", 0)), "трат"),
        (str(stats.get("moods", 0)), "отметок настроения"),
        (str(stats.get("memories", 0)), "воспоминаний"),
        (str(points), "очков пары"),
    ]
    for i, (value, label) in enumerate(tiles):
        row, col = divmod(i, 2)
        tx = M + col * (tile_w + tile_gap)
        ty = tiles_y + row * (tile_h + tile_gap)
        rounded(d, [tx, ty, tx + tile_w, ty + tile_h], 24, PALETTE["card"])
        d.text((tx + 30, ty + 26), value, font=f_value, fill=PALETTE["text"])
        d.text((tx + 30, ty + 94), label, font=f_label, fill=PALETTE["muted"])

    # ── Топ категорий ─────────────────────────────────────
    section_y = tiles_y + 2 * (tile_h + tile_gap) + 30
    d.text((M, section_y), "Топ категорий", font=f_section, fill=PALETTE["text"])
    by = section_y + 64
    max_amount = max((a for _, a in top_categories), default=1.0)
    for label, amount in top_categories[:4]:
        d.text((M, by), label, font=f_sub, fill=PALETTE["text"])
        amt_txt = f"{amount:,.0f} ₽" if amount >= 100 else f"{amount:.2f}"
        amt_w = d.textlength(amt_txt, font=f_small)
        d.text((W - M - amt_w, by + 4), amt_txt, font=f_small, fill=PALETTE["muted"])
        bar(d, M, by + 46, W - 2 * M, 16, amount / max_amount, PALETTE["accent"], PALETTE["line"])
        by += 96

    # ── Активность за 14 дней ─────────────────────────────
    act_y = by + 20
    d.text((M, act_y), "Активность · 14 дней", font=f_section, fill=PALETTE["text"])
    chart_top = act_y + 70
    chart_h = 120
    chart_bottom = chart_top + chart_h
    n = len(activity)
    if n > 0:
        slot_w = (W - 2 * M) / n
        bar_w = max(8, int(slot_w * 0.6))
        max_act = max(activity) or 1
        for i, cnt in enumerate(activity):
            bh = max(6, int(chart_h * cnt / max_act))
            cx = int(M + slot_w * i + (slot_w - bar_w) / 2)
            color = PALETTE["accent"] if i == n - 1 else PALETTE["accent2"]
            rounded(d, [cx, chart_bottom - bh, cx + bar_w, chart_bottom], radius=6, fill=color)
    else:
        d.text((M, chart_top), "Пока мало данных", font=f_sub, fill=PALETTE["muted"])

    # ── Подвал ────────────────────────────────────────────
    center_text(d, W // 2, H - 78, "сделано с ❤️", f_small, PALETTE["muted"])

    img = img.convert("RGB")
    img.save(out_path, "PNG")
    return out_path


def initials(name: str) -> str:
    """Инициалы: 'Анна Смирнова' -> 'АС'; 'Анна' -> 'А'."""
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    first = parts[0][0].upper()
    second = parts[1][0].upper() if len(parts) > 1 else ""
    return first + second


def short(name: str, limit: int = 14) -> str:
    """Короткое имя для подписи под аватаром."""
    name = name.strip() or "?"
    return name if len(name) <= limit else name[: limit - 1] + "…"
