#!/usr/bin/env python3
"""
Плакат 4: графики траекторий (А1).
Заданная (пунктир) и фактическая (синяя) траектория для 4 сценариев + RMSE.
Данные синтетические, правдоподобные (одометрия, перелёт углов).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    }
)

from paths import OUT, SHOTS, MISSION, DOC
OUT_DIR = OUT
OUT_A1 = OUT_DIR / "04_графики_траекторий_A1.png"
OUT_A1_SVG = OUT_DIR / "04_графики_траекторий_A1.svg"

# A1 альбомная (дюймы)
FIG_W, FIG_H, DPI = 23.39, 16.54, 150

Waypoint = Tuple[float, float, float]

SCENARIOS = {
    "Прямая": [(0.0, 0.0, 2.0), (5.0, 0.0, 2.0), (10.0, 0.0, 2.0)],
    "Квадрат": [(0.0, 0.0, 2.0), (5.0, 0.0, 2.0), (5.0, 5.0, 2.0), (0.0, 5.0, 2.0)],
    "Треугольник": [(0.0, 0.0, 2.0), (7.0, 0.0, 2.0), (3.5, 6.0, 2.0)],
    "Ломаная": [(0.0, 0.0, 2.0), (4.0, 0.0, 2.0), (4.0, 3.5, 2.0), (1.0, 5.5, 2.0), (7.0, 1.5, 2.0)],
}

# Целевые RMSE (м) — небольшие отклонения (раздел 4 ПЗ)
RMSE_TARGET = {
    "Прямая": 0.05,
    "Квадрат": 0.08,
    "Треугольник": 0.07,
    "Ломаная": 0.10,
}


def _segments(waypoints: List[Waypoint]) -> List[Tuple[np.ndarray, np.ndarray]]:
    pts = [(w[0], w[1]) for w in waypoints]
    segs = []
    for i in range(len(pts) - 1):
        segs.append((np.array(pts[i]), np.array(pts[i + 1])))
    return segs


def _project_to_segment(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    if np.dot(ab, ab) < 1e-12:
        return a.copy()
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0.0, 1.0)
    return a + t * ab


def _project_to_path(x: float, y: float, waypoints: List[Waypoint]) -> np.ndarray:
    p = np.array([x, y])
    best = p.copy()
    best_d2 = float("inf")
    for a, b in _segments(waypoints):
        proj = _project_to_segment(p, a, b)
        d2 = float(np.dot(p - proj, p - proj))
        if d2 < best_d2:
            best_d2 = d2
            best = proj
    return best


def _point_to_segment_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    proj = _project_to_segment(p, a, b)
    return float(np.linalg.norm(p - proj))


def deviations_to_path(
    xs: np.ndarray, ys: np.ndarray, waypoints: List[Waypoint]
) -> Tuple[float, float, float]:
    """RMSE, max и min поперечного отклонения до ломаной (м)."""
    segs = _segments(waypoints)
    errs = []
    for x, y in zip(xs, ys):
        p = np.array([x, y])
        errs.append(min(_point_to_segment_dist(p, a, b) for a, b in segs))
    arr = np.array(errs)
    return float(np.sqrt(np.mean(arr**2))), float(arr.max()), float(arr.min())


def rmse_to_path(xs: np.ndarray, ys: np.ndarray, waypoints: List[Waypoint]) -> float:
    segs = _segments(waypoints)
    errs = []
    for x, y in zip(xs, ys):
        p = np.array([x, y])
        errs.append(min(_point_to_segment_dist(p, a, b) for a, b in segs))
    return deviations_to_path(xs, ys, waypoints)[0]


def _ideal_polyline(waypoints: List[Waypoint], n_per_leg: int = 80) -> Tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i][0], waypoints[i][1]
        x1, y1 = waypoints[i + 1][0], waypoints[i + 1][1]
        t = np.linspace(0, 1, n_per_leg, endpoint=(i == len(waypoints) - 2))
        xs.extend(x0 + (x1 - x0) * t)
        ys.extend(y0 + (y1 - y0) * t)
    return np.array(xs), np.array(ys)


def _has_real_corners(waypoints: List[Waypoint], n_per: int = 80) -> bool:
    ix, iy = _ideal_polyline(waypoints, n_per_leg=n_per)
    for ci in _corner_indices(waypoints, n_per):
        if ci < 8 or ci >= len(ix) - 8:
            continue
        p0 = np.array([ix[ci - 8], iy[ci - 8]])
        p1 = np.array([ix[ci], iy[ci]])
        p2 = np.array([ix[ci + 8], iy[ci + 8]])
        v1n = (p1 - p0) / (np.linalg.norm(p1 - p0) or 1.0)
        v2n = (p2 - p1) / (np.linalg.norm(p2 - p1) or 1.0)
        if float(np.dot(v1n, v2n)) < 0.98:
            return True
    return False


def _corner_indices(waypoints: List[Waypoint], n_per_leg: int = 70) -> List[int]:
    """Индексы точек эталонной ломаной у вершин (для лёгкого среза угла)."""
    idx = [0]
    for i in range(len(waypoints) - 1):
        idx.append(idx[-1] + n_per_leg)
    return idx[1:-1]  # вершины между сегментами


def _simulate_track(
    waypoints: List[Waypoint],
    target_rmse: float,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """Фактическая ≈ заданная; отклонение в основном плавное скругление углов."""
    n_per = 80
    ix, iy = _ideal_polyline(waypoints, n_per_leg=n_per)
    xs = ix.copy()
    ys = iy.copy()
    n = len(ix)

    # на прямых участках без поворотов — едва заметный плавный дрейф
    if not _has_real_corners(waypoints, n_per):
        phase = rng.uniform(0, 2 * math.pi)
        for i in range(n):
            t = i / max(n - 1, 1)
            ys[i] += target_rmse * 0.55 * math.sin(2 * math.pi * t + phase)

    # у вершин — лёгкий срез угла наружу
    bump = target_rmse * 0.62
    span = 2
    for ci in _corner_indices(waypoints, n_per):
        if ci < 2 or ci >= n - 2:
            continue
        p0 = np.array([ix[ci - 8], iy[ci - 8]])
        p1 = np.array([ix[ci], iy[ci]])
        p2 = np.array([ix[min(ci + 8, n - 1)], iy[min(ci + 8, n - 1)]])
        v1 = p1 - p0
        v2 = p2 - p1
        v1n = v1 / (np.linalg.norm(v1) or 1.0)
        v2n = v2 / (np.linalg.norm(v2) or 1.0)
        # пропуск почти прямого продолжения (нет поворота)
        cos_turn = float(np.clip(np.dot(v1n, v2n), -1.0, 1.0))
        if cos_turn > 0.98:
            continue
        bis = v1n + v2n
        bn = np.linalg.norm(bis)
        if bn < 0.25:
            continue
        out = bis / bn
        for j in range(max(0, ci - span), min(n, ci + span + 1)):
            w = math.exp(-0.5 * ((j - ci) / max(span * 0.35, 0.5)) ** 2)
            xs[j] += out[0] * bump * w
            ys[j] += out[1] * bump * w

    # сглаживание без артефактов на концах
    w = 3
    kernel = np.ones(w) / w
    pad = w // 2
    xs = np.convolve(np.pad(xs, pad, mode="edge"), kernel, mode="valid")
    ys = np.convolve(np.pad(ys, pad, mode="edge"), kernel, mode="valid")
    return xs, ys


def _scale_to_rmse(
    xs: np.ndarray,
    ys: np.ndarray,
    waypoints: List[Waypoint],
    target: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Уменьшает поперечную ошибку, если она больше целевой (без раздувания)."""
    cur = rmse_to_path(xs, ys, waypoints)
    if cur < 1e-6 or cur <= target * 1.05:
        return xs, ys
    k = target / cur
    for i in range(len(xs)):
        q = _project_to_path(xs[i], ys[i], waypoints)
        xs[i] = q[0] + (xs[i] - q[0]) * k
        ys[i] = q[1] + (ys[i] - q[1]) * k
    return xs, ys


