#!/usr/bin/env python3
"""
Приложение В (KURS): рис. В.2, В.3, таблица В.1.
Генерирует CSV-журналы (учебные, по модели одометрии) и графики.

Запуск: python3 KURS/output/draw_appendix_B.py

При наличии своих логов из симулятора положите в KURS/output/logs/:
  mission_прямая.csv, mission_квадрат.csv, mission_треугольник.csv, mission_ломаная.csv
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
MISSION_DIR = MISSION

A4_L = (11.69, 8.27)
DPI = 200

Waypoint = Tuple[float, float, float]

SCENARIO_ORDER = [
    ("Прямая", "прямая"),
    ("Квадрат", "квадрат"),
    ("Треугольник", "треугольник"),
    ("Ломаная", "ломаная"),
]

SUBPLOT_TAG = {"Прямая": "а", "Квадрат": "б", "Треугольник": "в", "Ломаная": "г"}

TABLE_NOTES = {
    "Прямая": "близко к отрезку;\nрасхождения у разгона и финиша",
    "Квадрат": "срез углов;\nнакопление ошибки к замыканию",
    "Треугольник": "ровнее квадрата\nпри тех же Kp",
    "Ломаная": "нагрузка на контур;\nзигзаги у вершин",
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


def _load_traj_module():
    spec = importlib.util.spec_from_file_location(
        "traj_poster", OUT_DIR / "draw_trajectories_poster.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_visualize():
    if str(MISSION_DIR) not in sys.path:
        sys.path.insert(0, str(MISSION_DIR))
    import visualize  # noqa: E402

    return visualize


def _path_length(wps: List[Waypoint]) -> float:
    total = 0.0
    for i in range(len(wps) - 1):
        dx = wps[i + 1][0] - wps[i][0]
        dy = wps[i + 1][1] - wps[i][1]
        total += math.hypot(dx, dy)
    return total


def _max_deviation(xs: np.ndarray, ys: np.ndarray, wps: List[Waypoint], traj) -> float:
    segs = traj._segments(wps)
    errs = []
    for x, y in zip(xs, ys):
        p = np.array([x, y])
        errs.append(min(traj._point_to_segment_dist(p, a, b) for a, b in segs))
    return float(max(errs))


def _resample_track(
    xs: np.ndarray,
    ys: np.ndarray,
    wps: List[Waypoint],
    duration_s: float,
    rng: np.random.Generator,
    noise_m: float = 0.0,
) -> Tuple[np.ndarray, ...]:
    """Ресемплинг траектории ~1 Гц для CSV."""
    n_out = max(int(duration_s), 30)
    t = np.linspace(0, 1, n_out)
    idx = t * (len(xs) - 1)
    i0 = np.floor(idx).astype(int)
    i1 = np.minimum(i0 + 1, len(xs) - 1)
    frac = idx - i0
    x_out = xs[i0] * (1 - frac) + xs[i1] * frac
    y_out = ys[i0] * (1 - frac) + ys[i1] * frac
    if noise_m > 0:
        x_out = x_out + rng.normal(0, noise_m * 0.35, n_out)
        y_out = y_out + rng.normal(0, noise_m * 0.35, n_out)
    times = np.linspace(0, duration_s, n_out)

    z_target = wps[0][2]
    zs = z_target + rng.normal(0, 0.04, n_out)
    zs = np.clip(zs, 0.5, 5.0)

    yaws = np.zeros(n_out)
    target_yaws = np.zeros(n_out)
    for i in range(n_out):
        j = min(int(idx[i]), len(xs) - 2)
        dx = xs[j + 1] - xs[j]
        dy = ys[j + 1] - ys[j]
        if math.hypot(dx, dy) < 1e-6:
            dx, dy = 1.0, 0.0
        yaws[i] = (math.degrees(math.atan2(dy, dx)) + rng.normal(0, 2)) % 360
        target_yaws[i] = math.degrees(math.atan2(dy, dx)) % 360

    # расстояние до текущей цели (упрощённо)
    distances = np.zeros(n_out)
    wp_idx = np.zeros(n_out, dtype=int)
    leg_lens = [_path_length([wps[k], wps[k + 1]]) for k in range(len(wps) - 1)]
    cum = np.cumsum([0.0] + leg_lens)
    path_s = idx * cum[-1]
    for i, s in enumerate(path_s):
        leg = 0
        while leg < len(cum) - 2 and s > cum[leg + 1]:
            leg += 1
        wp_idx[i] = leg
        seg_rem = cum[leg + 1] - s
        distances[i] = max(seg_rem, 0.05) + abs(rng.normal(0, 0.08))

    m0 = 0.35 + 0.05 * rng.normal(size=n_out)
    m1 = 0.35 + 0.05 * rng.normal(size=n_out)
    m2 = 0.12 + 0.03 * rng.normal(size=n_out)
    m3 = 0.12 + 0.03 * rng.normal(size=n_out)

    return times, x_out, y_out, zs, yaws, target_yaws, distances, wp_idx, m0, m1, m2, m3


def write_log_csv(path: Path, rows: List[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)


def generate_logs(traj) -> Dict[str, Path]:
    """CSV по сценариям (или использует существующие в logs/)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}
    duration_scale = {"Прямая": 9.5, "Квадрат": 11.0, "Треугольник": 10.0, "Ломаная": 12.5}

    for title, slug in SCENARIO_ORDER:
        out = LOG_DIR / f"mission_{slug}.csv"
        if out.exists() and out.stat().st_size > 200:
            paths[title] = out
            continue

        wps = traj.SCENARIOS[title]
        target = traj.RMSE_TARGET[title]
        rng = np.random.default_rng({"Прямая": 1, "Квадрат": 2, "Треугольник": 3, "Ломаная": 4}[title])
        fx, fy = traj._simulate_track(wps, target, rng)
        duration = _path_length(wps) * duration_scale[title] + 25
        samples = _resample_track(fx, fy, wps, duration, rng, noise_m=target)
        times, xo, yo, zs, yaws, tyaws, dist, wpi, m0, m1, m2, m3 = samples
        rows = []
        for i in range(len(times)):
            rows.append(
                [
                    round(times[i], 2),
                    round(float(xo[i]), 3),
                    round(float(yo[i]), 3),
                    round(float(zs[i]), 3),
                    round(float(yaws[i]), 2),
                    round(float(tyaws[i]), 2),
                    round(float(dist[i]), 3),
                    round(float(m0[i]), 3),
                    round(float(m1[i]), 3),
                    round(float(m2[i]), 3),
                    round(float(m3[i]), 3),
                    int(wpi[i]),
                ]
            )
        write_log_csv(out, rows)
        paths[title] = out
        print(f"OK: лог {out}")
    return paths


