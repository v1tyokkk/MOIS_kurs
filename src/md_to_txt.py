#!/usr/bin/env python3
"""Конвертация KURS/*.md → *.txt без markdown-разметки."""

from __future__ import annotations

import re
from pathlib import Path

KURS = Path(__file__).resolve().parent.parent / 'doc'

REPORTS = [
    ("ПЗ.md", "ПЗ.txt", "main"),
    ("ПЗ_А.md", "ПЗ_А.txt", "appendix"),
    ("ПЗ_Б.md", "ПЗ_Б.txt", "appendix"),
    ("ПЗ_В.md", "ПЗ_В.txt", "appendix"),
]

RE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
RE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
RE_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
RE_MD_HEADING = re.compile(r"^#+\s*")
RE_FENCE = re.compile(r"^```")


def strip_md_markup(line: str) -> str:
    s = line
    if RE_MD_HEADING.match(s):
        s = RE_MD_HEADING.sub("", s)
    s = RE_BOLD.sub(r"\1", s)
    s = RE_ITALIC.sub(r"\1", s)
    s = RE_LINK.sub(r"\1", s)
    return s.rstrip()


def skip_title_block(lines: list[str], mode: str) -> list[str]:
    if mode == "main":
        for i, line in enumerate(lines):
            if line.strip() == "СОДЕРЖАНИЕ":
                return lines[i:]
        return lines

    # appendix: оставить «ПРИЛОЖЕНИЕ …», убрать титул до СОДЕРЖАНИЕ
    out: list[str] = []
    i = 0
    if lines and lines[0].strip().upper().startswith("ПРИЛОЖЕНИЕ"):
        out.append(lines[0].strip())
        i = 1
    for j in range(i, len(lines)):
        if lines[j].strip() == "СОДЕРЖАНИЕ":
            return out + lines[j:]
    return out if out else lines


def normalize_output(lines: list[str]) -> str:
    cleaned: list[str] = []
    in_fence = False
    for raw in lines:
        if RE_FENCE.match(raw.strip()):
            in_fence = not in_fence
            continue
        line = strip_md_markup(raw) if not in_fence else raw.rstrip()
        cleaned.append(line)

    blocks: list[str] = []
    prev_empty = False
    for line in cleaned:
        if not line.strip():
            if not prev_empty and blocks:
                blocks.append("")
            prev_empty = True
            continue
        prev_empty = False
        blocks.append(line)

    while blocks and not blocks[0].strip():
        blocks.pop(0)
    while blocks and not blocks[-1].strip():
        blocks.pop()

    # пустая строка после СОДЕРЖАНИЕ и перед первым разделом CAPS
    result: list[str] = []
    for i, line in enumerate(blocks):
        result.append(line)
        if line.strip() == "СОДЕРЖАНИЕ" and i + 1 < len(blocks) and blocks[i + 1].strip():
            result.append("")
    return "\n".join(result) + "\n"


def convert_file(src: Path, dst: Path, mode: str) -> None:
    text = src.read_text(encoding="utf-8")
    lines = text.splitlines()
    lines = skip_title_block(lines, mode)
    dst.write_text(normalize_output(lines), encoding="utf-8")
    print(f"OK: {dst.name} ({dst.stat().st_size} байт)")


def main() -> None:
    for md_name, txt_name, mode in REPORTS:
        src = KURS / md_name
        if not src.is_file():
            print(f"Пропуск (нет файла): {md_name}")
            continue
        convert_file(src, KURS / txt_name, mode)
    print("\nГотово: текстовые файлы в", KURS)


if __name__ == "__main__":
    main()
