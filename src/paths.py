"""Пути пакета kurs01 (doc + src)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "doc"
OUT = DOC / "output"
SHOTS = DOC / "screenshots"
MISSION = DOC / "program" / "waypoint_mission"
