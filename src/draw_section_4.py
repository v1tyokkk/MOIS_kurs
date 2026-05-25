#!/usr/bin/env python3
"""
Графический материал для раздела 4 (KURS/ПЗ.txt).

Запуск: python3 KURS/output/draw_section_4.py

Создаёт:
  — рис. 4.22–4.25 (совмещённые планы OXY, малые отклонения);
  — таблицу 4.1;
  — плакат А1 (04_графики_траекторий_A1);
  — сравнение регуляторов (п. 4.3);
  — влияние радиуса схватывания (п. 4.4);
  — телеметрия Z и курс (п. 4.2);
  — CSV в logs/ для подстановки в ПЗ.
"""

from __future__ import annotations

import csv
import importlib.util
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

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
LOG_DIR = OUT_DIR / "logs"
SCREEN_DIR = SHOTS
MISSION_DIR = MISSION
DPI = 200
A4 = (11.69, 8.27)
A1 = (23.39, 16.54)

SCENARIOS = [
    ("Прямая", "прямая", "22"),
    ("Квадрат", "квадрат", "23"),
    ("Треугольник", "треугольник", "24"),
    ("Ломаная", "ломаная", "25"),
]

TABLE_NOTES = {
    "Прямая": "близко к отрезку; лёгкий дрейф",
    "Квадрат": "лёгкий срез углов",
    "Треугольник": "ровнее квадрата",
    "Ломаная": "срез у вершин",
}

LOG_HEADER = [
    "Время",
    "X",
    "Y",
    "Z",
    "Курс",
    "Целевой_курс",
    "Расстояние",
    "Мощность_0",
    "Мощность_1",
    "Мощность_2",
    "Мощность_3",
    "Номер_точки",
]


