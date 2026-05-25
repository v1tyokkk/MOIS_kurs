#!/usr/bin/env python3
"""Плакат 3: геометрическая схема расчёта целевого курса (А4)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Arc, FancyArrowPatch, FancyBboxPatch, Circle, Wedge

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "mathtext.fontset": "stix",
    }
)

from paths import OUT, SHOTS, MISSION, DOC
OUT_DIR = OUT
OUT_MAIN = OUT_DIR / "03_геометрическая_схема_курса_A4.png"
OUT_MAIN_SVG = OUT_DIR / "03_геометрическая_схема_курса_A4.svg"
OUT_FORM = OUT_DIR / "03_формулы_расчета_курса_A4.png"

FIG_W, FIG_H, DPI = 8.27, 11.69, 200

# Точки схемы (план OXY)
X, Y = 2.0, 2.0
X_T, Y_T = 8.0, 6.0
# Учебный пример: ψ заметно «левее» направления на цель — угол eψ нагляднее
PSI_DEG = 0.0  # текущий курс ψ, °
ARROW_LEN = 4.5
ARC_RADIUS = 3.8

DX, DY = X_T - X, Y_T - Y
D = math.hypot(DX, DY)
PSI_T_DEG = math.degrees(math.atan2(DY, DX))
E_PSI = math.degrees(
    math.atan2(
        math.sin(math.radians(PSI_T_DEG - PSI_DEG)),
        math.cos(math.radians(PSI_T_DEG - PSI_DEG)),
    )
)


def _arrow(ax, x0, y0, x1, y1, color, lw=2.2, ls="-", zorder=3):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=lw,
            color=color,
            linestyle=ls,
            shrinkA=0,
            shrinkB=0,
            zorder=zorder,
        )
    )


def draw_diagram(ax) -> None:
    ax.set_aspect("equal")
    ax.set_xlim(-0.3, 10.3)
    ax.set_ylim(-0.3, 8.8)
    ax.grid(True, linestyle="--", linewidth=0.6, color="#cccccc", alpha=0.85)
    ax.set_xlabel("X, м", fontsize=14)
    ax.set_ylabel("Y, м", fontsize=14)
    ax.tick_params(labelsize=12)

    # линия на цель (для угла ψц)
    ax.plot([X, X_T], [Y, Y_T], color="#cc0000", linewidth=1.2, linestyle=":", zorder=1)

    # ось X — ориентир для угла ψ (пунктир)
    ax.plot([X, X + 5.5], [Y, Y], color="#888888", linewidth=1.0, linestyle=":", zorder=0)
    ax.text(X + 5.65, Y - 0.25, "X", fontsize=11, color="#666666")

    # вектор целевого курса ψц
    L = ARROW_LEN
    rad_t = math.radians(PSI_T_DEG)
    _arrow(ax, X, Y, X + L * math.cos(rad_t), Y + L * math.sin(rad_t), "#cc0000", lw=3.0)
    ax.text(
        X + L * math.cos(rad_t) * 0.55 + 0.35,
        Y + L * math.sin(rad_t) * 0.55 + 0.25,
        r"$\psi_\mathrm{ц}$",
        fontsize=16,
        color="#cc0000",
        fontweight="bold",
    )

    # текущий курс ψ
    rad_c = math.radians(PSI_DEG)
    _arrow(ax, X, Y, X + L * math.cos(rad_c), Y + L * math.sin(rad_c), "#1a7a1a", lw=3.0)
    ax.text(
        X + L * math.cos(rad_c) * 0.55 - 0.15,
        Y + L * math.sin(rad_c) * 0.55 - 0.35,
        r"$\psi$",
        fontsize=16,
        color="#1a7a1a",
        fontweight="bold",
    )

    # сектор угла eψ (крупная дуга)
    ax.add_patch(
        Wedge(
            (X, Y),
            ARC_RADIUS,
            PSI_DEG,
            PSI_T_DEG,
            width=ARC_RADIUS * 0.55,
            facecolor="#ebe0f5",
            edgecolor="#5a2d82",
            linewidth=2.2,
            linestyle="--",
            alpha=0.75,
            zorder=2,
        )
    )
    arc = Arc(
        (X, Y),
        ARC_RADIUS * 2,
        ARC_RADIUS * 2,
        angle=0,
        theta1=PSI_DEG,
        theta2=PSI_T_DEG,
        color="#5a2d82",
        linewidth=2.5,
        linestyle="-",
        zorder=3,
    )
    ax.add_patch(arc)
    mid_a = math.radians((PSI_DEG + PSI_T_DEG) / 2)
    r_lbl = ARC_RADIUS * 0.72
    ax.text(
        X + r_lbl * math.cos(mid_a),
        Y + r_lbl * math.sin(mid_a),
        r"$e_\psi$",
        fontsize=17,
        color="#5a2d82",
        fontweight="bold",
    )

    # аппарат
    ax.add_patch(Circle((X, Y), 0.22, facecolor="#4a90d9", edgecolor="#1a4a7a", lw=1.8, zorder=5))
    ax.add_patch(
        FancyBboxPatch(
            (0.35, 0.55),
            2.5,
            0.75,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor="#e8f4fc",
            edgecolor="#1a4a7a",
            lw=1.2,
        )
    )
    ax.text(1.6, 0.92, "Аппарат  (x, y)", ha="center", va="center", fontsize=13, fontweight="bold")

    # целевая точка
    ax.add_patch(Circle((X_T, Y_T), 0.22, facecolor="#e74c3c", edgecolor="#922b21", lw=1.8, zorder=5))
    ax.add_patch(
        FancyBboxPatch(
            (6.0, 6.35),
            3.2,
            0.85,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor="white",
            edgecolor="#922b21",
            lw=1.2,
        )
    )
    ax.text(7.6, 6.78, "Целевая точка  (xц, yц)", ha="center", va="center", fontsize=13, fontweight="bold")

    # расстояние d (числовые значения углов не подписываем — только ψ, ψц, eψ на схеме)
    ax.text(4.2, 5.35, f"d = {D:.2f} м", fontsize=13, bbox=dict(boxstyle="round", facecolor="white", edgecolor="gray"))


def draw_formulas(ax) -> None:
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    lines = [
        r"$d = \sqrt{(x_\mathrm{ц}-x)^2 + (y_\mathrm{ц}-y)^2}$",
        r"$\psi_\mathrm{ц} = \mathrm{atan2}(y_\mathrm{ц}-y,\; x_\mathrm{ц}-x)\cdot 180/\pi$",
        r"$e_\psi = \mathrm{atan2}(\sin(\psi_\mathrm{ц}-\psi),\; \cos(\psi_\mathrm{ц}-\psi))\cdot 180/\pi$",
        "Условие достижения точки:  d ≤ rсхв + δ",
    ]
    y0 = 0.88
    for i, line in enumerate(lines):
        ax.text(0.5, y0 - i * 0.2, line, ha="center", va="center", fontsize=15)


def main() -> None:
    # Основной лист: схема + формулы
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.suptitle(
        "ГЕОМЕТРИЧЕСКАЯ СХЕМА РАСЧЁТА ЦЕЛЕВОГО КУРСА",
        fontsize=17,
        fontweight="bold",
        y=0.98,
    )
    ax_plot = fig.add_axes([0.10, 0.28, 0.86, 0.62])
    ax_form = fig.add_axes([0.06, 0.04, 0.88, 0.20])
    draw_diagram(ax_plot)
    draw_formulas(ax_form)

    fig.savefig(OUT_MAIN, dpi=DPI, facecolor="white", pad_inches=0.15)
    fig.savefig(OUT_MAIN_SVG, facecolor="white", pad_inches=0.15)
    plt.close(fig)

    # Отдельно только формулы (как второй файл в output)
    fig2, ax2 = plt.subplots(figsize=(FIG_W, 3.5), dpi=DPI)
    draw_formulas(ax2)
    fig2.suptitle("Формулы расчёта", fontsize=15, fontweight="bold", y=0.92)
    fig2.savefig(OUT_FORM, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig2)

    print(f"OK: {OUT_MAIN}")
    print(f"OK: {OUT_MAIN_SVG}")
    print(f"OK: {OUT_FORM}")


if __name__ == "__main__":
    main()