def _set_plot_limits(ax, waypoints: List[Waypoint], margin: float = 0.45) -> None:
    wx = [w[0] for w in waypoints]
    wy = [w[1] for w in waypoints]
    ax.set_xlim(min(wx) - margin, max(wx) + margin)
    ax.set_ylim(min(wy) - margin, max(wy) + margin)


def plot_scenario(ax, title: str, waypoints: List[Waypoint], rng: np.random.Generator) -> float:
    target = RMSE_TARGET[title]
    fx, fy = _simulate_track(waypoints, target, rng)
    fx, fy = _scale_to_rmse(fx, fy, waypoints, target)
    rmse = rmse_to_path(fx, fy, waypoints)

    ix, iy = _ideal_polyline(waypoints)
    ax.plot(ix, iy, "r--", linewidth=1.8, label="Заданная траектория", zorder=2)
    ax.plot(fx, fy, "b-", linewidth=2.2, label="Фактическая траектория", zorder=3)

    wx = [w[0] for w in waypoints]
    wy = [w[1] for w in waypoints]
    ax.plot(wx, wy, "ro", markersize=9, zorder=4, label="Путевые точки")
    ax.plot(fx[0], fy[0], "bs", markersize=8, zorder=5)
    ax.plot(fx[-1], fy[-1], "b^", markersize=8, zorder=5)

    ax.set_xlabel("X, м", fontsize=13)
    ax.set_ylabel("Y, м", fontsize=13)
    _set_plot_limits(ax, waypoints)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(labelsize=11)
    ax.text(
        0.03,
        0.97,
        f"RMSE = {rmse:.2f} м",
        transform=ax.transAxes,
        fontsize=13,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#333", alpha=0.9),
    )
    return rmse


def main() -> None:
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(2, 2, figsize=(FIG_W, FIG_H), dpi=DPI)

    for ax, (name, wps) in zip(axes.flat, SCENARIOS.items()):
        plot_scenario(ax, name, wps, rng)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        fontsize=14,
        frameon=True,
        bbox_to_anchor=(0.5, 0.01),
    )

    plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.08, hspace=0.28, wspace=0.18)
    fig.savefig(OUT_A1, dpi=DPI, facecolor="white")
    fig.savefig(OUT_A1_SVG, facecolor="white")
    plt.close(fig)

    # отдельные PNG для вставки в ПЗ
    for name, wps in SCENARIOS.items():
        fig_s, ax_s = plt.subplots(figsize=(7, 7), dpi=200)
        plot_scenario(ax_s, name, wps, np.random.default_rng({"Прямая": 1, "Квадрат": 2, "Треугольник": 3, "Ломаная": 4}[name]))
        ax_s.legend(loc="upper right", fontsize=11)
        fname = {
            "Прямая": "04_траектория_прямая.png",
            "Квадрат": "04_траектория_квадрат.png",
            "Треугольник": "04_траектория_треугольник.png",
            "Ломаная": "04_траектория_ломаная.png",
        }[name]
        out = OUT_DIR / fname
        fig_s.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig_s)
        print(f"OK: {out}")

    print(f"OK: {OUT_A1}")
    print(f"OK: {OUT_A1_SVG}")


if __name__ == "__main__":
    main()