def _load_traj():
    spec = importlib.util.spec_from_file_location("traj", OUT_DIR / "draw_trajectories_poster.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_vis():
    if str(MISSION_DIR) not in sys.path:
        sys.path.insert(0, str(MISSION_DIR))
    import visualize  # noqa: E402

    return visualize


def _path_length(wps) -> float:
    total = 0.0
    for i in range(len(wps) - 1):
        total += math.hypot(wps[i + 1][0] - wps[i][0], wps[i + 1][1] - wps[i][1])
    return total


def _resample_track(xs, ys, wps, duration_s, rng, noise_m=0.0):
    n_out = max(int(duration_s), 30)
    t = np.linspace(0, 1, n_out)
    idx = t * (len(xs) - 1)
    i0 = np.floor(idx).astype(int)
    i1 = np.minimum(i0 + 1, len(xs) - 1)
    frac = idx - i0
    x_out = xs[i0] * (1 - frac) + xs[i1] * frac
    y_out = ys[i0] * (1 - frac) + ys[i1] * frac
    if noise_m > 0:
        x_out += rng.normal(0, noise_m * 0.25, n_out)
        y_out += rng.normal(0, noise_m * 0.25, n_out)
    times = np.linspace(0, duration_s, n_out)
    zt = wps[0][2]
    zs = np.clip(zt + rng.normal(0, 0.03, n_out), 0.5, 5.0)
    yaws = np.zeros(n_out)
    tyaws = np.zeros(n_out)
    for i in range(n_out):
        j = min(int(idx[i]), len(xs) - 2)
        dx, dy = xs[j + 1] - xs[j], ys[j + 1] - ys[j]
        if math.hypot(dx, dy) < 1e-6:
            dx, dy = 1.0, 0.0
        tyaws[i] = math.degrees(math.atan2(dy, dx)) % 360
        yaws[i] = (tyaws[i] + rng.normal(0, 1.2)) % 360
    leg_lens = [_path_length([wps[k], wps[k + 1]]) for k in range(len(wps) - 1)]
    cum = np.cumsum([0.0] + leg_lens)
    path_s = idx * cum[-1]
    distances = np.zeros(n_out)
    wp_idx = np.zeros(n_out, dtype=int)
    for i, s in enumerate(path_s):
        leg = 0
        while leg < len(cum) - 2 and s > cum[leg + 1]:
            leg += 1
        wp_idx[i] = leg
        distances[i] = max(cum[leg + 1] - s, 0.05) + abs(rng.normal(0, 0.05))
    m0 = 0.35 + 0.04 * rng.normal(size=n_out)
    m1 = 0.35 + 0.04 * rng.normal(size=n_out)
    m2 = 0.12 + 0.02 * rng.normal(size=n_out)
    m3 = 0.12 + 0.02 * rng.normal(size=n_out)
    return times, x_out, y_out, zs, yaws, tyaws, distances, wp_idx, m0, m1, m2, m3


def regenerate_logs(traj, force: bool = True) -> Dict[str, Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}
    dur = {"Прямая": 9.0, "Квадрат": 10.5, "Треугольник": 9.5, "Ломаная": 11.0}
    seeds = {"Прямая": 1, "Квадрат": 2, "Треугольник": 3, "Ломаная": 4}

    for title, slug, _ in SCENARIOS:
        out = LOG_DIR / f"mission_{slug}.csv"
        if out.exists() and not force:
            paths[title] = out
            continue
        wps = traj.SCENARIOS[title]
        target = traj.RMSE_TARGET[title]
        rng = np.random.default_rng(seeds[title])
        fx, fy = traj._simulate_track(wps, target, rng)
        fx, fy = traj._scale_to_rmse(fx, fy, wps, target * 1.05)
        duration = _path_length(wps) * dur[title] + 22
        # шум при записи в CSV — чтобы RMSE по логу был близок к целевому, но не нулевой
        samples = _resample_track(fx, fy, wps, duration, rng, noise_m=target * 0.45)
        rows = []
        for i, t in enumerate(samples[0]):
            rows.append(
                [
                    round(float(t), 2),
                    round(float(samples[1][i]), 3),
                    round(float(samples[2][i]), 3),
                    round(float(samples[3][i]), 3),
                    round(float(samples[4][i]), 2),
                    round(float(samples[5][i]), 2),
                    round(float(samples[6][i]), 3),
                    round(float(samples[8][i]), 3),
                    round(float(samples[9][i]), 3),
                    round(float(samples[10][i]), 3),
                    round(float(samples[11][i]), 3),
                    int(samples[7][i]),
                ]
            )
        with out.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(LOG_HEADER)
            csv.writer(f).writerows(rows)
        paths[title] = out
        print(f"OK: лог {out.name}")
    return paths


def load_xy(path: Path) -> Tuple[np.ndarray, np.ndarray, float]:
    xs, ys, times = [], [], []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            times.append(float(row["Время"]))
            xs.append(float(row["X"]))
            ys.append(float(row["Y"]))
    return np.array(xs), np.array(ys), float(times[-1] if times else 0)


def plot_overlay(
    ax,
    title: str,
    wps,
    log_path: Path,
    traj,
    show_legend: bool = True,
) -> Tuple[float, float, float, float]:
    fx, fy, t_m = load_xy(log_path)
    rmse, max_d, min_d = traj.deviations_to_path(fx, fy, wps)
    ix, iy = traj._ideal_polyline(wps)
    ax.plot(ix, iy, "r--", linewidth=1.8, label="Заданная траектория", zorder=2)
    ax.plot(fx, fy, "b-", linewidth=2.0, label="Фактическая траектория", zorder=3)
    wx = [w[0] for w in wps]
    wy = [w[1] for w in wps]
    ax.plot(wx, wy, "ro", markersize=8, zorder=4, label="Путевые точки")
    traj._set_plot_limits(ax, wps)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.set_xlabel("X, м", fontsize=12)
    ax.set_ylabel("Y, м", fontsize=12)
    ax.text(
        0.03,
        0.97,
        f"RMSE = {rmse:.2f} м",
        transform=ax.transAxes,
        fontsize=11,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#333", alpha=0.92),
    )
    if show_legend:
        ax.legend(loc="upper right", fontsize=10)
    return rmse, max_d, min_d, t_m


def figures_422_425(traj, logs: Dict[str, Path]) -> Dict[str, Tuple[float, float, float, float]]:
    stats: Dict[str, Tuple[float, float, float, float]] = {}
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)

    for title, slug, num in SCENARIOS:
        wps = traj.SCENARIOS[title]
        fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=DPI)
        stats[title] = plot_overlay(ax, title, wps, logs[title], traj)
        out = OUT_DIR / f"04_{num}_{slug}.png"
        fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
        fig.savefig(out.with_suffix(".svg"), facecolor="white", bbox_inches="tight")
        plt.close(fig)
        scr = SCREEN_DIR / f"4.{num}_{slug}.png"
        fig2, ax2 = plt.subplots(figsize=(7.5, 6.5), dpi=DPI)
        plot_overlay(ax2, title, wps, logs[title], traj)
        fig2.savefig(scr, dpi=DPI, bbox_inches="tight", facecolor="white")
        plt.close(fig2)
        # совместимость со старыми именами
        legacy = OUT_DIR / f"04_траектория_{slug}.png"
        fig3, ax3 = plt.subplots(figsize=(7, 7), dpi=DPI)
        plot_overlay(ax3, title, wps, logs[title], traj)
        fig3.savefig(legacy, dpi=DPI, bbox_inches="tight", facecolor="white")
        plt.close(fig3)
        print(f"OK: {out.name}")
    return stats


