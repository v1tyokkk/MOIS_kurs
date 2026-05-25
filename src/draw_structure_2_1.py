#!/usr/bin/env python3
"""
Рисунок 2.1 — структурная схема программы waypoint_mission.
Запуск: python3 KURS/output/draw_structure_2_1.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    }
)

from paths import OUT, SHOTS, MISSION, DOC
OUT_DIR = OUT
OUT_PNG = OUT_DIR / "02_структурная_схема_2.1_A4.png"
OUT_SVG = OUT_DIR / "02_структурная_схема_2.1_A4.svg"
OUT_SCREEN = SHOTS / "2.1.png"

FIG = (11.69, 8.27)
DPI = 200
LW = 1.5


def _box(
    ax,
    xy,
    w,
    h,
    text: str,
    *,
    facecolor: str = "white",
    edgecolor: str = "#111",
    fontsize: float = 10,
    sub: str | None = None,
) -> tuple[float, float]:
    """Центр блока (cx, cy)."""
    x, y = xy
    rect = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=LW,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(rect)
    cx, cy = x + w / 2, y + h / 2
    if sub:
        ax.text(cx, cy + 0.12 * h, text, ha="center", va="center", fontsize=fontsize, fontweight="bold")
        ax.text(cx, cy - 0.18 * h, sub, ha="center", va="center", fontsize=fontsize - 1, color="#333")
    else:
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, fontweight="bold")
    return cx, cy


def _arrow(ax, p0, p1, text: str | None = None, style: str = "-|>", color: str = "#111") -> None:
    ax.add_patch(
        FancyArrowPatch(
            p0,
            p1,
            arrowstyle=style,
            mutation_scale=12,
            linewidth=LW,
            color=color,
            shrinkA=4,
            shrinkB=4,
            connectionstyle="arc3,rad=0.0",
        )
    )
    if text:
        mx = (p0[0] + p1[0]) / 2
        my = (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.12, text, ha="center", va="bottom", fontsize=8, color="#333")


def main() -> None:
    fig, ax = plt.subplots(figsize=FIG, dpi=DPI)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8.5)
    ax.axis("off")
    ax.set_facecolor("white")

    ax.text(
        6,
        8.15,
        "Рисунок 2.1 – Структурная схема программы",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )

    # Внешняя среда
    mur_c = _box(
        ax,
        (4.6, 6.85),
        2.8,
        0.75,
        "MUR IDE / pymurapi",
        facecolor="#f5f5f5",
        fontsize=11,
        sub="симулятор, телеметрия, моторы",
    )

    # Главный сценарий
    main_c = _box(
        ax,
        (3.2, 5.35),
        5.6,
        1.05,
        "waypoint_mission.py",
        facecolor="#e8f4fc",
        fontsize=12,
        sub="главный сценарий миссии",
    )

    _arrow(ax, (mur_c[0], mur_c[1] - 0.4), (main_c[0], main_c[1] + 0.55), "init / цикл 10 Гц")

    # Группа «чистые функции»
    ax.add_patch(
        Rectangle(
            (0.35, 0.55),
            7.0,
            3.55,
            linewidth=1.2,
            edgecolor="#666",
            linestyle="--",
            facecolor="#fafafa",
        )
    )
    ax.text(0.55, 3.95, "без обращения к симулятору (функции и классы)", fontsize=9, color="#555", va="top")

    wp_c = _box(ax, (0.55, 2.55), 2.05, 0.95, "waypoints.py", fontsize=9, sub="маршрут, схват")
    nav_c = _box(ax, (2.85, 2.55), 2.05, 0.95, "navigation.py", fontsize=9, sub="ψц, дистанция")
    ctl_c = _box(ax, (5.15, 2.55), 2.05, 0.95, "control.py", fontsize=9, sub="P-регуляторы")
    odo_c = _box(ax, (0.55, 0.85), 2.05, 0.95, "odometry.py", fontsize=9, sub="оценка X, Y")
    log_c = _box(ax, (2.85, 0.85), 2.05, 0.95, "logger_module.py", fontsize=9, sub="CSV-журнал")
    vis_c = _box(ax, (5.15, 0.85), 2.05, 0.95, "visualize.py", fontsize=9, sub="графики OXY, Z")

    # Стрелки от главного к модулям
    _arrow(ax, (main_c[0] - 1.8, main_c[1] - 0.55), (wp_c[0], wp_c[1] + 0.5), "маршрут")
    _arrow(ax, (main_c[0] - 0.6, main_c[1] - 0.55), (nav_c[0], nav_c[1] + 0.5))
    _arrow(ax, (main_c[0] + 0.6, main_c[1] - 0.55), (ctl_c[0], ctl_c[1] + 0.5), "моторы")
    _arrow(ax, (main_c[0] - 1.8, main_c[1] - 0.55), (odo_c[0], odo_c[1] + 0.5), "X, Y, dt")
    _arrow(ax, (main_c[0] - 0.2, main_c[1] - 0.55), (log_c[0], log_c[1] + 0.5), "~1 с")
    _arrow(ax, (main_c[0] + 1.2, main_c[1] - 0.55), (vis_c[0], vis_c[1] + 0.5), "по окончании")

    # CSV между логом и визуализацией
    _arrow(ax, (log_c[0] + 1.0, log_c[1]), (vis_c[0] - 1.0, vis_c[1]), "CSV", style="-|>")

    # Пояснение справа
    ax.text(
        8.0,
        3.2,
        "В цикле:\n"
        "• обновление положения\n"
        "  (API или odometry)\n"
        "• navigation → control\n"
        "• запись в журнал\n\n"
        "После миссии:\n"
        "• закрытие лога\n"
        "• visualize (опц.)",
        ha="left",
        va="top",
        fontsize=9.5,
        linespacing=1.35,
        bbox=dict(boxstyle="round", facecolor="#fffef5", edgecolor="#ccc", alpha=0.95),
    )

    ax.text(
        6,
        0.18,
        "Блоки — файлы проекта mur_ide/resources/examples/waypoint_mission/",
        ha="center",
        fontsize=8.5,
        color="#555",
    )

    fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.02)
    for path in (OUT_PNG, OUT_SVG):
        fig.savefig(path, dpi=DPI, facecolor="white")
    OUT_SCREEN.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_SCREEN, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"OK: {OUT_PNG}")
    print(f"OK: {OUT_SVG}")
    print(f"OK: {OUT_SCREEN}")


if __name__ == "__main__":
    main()