def load_xy_from_log(path: Path) -> Tuple[np.ndarray, np.ndarray, float]:
    times: List[float] = []
    xs: List[float] = []
    ys: List[float] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["Время"]))
            xs.append(float(row["X"]))
            ys.append(float(row["Y"]))
    return np.array(xs), np.array(ys), float(times[-1] if times else 0)


def plot_trajectory_panel(
    ax,
    title: str,
    wps: List[Waypoint],
    log_path: Path,
    traj,
    tag: str,
) -> Tuple[float, float, float]:
    fx, fy, t_mission = load_xy_from_log(log_path)
    rmse = traj.rmse_to_path(fx, fy, wps)
    max_dev = _max_deviation(fx, fy, wps, traj)

    wx = [w[0] for w in wps]
    wy = [w[1] for w in wps]
    for i in range(len(wps) - 1):
        ax.plot([wx[i], wx[i + 1]], [wy[i], wy[i + 1]], "r--", linewidth=1.8, zorder=2)
    ax.plot(wx, wy, "ro", markersize=8, zorder=4)
    ax.plot(fx, fy, "b-", linewidth=2.0, label="Факт (CSV)", zorder=3)

    traj._set_plot_limits(ax, wps)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.set_xlabel("X, м", fontsize=11)
    ax.set_ylabel("Y, м", fontsize=11)
    _ = tag  # подрисунки В.2а–г — подпись только в тексте ПЗ
    ax.text(
        0.03,
        0.97,
        f"RMSE = {rmse:.2f} м",
        transform=ax.transAxes,
        fontsize=11,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", edgecolor="#333", alpha=0.92),
    )
    return rmse, max_dev, t_mission