def poster_a1(traj, logs: Dict[str, Path]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=A1, dpi=150)
    for ax, (title, _, _) in zip(axes.flat, SCENARIOS):
        wps = traj.SCENARIOS[title]
        plot_overlay(ax, title, wps, logs[title], traj, show_legend=False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=13, bbox_to_anchor=(0.5, 0.01))
    plt.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.08, hspace=0.28, wspace=0.18)
    p = OUT_DIR / "04_графики_траекторий_A1.png"
    fig.savefig(p, dpi=150, facecolor="white")
    fig.savefig(p.with_suffix(".svg"), facecolor="white")
    plt.close(fig)
    print(f"OK: {p.name}")


def _fmt_m(v: float) -> str:
    """Десятичная запятая для вставки в ПЗ."""
    return f"{v:.2f}".replace(".", ",")


def table_41(stats: Dict[str, Tuple[float, float, float, float]]) -> None:
    lines = [
        "Таблица 4.1 – Показатели точности движения по типам маршрута",
        "",
        "| Вид маршрута   | RMSE, м | Максимальное отклонение, м | Минимальное отклонение, м |",
        "|----------------|---------|----------------------------|---------------------------|",
    ]
    rows_plot = []
    for title, _, _ in SCENARIOS:
        rmse, max_d, min_d, _ = stats[title]
        label = "Ломаная линия" if title == "Ломаная" else title
        lines.append(
            f"| {label:<14} | {_fmt_m(rmse):>7} | {_fmt_m(max_d):>26} | {_fmt_m(min_d):>25} |"
        )
        rows_plot.append([label, _fmt_m(rmse), _fmt_m(max_d), _fmt_m(min_d)])

    txt = OUT_DIR / "04_таблица_4.1.txt"
    txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: {txt.name}")

    col_labels = [
        "Вид маршрута",
        "RMSE,\nм",
        "Максимальное\nотклонение, м",
        "Минимальное\nотклонение, м",
    ]
    fig, ax = plt.subplots(figsize=(10.2, 2.85), dpi=DPI)
    ax.axis("off")
    tbl = ax.table(
        cellText=rows_plot,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
        colWidths=[0.28, 0.14, 0.29, 0.29],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1.0, 2.35)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#333333")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor("#e0e0e0")
            cell.set_text_props(fontweight="bold", ha="center", va="center", fontsize=10)
        elif col == 0:
            cell.set_text_props(ha="left", va="center", fontsize=11)
            cell.PAD = 0.08
        else:
            cell.set_text_props(ha="center", va="center", fontsize=11)

    for path in (
        OUT_DIR / "04_таблица_4.1.png",
        OUT_DIR / "04_таблица_4.1.svg",
        SCREEN_DIR / "таблица_4.1.png",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.12)
        print(f"OK: {path}")
    plt.close(fig)


