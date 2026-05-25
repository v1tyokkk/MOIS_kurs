# Траектория движения АНПА по путевым точкам (MUR IDE)

Материалы курсовой: пояснительная записка, приложения, готовые рисунки и **скрипты** для пересборки графики и Word.

Симулятор и IDE **не входят** в этот репозиторий — нужна установленная MUR IDE ([murproject.com](https://murproject.com/#muride)) или полный репозиторий `mur_ide-macos-arm`.

## Структура

| Папка | Содержимое |
|-------|------------|
| **doc/** | ПЗ, приложения А–В, `docx/`, `output/` (PNG/SVG), `screenshots/`, задание, инструкции по рисункам |
| **doc/program/waypoint_mission/** | Копия примера миссии для симулятора (открыть в IDE, F5) |
| **src/** | Только Python-скрипты |

## Зависимости

```bash
python3 -m pip install matplotlib numpy python-docx
```

Для `build_docx.py` дополнительно нужен модуль **word-manager** (если его нет — используйте готовые файлы в `doc/docx/`).

## Скрипты (из корня репозитория)

```bash
cd kurs01-trajectory-anpa
```

| Команда | Результат |
|---------|-----------|
| `python3 src/md_to_txt.py` | Обновляет `doc/*.txt` из `doc/*.md` (если правили md) |
| `python3 src/build_docx.py` | Собирает `doc/docx/ПЗ.docx` и приложения |
| `python3 src/draw_flowchart_2_2.py` | Рис. 2.2 → `doc/output/`, `doc/screenshots/` |
| `python3 src/draw_structure_2_1.py` | Рис. 2.1 |
| `python3 src/draw_geometry_course.py` | Геометрия курса |
| `python3 src/draw_section_4.py` | Раздел 4 (графики, табл. 4.1) |
| `python3 src/draw_appendix_B.py` | Приложение В |

После прогона миссии в симуляторе скопируйте CSV в `doc/output/logs/` (создайте папку при необходимости) и снова запустите `draw_section_4.py`.

## Программа в симуляторе

1. В MUR IDE откройте `doc/program/waypoint_mission/waypoint_mission.py`.
2. Запустите симулятор, включите **Remote mode**.
3. Нажмите **F5** в IDE.
4. Точки маршрута — `doc/program/waypoint_mission/waypoints.csv`.

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError: matplotlib` | `pip install matplotlib numpy` |
| `draw_section_4` не находит логи | Положите `mission_*.csv` в `doc/output/logs/` |
| `build_docx` падает на word_manager | Работайте с готовыми `doc/docx/*.docx` |
| Скрипт пишет в не ту папку | Запускайте из корня пакета, не из `src/` |

## Автор

Укажите ФИО группы при выкладке на GitHub.
