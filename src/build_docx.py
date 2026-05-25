#!/usr/bin/env python3
"""Сборка DOCX из KURS/*.txt через word-manager."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx_build_lib import WORD_MANAGER_SRC, build_all  # noqa: E402

KURS = Path(__file__).resolve().parent.parent / 'doc'


def main() -> None:
    if not WORD_MANAGER_SRC.is_dir():
        print(f"Не найден word-manager: {WORD_MANAGER_SRC}", file=sys.stderr)
        sys.exit(1)

    paths = build_all(KURS)
    for path in paths:
        print(f"OK: {path}")
    print(f"\nГотово: {len(paths)} файлов в {KURS / 'docx'}")


if __name__ == "__main__":
    main()