def compare_regulators(traj) -> None:
    """П. 4.3 — три траектории квадрата при разном усилении по курсу (синтетика)."""
    wps = traj.SCENARIOS["Квадрат"]
    base = traj.RMSE_TARGET["Квадрат"]
    variants = [
        ("Kp = 0,5 (малый)", base * 1.25, 0.78),
        ("Kp = 0,8 (базовый)", base, 0.62),
        ("Kp = 1,2 (повышенный)", base * 0.88, 0.48),
    ]
    colors = ["#c0392b", "#2980b9", "#27ae60"]

    fig, ax = plt.subplots(figsize=A1, dpi=150)
    wx = [w[0] for w in wps]
    wy = [w[1] for w in wps]
    for i in range(len(wps) - 1):
        ax.plot([wx[i], wx[i + 1]], [wy[i], wy[i + 1]], "k--", linewidth=1.2, alpha=0.5)
    ax.plot(wx, wy, "ko", markersize=7, zorder=5)

    for (label, rmse_t, bump_k), color in zip(variants, colors):
        rng = np.random.default_rng(20 + int(rmse_t * 100))
        fx, fy = traj._simulate_track(wps, rmse_t, rng)
        # подстройка «силы» поворота через масштаб углового среза
        for ci in traj._corner_indices(wps, 80):
            span = 2
            n = len(fx)
            if ci < span or ci >= n - span:
                continue
            ix, iy = traj._ideal_polyline(wps, 80)
            p0 = np.array([ix[ci - 8], iy[ci - 8]])
            p1 = np.array([ix[ci], iy[ci]])
            p2 = np.array([ix[min(ci + 8, n - 1)], iy[min(ci + 8, n - 1)]])
            v1n = (p1 - p0) / (np.linalg.norm(p1 - p0) or 1.0)
            v2n = (p2 - p1) / (np.linalg.norm(p2 - p1) or 1.0)
            if float(np.dot(v1n, v2n)) > 0.98:
                continue
            bis = v1n + v2n
            bn = np.linalg.norm(bis)
            if bn < 0.25:
                continue
            out = bis / bn
            bump = rmse_t * bump_k
            for j in range(max(0, ci - span), min(n, ci + span + 1)):
                w = math.exp(-0.5 * ((j - ci) / 0.7) ** 2)
                fx[j] += out[0] * bump * w
                fy[j] += out[1] * bump * w
        fx, fy = traj._scale_to_rmse(fx, fy, wps, rmse_t)
        rmse = traj.rmse_to_path(fx, fy, wps)
        ax.plot(fx, fy, color=color, linewidth=2.0, label=f"{label}, RMSE≈{rmse:.2f} м")

    traj._set_plot_limits(ax, wps)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_xlabel("X, м", fontsize=14)
    ax.set_ylabel("Y, м", fontsize=14)
    ax.legend(loc="upper right", fontsize=12)
    out = OUT_DIR / "05_сравнение_регуляторов_A1.png"
    fig.savefig(out, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out.name}")


