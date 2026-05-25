#!/usr/bin/env python3
"""
Блок-схема по ГОСТ 19.701-90.
Блоки: высота : ширина = 2 : 3. Подписи (кроме Начало/Конец) — в 3 строки.
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
        "mathtext.fontset": "stix",
    }
)

CX = 5.0
Y_TOP = 16.5

FS = 17
FS_TERMINAL = 18

# Высота : ширина = 2 : 3  →  h = w * 2/3  (блок шире, чем высок)
HEIGHT_RATIO = 2
WIDTH_RATIO = 3
BOX_W = 4.5
BOX_H = BOX_W * HEIGHT_RATIO / WIDTH_RATIO
# Начало / Конец: ширина как у остальных, высота как раньше (уже)
TERMINAL_W = BOX_W
TERMINAL_H = (BOX_W * 0.75) * HEIGHT_RATIO / WIDTH_RATIO
SKEW = 0.26
GAP_SHAPES = 0.58
ARROW_MUTATION = 14
LW = 1.6

FIG_W_IN = 8.27
FIG_H_IN = 11.69
FIG_DPI = 200

from paths import OUT, SHOTS, MISSION, DOC
OUT_DIR = OUT
OUT_PNG = OUT_DIR / "02_блок_схема_алгоритма_A4.png"
OUT_SVG = OUT_DIR / "02_блок_схема_алгоритма_A4.svg"

# Все подписи — 3 строки, кроме Начало / Конец
LABELS = {
    "io_start": "Подключение к\nсимулятору и\nзагрузка маршрута",
    "telemetry": "Телеметрия\nи оценка\nкоординат",
    "nav": "Расчёт\nрасстояния и\nцелевого курса",
    "control": "П-регуляторы\nуправление\nмоторами",
    "waypoint": "Проверка\nдостижения\nпутевой точки",
    "csv": "Запись\nпараметров\nв CSV",
}


@dataclass(frozen=True)
class ShapeBounds:
    top: float
    bottom: float
    center: float


def _line_count(text: str) -> int:
    return text.count("\n") + 1


def _box_size(text: str) -> tuple[float, float]:
    """Один размер: ширина 3, высота 2 (в тех же условных единицах)."""
    _ = text
    return BOX_W, BOX_H


def _box_half_h(text: str) -> float:
    return _box_size(text)[1] / 2


def arrow_down(ax, y_tail: float, y_head: float) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (CX, y_tail),
            (CX, y_head),
            arrowstyle="-|>",
            mutation_scale=ARROW_MUTATION,
            linewidth=LW,
            color="black",
            shrinkA=0,
            shrinkB=0,
            clip_on=False,
        )
    )


def _text(ax, y: float, text: str) -> None:
    n = _line_count(text)
    fs = FS_TERMINAL if n == 1 else FS
    ax.text(
        CX,
        y,
        text,
        ha="center",
        va="center",
        fontsize=fs,
        linespacing=0.88,
    )


def gost_terminal(ax, y: float, text: str) -> ShapeBounds:
    """Начало / конец — «стадион»: ширина = BOX_W, высота прежняя."""
    w, h = TERMINAL_W, TERMINAL_H
    ax.add_patch(
        FancyBboxPatch(
            (CX - w / 2, y - h / 2),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={h / 2}",
            fill=False,
            ec="black",
            lw=LW,
        )
    )
    _text(ax, y, text)
    return ShapeBounds(top=y + h / 2, bottom=y - h / 2, center=y)


def gost_process(ax, y: float, text: str) -> ShapeBounds:
    w, h = _box_size(text)
    ax.add_patch(
        Rectangle((CX - w / 2, y - h / 2), w, h, fill=False, ec="black", lw=LW)
    )
    _text(ax, y, text)
    return ShapeBounds(top=y + h / 2, bottom=y - h / 2, center=y)


def gost_io(ax, y: float, text: str) -> ShapeBounds:
    w, h = _box_size(text)
    half_h, half_w = h / 2, w / 2
    pts = [
        (CX - half_w + SKEW, y - half_h),
        (CX + half_w + SKEW, y - half_h),
        (CX + half_w - SKEW, y + half_h),
        (CX - half_w - SKEW, y + half_h),
    ]
    ax.add_patch(Polygon(pts, closed=True, fill=False, ec="black", lw=LW))
    _text(ax, y, text)
    return ShapeBounds(top=y + half_h, bottom=y - half_h, center=y)


def center_below(prev: ShapeBounds, half_h: float) -> float:
    return prev.bottom - GAP_SHAPES - half_h


def link(ax, upper: ShapeBounds, lower: ShapeBounds) -> None:
    arrow_down(ax, upper.bottom, lower.top)


def half_h(text: str) -> float:
    return _box_half_h(text)


def main() -> None:
    fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=FIG_DPI)
    ax.set_aspect("equal")
    ax.axis("off")

    s0 = gost_terminal(ax, Y_TOP, "Начало")

    y = center_below(s0, half_h(LABELS["io_start"]))
    s1 = gost_io(ax, y, LABELS["io_start"])
    link(ax, s0, s1)

    prev = s1
    proc_keys = ("telemetry", "nav", "control", "waypoint")
    y = center_below(s1, half_h(LABELS[proc_keys[0]]))
    for i, key in enumerate(proc_keys):
        s = gost_process(ax, y, LABELS[key])
        link(ax, prev, s)
        prev = s
        next_key = "csv" if i == len(proc_keys) - 1 else proc_keys[i + 1]
        y = center_below(s, half_h(LABELS[next_key]))

    s_csv = gost_io(ax, y, LABELS["csv"])
    link(ax, prev, s_csv)

    y_end = center_below(s_csv, TERMINAL_H / 2)
    s_end = gost_terminal(ax, y_end, "Конец")
    link(ax, s_csv, s_end)

    # запас: параллелограмм (+ SKEW), наконечники стрелок, овал сверху
    pad_x = BOX_W / 2 + SKEW + 0.55
    pad_top = 0.65
    pad_bottom = 0.55
    ax.set_xlim(CX - pad_x, CX + pad_x)
    ax.set_ylim(s_end.bottom - pad_bottom, s0.top + pad_top)

    fig.subplots_adjust(left=0.12, right=0.88, top=0.95, bottom=0.04)
    save_kw = dict(dpi=FIG_DPI, facecolor="white", pad_inches=0.12)
    fig.savefig(OUT_PNG, **save_kw)
    fig.savefig(OUT_SVG, **save_kw)
    plt.close()
    print(f"OK: {OUT_PNG}")
    print(f"OK: {OUT_SVG}")


if __name__ == "__main__":
    main()
