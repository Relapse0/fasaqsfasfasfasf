"""График настроения (matplotlib, тёмная тема).

Строит сглаженные линии настроения для одного или двух партнёров.
"""
from __future__ import annotations

from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.dates import DateFormatter  # noqa: E402

from presentation.cards.base import PALETTE  # noqa: E402


def render_mood_chart(
    *,
    series: dict[str, list[tuple[datetime, int]]],  # имя -> [(дата, 1..5)]
    out_path: str,
    width: int = 1000,
    height: int = 560,
) -> str:
    """series: словарь «имя партнёра» -> точки (datetime, mood)."""
    bg = tuple(c / 255 for c in PALETTE["bg"])
    text_c = tuple(c / 255 for c in PALETTE["text"])
    muted_c = tuple(c / 255 for c in PALETTE["muted"])
    accent = tuple(c / 255 for c in PALETTE["accent"])
    accent2 = tuple(c / 255 for c in PALETTE["accent2"])
    grid_c = tuple(c / 255 for c in PALETTE["line"])

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    colors = [accent, accent2]
    for i, (name, points) in enumerate(series.items()):
        if not points:
            continue
        points = sorted(points, key=lambda p: p[0])
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        color = colors[i % len(colors)]
        ax.plot(xs, ys, marker="o", linewidth=3, color=color, label=name, markersize=8)
        # Лёгкая заливка под линией
        ax.fill_between(xs, ys, alpha=0.08, color=color)

    # Оси и сетка
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["😞", "😕", "😐", "🙂", "😍"], fontsize=16)
    ax.grid(axis="y", color=grid_c, linewidth=0.6, alpha=0.5)
    ax.tick_params(colors=muted_c, labelsize=12)
    ax.xaxis.set_major_formatter(DateFormatter("%d.%m"))
    for spine in ax.spines.values():
        spine.set_color(grid_c)

    ax.legend(loc="upper right", facecolor=PALETTE["card"], edgecolor="none",
              labelcolor=text_c, fontsize=12)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return out_path