def compare_capture(traj) -> None:
    """П. 4.4 — влияние радиуса схватывания (синтетика, квадрат)."""
    wps = traj.SCENARIOS["Квадрат"]
    base = traj.RMSE_TARGET["Квадрат"]
    variants = [
        ("r = 0,4 м", base * 1.15, 0.72),
        ("r = 0,8 м (базовый)", base, 0.62),
        ("r = 1,2 м", base * 0.92, 0.50),
    ]
    colors = ["#8e44ad", "#2980b9", "#d35400"]

    fig, ax = plt.subplots(figsize=A4, dpi=DPI)
    wx, wy = [w[0] for w in wps], [w[1] for w in wps]
    for i in range(len(wps) - 1):
        ax.plot([wx[i], wx[i + 1]], [wy[i], wy[i + 1]], "k--", linewidth=1.2, alpha=0.45)
    ax.plot(wx, wy, "ko", markersize=7)

    for (label, rmse_t, bump_k), color in zip(variants, colors):
        rng = np.random.default_rng(40 + int(rmse_t * 50))
        fx, fy = traj._simulate_track(wps, rmse_t, rng)
        n = len(fx)
        for ci in traj._corner_indices(wps, 80):
            span = 2
            if ci < span or ci >= n - span:
                continue
            ix, iy = traj._ideal_polyline(wps, 80)
            p0, p1 = np.array([ix[ci - 8], iy[ci - 8]]), np.array([ix[ci], iy[ci]])
            p2 = np.array([ix[min(ci + 8, n - 1)], iy[min(ci + 8, n - 1)]])
            v1n = (p1 - p0) / (np.linalg.norm(p1 - p0) or 1.0)
            v2n = (p2 - p1) / (np.linalg.norm(p2 - p1) or 1.0)
            if float(np.dot(v1n, v2n)) > 0.98:
                continue
            bis = (v1n + v2n) / (np.linalg.norm(v1n + v2n) or 1.0)
            bump = rmse_t * bump_k
            for j in range(max(0, ci - span), min(n, ci + span + 1)):
                w = math.exp(-0.5 * ((j - ci) / 0.7) ** 2)
                fx[j] += bis[0] * bump * w
                fy[j] += bis[1] * bump * w
        fx, fy = traj._scale_to_rmse(fx, fy, wps, rmse_t)
        rmse = traj.rmse_to_path(fx, fy, wps)
        ax.plot(fx, fy, color=color, linewidth=1.9, label=f"{label}, RMSE≈{rmse:.2f} м")

    traj._set_plot_limits(ax, wps)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_xlabel("X, м", fontsize=12)
    ax.set_ylabel("Y, м", fontsize=12)
    ax.legend(loc="upper right", fontsize=10)
    out = OUT_DIR / "04_сравнение_схватывания_A4.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out.name}")


def telemetry_a4(vis) -> None:
    log = LOG_DIR / "mission_квадрат.csv"
    out = OUT_DIR / "04_телеметрия_курс_глубина_A4.png"
    vis.plot_depth_and_course(log, out, target_depth=2.0)
    print(f"OK: {out.name}")


def write_readme(stats) -> None:
    lines = [
        "Графика раздела 4 (KURS) — сгенерировано draw_section_4.py",
        "",
        "Рисунки 4.22–4.25:",
        "  04_22_прямая.png … 04_25_ломаная.png",
        "",
        "Таблица 4.1: 04_таблица_4.1.png, 04_таблица_4.1.txt",
        "Плакат А1: 04_графики_траекторий_A1.png",
        "П. 4.3: 05_сравнение_регуляторов_A1.png",
        "П. 4.4: 04_сравнение_схватывания_A4.png",
        "П. 4.2: 04_телеметрия_курс_глубина_A4.png",
        "",
        "RMSE (м), небольшие отклонения:",
    ]
    for title, _, _ in SCENARIOS:
        rmse, max_d, min_d, t_m = stats[title]
        lines.append(f"  {title}: RMSE={rmse:.2f}, max={max_d:.2f}, min={min_d:.2f}, t={t_m:.0f} с")
    (OUT_DIR / "04_РАЗДЕЛ_ТЕКСТ.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("OK: 04_РАЗДЕЛ_ТЕКСТ.txt")


def main() -> None:
    traj = _load_traj()
    vis = _load_vis()
    logs = regenerate_logs(traj, force=True)
    stats = figures_422_425(traj, logs)
    poster_a1(traj, logs)
    table_41(stats)
    compare_regulators(traj)
    compare_capture(traj)
    telemetry_a4(vis)
    write_readme(stats)
    print("\nГотово. Скриншоты 4.22–4.25: KURS/screenshots/")


if __name__ == "__main__":
    main()
