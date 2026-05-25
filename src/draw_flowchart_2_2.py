#!/usr/bin/env python3
"""
Рисунок 2.2 – блок-схема основного цикла программы (ГОСТ 19.701-90).
Запуск: python3 KURS/output/draw_flowchart_2_2.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    }
)

CX = 4.05
LOOP_X = 0.95
EXIT_X = 7.05
Y_TOP = 22.8

FS = 13
FS_TERM = 14
BOX_W = 4.15
BOX_H = 1.42
TERM_H = 0.62
SKEW = 0.22
GAP = 0.18
ARROW = 10
LW = 1.45
DIA_HW = 2.05
DIA_HH = 0.78

FIG = (8.27, 11.69)
DPI = 200

OUT_PNG = OUT / "02_блок_схема_2.2_A4.png"
OUT_SVG = OUT_PNG.with_suffix(".svg")
OUT_SCR = SHOTS / "2.2.png"


@dataclass(frozen=True)
class Bounds:
    top: float
    bottom: float
    center: float
    left: float
    right: float


def _text(ax, y: float, s: str) -> None:
    fs = FS_TERM if s.count("\n") == 0 else FS
    ax.text(CX, y, s, ha="center", va="center", fontsize=fs, linespacing=0.84)


def _text_at(ax, x: float, y: float, s: str, **kw) -> None:
    ax.text(x, y, s, ha="center", va="center", fontsize=FS, linespacing=0.84, **kw)


def _down(ax, x: float, y0: float, y1: float) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x, y0),
            (x, y1),
            arrowstyle="-|>",
            mutation_scale=ARROW,
            linewidth=LW,
            color="black",
            shrinkA=0,
            shrinkB=0,
        )
    )


def _arrow(ax, p0, p1) -> None:
    ax.add_patch(
        FancyArrowPatch(
            p0,
            p1,
            arrowstyle="-|>",
            mutation_scale=ARROW,
            linewidth=LW,
            color="black",
            shrinkA=0,
            shrinkB=0,
        )
    )


def terminal(ax, x: float, y: float, label: str) -> Bounds:
    w, h = BOX_W, TERM_H
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={h / 2}",
            fill=False,
            ec="black",
            lw=LW,
        )
    )
    _text_at(ax, x, y, label)
    return Bounds(y + h / 2, y - h / 2, y, x - w / 2, x + w / 2)


def process(ax, x: float, y: float, label: str) -> Bounds:
    w, h = BOX_W, BOX_H
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, ec="black", lw=LW))
    _text_at(ax, x, y, label)
    return Bounds(y + h / 2, y - h / 2, y, x - w / 2, x + w / 2)


def io_block(ax, x: float, y: float, label: str) -> Bounds:
    w, h = BOX_W, BOX_H
    hh, hw = h / 2, w / 2
    pts = [
        (x - hw + SKEW, y - hh),
        (x + hw + SKEW, y - hh),
        (x + hw - SKEW, y + hh),
        (x - hw - SKEW, y + hh),
    ]
    ax.add_patch(Polygon(pts, closed=True, fill=False, ec="black", lw=LW))
    _text_at(ax, x, y, label)
    return Bounds(y + hh, y - hh, y, x - hw - SKEW, x + hw + SKEW)


def decision(ax, x: float, y: float, label: str) -> Bounds:
    pts = [
        (x, y + DIA_HH),
        (x + DIA_HW, y),
        (x, y - DIA_HH),
        (x - DIA_HW, y),
    ]
    ax.add_patch(Polygon(pts, closed=True, fill=False, ec="black", lw=LW))
    _text_at(ax, x, y, label)
    return Bounds(y + DIA_HH, y - DIA_HH, y, x - DIA_HW, x + DIA_HW)


def below(prev: Bounds, half_h: float) -> float:
    return prev.bottom - GAP - half_h


def main() -> None:
    fig, ax = plt.subplots(figsize=FIG, dpi=DPI)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(
        CX,
        Y_TOP + 0.28,
        "Рисунок 2.2 – Блок-схема основного цикла программы",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )

    L = {
        "init": "Инициализация\nсоединения\nс аппаратом",
        "route": "Загрузка\nмаршрута",
        "cond": "Миссия\nне завершена?",
        "pos": "Обновление оценки\nположения X, Y",
        "telem": "Получение курса\nи глубины",
        "nav": "Расстояние и\nцелевой курс",
        "ctrl": "Ошибки, П-законы,\nограничение сигналов",
        "motors": "Передача мощностей\nна движители",
        "log": "Периодическая\nзапись в лог",
        "wp": "Проверка достижения\nточки, сдвиг индекса",
        "wait": "Пауза цикла\n(10 Гц)",
        "close": "Закрытие лога,\nсброс моторов",
    }

    hh = BOX_H / 2

    s0 = terminal(ax, CX, Y_TOP, "Начало")
    y = below(s0, hh)
    s1 = io_block(ax, CX, y, L["init"])
    _down(ax, CX, s0.bottom, s1.top)

    y = below(s1, hh)
    s2 = io_block(ax, CX, y, L["route"])
    _down(ax, CX, s1.bottom, s2.top)

    y = below(s2, DIA_HH)
    sd = decision(ax, CX, y, L["cond"])

    ax.text(sd.center - 0.45, sd.bottom - 0.05, "да", fontsize=10, ha="right", va="top")
    ax.text(sd.right + 0.12, sd.center + 0.1, "нет", fontsize=10, ha="left", va="bottom")

    prev = sd
    for key in ("pos", "telem", "nav", "ctrl", "motors", "log", "wp", "wait"):
        y = below(prev, hh)
        s = process(ax, CX, y, L[key])
        _down(ax, CX, prev.bottom, s.top)
        prev = s

    # Возврат к условию — слева
    _arrow(ax, (prev.left, prev.center), (LOOP_X, prev.center))
    _arrow(ax, (LOOP_X, prev.center), (LOOP_X, sd.center))
    _arrow(ax, (LOOP_X, sd.center), (sd.left, sd.center))

    # Выход «нет» — справа вниз
    y_close = below(prev, hh)
    s_close = process(ax, EXIT_X, y_close, L["close"])
    _arrow(ax, (sd.right, sd.center), (EXIT_X, sd.center))
    _down(ax, EXIT_X, sd.center, s_close.top)

    y_end = below(s_close, TERM_H / 2)
    s_end = terminal(ax, EXIT_X, y_end, "Конец")
    _down(ax, EXIT_X, s_close.bottom, s_end.top)

    ax.text(
        CX,
        s_end.bottom - 0.55,
        "Цикл 10–20 Гц: итерация — шаги до «Пауза», затем возврат к проверке завершения миссии",
        ha="center",
        fontsize=8,
        color="#444",
    )

    ax.set_xlim(-0.35, 9.15)
    ax.set_ylim(s_end.bottom - 0.9, Y_TOP + 0.75)
    fig.subplots_adjust(left=0.04, right=0.99, top=0.97, bottom=0.02)
    kw = dict(dpi=DPI, facecolor="white", pad_inches=0.08)
    fig.savefig(OUT_PNG, **kw)
    fig.savefig(OUT_SVG, **kw)
    OUT_SCR.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_SCR, **kw)
    plt.close(fig)
    print(f"OK: {OUT_PNG}")
    print(f"OK: {OUT_SVG}")
    print(f"OK: {OUT_SCR}")


if __name__ == "__main__":
    main()