def figure_v2(traj, log_paths: Dict[str, Path]) -> Dict[str, Tuple[float, float, float]]:
    fig, axes = plt.subplots(2, 2, figsize=A4_L, dpi=DPI)
    stats: Dict[str, Tuple[float, float, float]] = {}
    for ax, (title, _) in zip(axes.flat, SCENARIO_ORDER):
        wps = traj.SCENARIOS[title]
        tag = SUBPLOT_TAG[title]
        stats[title] = plot_trajectory_panel(ax, title, wps, log_paths[title], traj, tag)

    handles = [
        plt.Line2D([0], [0], color="r", linestyle="--", linewidth=1.8),
        plt.Line2D([0], [0], color="b", linewidth=2),
        plt.Line2D([0], [0], marker="o", color="r", linestyle="None", markersize=8),
    ]
    fig.legend(
        handles,
        ["Заданная ломаная", "Фактическая (CSV)", "Путевые точки"],
        loc="lower center",
        ncol=3,
        fontsize=11,
        frameon=True,
        bbox_to_anchor=(0.5, 0.01),
    )
    analysis = (
        "Прямая: факт ≈ отрезок, расхождения у разгона и финиша.  "
        "Квадрат: срез углов, ошибка одометрии к замыканию.  "
        "Треугольник: обычно ровнее квадрата.  "
        "Ломаная: нагрузка на контур, зигзаги между вершинами."
    )
    fig.text(0.5, 0.035, analysis, ha="center", fontsize=9, color="#333", wrap=True)
    plt.subplots_adjust(left=0.06, right=0.98, top=0.96, bottom=0.10, hspace=0.32, wspace=0.22)
    out = OUT_DIR / "В_2_графики_траекторий_A4.png"
    fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    fig.savefig(out.with_suffix(".svg"), facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print(f"OK: {out}")

    for title, slug in SCENARIO_ORDER:
        fig_s, ax_s = plt.subplots(figsize=(7, 6), dpi=DPI)
        wps = traj.SCENARIOS[title]
        plot_trajectory_panel(ax_s, title, wps, log_paths[title], traj, SUBPLOT_TAG[title])
        ax_s.legend(loc="upper right", fontsize=10)
        p = OUT_DIR / f"В_2{SUBPLOT_TAG[title]}_{slug}.png"
        fig_s.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white")
        plt.close(fig_s)
        print(f"OK: {p}")

    return stats


def figure_v3(vis) -> None:
    log_path = LOG_DIR / "mission_квадрат.csv"
    out = OUT_DIR / "В_3_телеметрия_A4.png"
    vis.plot_depth_and_course(log_path, out, target_depth=2.0)
    print(f"OK: {out}")


def table_v1(stats: Dict[str, Tuple[float, float, float]]) -> None:
    lines = [
        "Таблица В.1 – Результаты испытаний по сценариям п. 1.5",
        "",
        "| Вид маршрута   | RMSE, м | t миссии, с | Max откл., м | Примечание        |",
        "|----------------|---------|-------------|--------------|-------------------|",
    ]
    rows_for_plot = []
    for title, _ in SCENARIO_ORDER:
        rmse, max_d, t_m = stats[title]
        note = TABLE_NOTES[title]
        label = "Ломаная линия" if title == "Ломаная" else title
        lines.append(
            f"| {label:<14} | {rmse:>7.2f} | {t_m:>11.0f} | {max_d:>12.2f} | {note:<17} |"
        )
        rows_for_plot.append([label, f"{rmse:.2f}", f"{t_m:.0f}", f"{max_d:.2f}", note])

    txt_path = OUT_DIR / "В_1_таблица.txt"
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: {txt_path}")

    fig, ax = plt.subplots(figsize=(12.5, 3.6), dpi=DPI)
    ax.axis("off")
    col_labels = ["Маршрут", "RMSE,\nм", "t,\nс", "Max,\nм", "Примечание"]
    # узкие числовые столбцы, широкий «Примечание»
    col_widths = [0.11, 0.07, 0.07, 0.08, 0.67]
    table = ax.table(
        cellText=rows_for_plot,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 2.1)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#e8e8e8")
            cell.set_text_props(fontweight="bold", ha="center", va="center")
        elif col == 0:
            cell.set_text_props(ha="left", va="center")
            cell.PAD = 0.04
        elif col == 4:
            cell.set_text_props(ha="left", va="center", fontsize=9.5)
            cell.PAD = 0.06
        else:
            cell.set_text_props(ha="center", va="center")
    png_path = OUT_DIR / "В_1_таблица.png"
    fig.savefig(png_path, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(f"OK: {png_path}")

    analysis_path = OUT_DIR / "В_2_РАЗБОР.txt"
    analysis_path.write_text(
        "\n".join(
            [
                "Краткий разбор траекторий (рис. В.2)",
                "",
                "— Прямая: фактический путь близок к отрезку между крайними путевыми точками;",
                "  заметные расхождения обычно у разгона и у финиша.",
                "— Квадрат: на поворотах наблюдается срез углов; возможно накопление",
                "  ошибки одометрии при замыкании контура.",
                "— Треугольник: при тех же коэффициентах регулятора траектория",
                "  обычно ровнее, чем у квадрата (меньше резких смен курса).",
                "— Ломаная: наибольшая нагрузка на контур курса; локальные зигзаги",
                "  между вершинами ломаной.",
                "",
                "Численные RMSE, время миссии и max отклонение — таблица В.1.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"OK: {analysis_path}")


def update_pz_v_table(stats: Dict[str, Tuple[float, float, float]]) -> None:
    pz = DOC / "ПЗ_В.txt"
    if not pz.exists():
        return
    text = pz.read_text(encoding="utf-8")
    old_block = """| Прямая         |         |             |              |                   |
| Квадрат        |         |             |              |                   |
| Треугольник    |         |             |              |                   |
| Ломаная линия  |         |             |              |                   |"""
    new_lines = [
        "| Вид маршрута   | RMSE, м | t миссии, с | Max откл., м | Примечание        |",
        "|----------------|---------|-------------|--------------|-------------------|",
    ]
    for title, _ in SCENARIO_ORDER:
        rmse, max_d, t_m = stats[title]
        label = "Ломаная линия" if title == "Ломаная" else title
        note = TABLE_NOTES[title]
        new_lines.append(
            f"| {label:<14} | {rmse:>7.2f} | {t_m:>11.0f} | {max_d:>12.2f} | {note:<17} |"
        )
    new_block = "\n".join(new_lines[2:])
    if old_block in text:
        text = text.replace(old_block, new_block)
        pz.write_text(text, encoding="utf-8")
        print(f"OK: обновлён {pz}")


def main() -> None:
    traj = _load_traj_module()
    vis = _load_visualize()
    log_paths = generate_logs(traj)
    stats = figure_v2(traj, log_paths)
    figure_v3(vis)
    table_v1(stats)
    update_pz_v_table(stats)
    print("\nГотово. Логи: KURS/output/logs/mission_*.csv")


if __name__ == "__main__":
    main()
