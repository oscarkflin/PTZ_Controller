"""Persistent, editable labels for camera preset numbers."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_PRESETS = [
    {"number": 1, "name": "Pulpit"},
    {"number": 2, "name": "Piano"},
    {"number": 3, "name": "Worship team"},
    {"number": 4, "name": "Wide stage"},
    {"number": 5, "name": "Audience"},
]


class PresetStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".ptz_controller" / "presets.json"

    def load(self) -> list[dict[str, object]]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            presets = [
                {"number": int(item["number"]), "name": str(item["name"]).strip()}
                for item in raw
                if 0 <= int(item["number"]) <= 15 and str(item["name"]).strip()
            ]
            if len({item["number"] for item in presets}) == len(presets):
                return sorted(presets, key=lambda item: int(item["number"]))
        except (FileNotFoundError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            pass
        return [item.copy() for item in DEFAULT_PRESETS]

    def save(self, presets: list[dict[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(presets, key=lambda item: int(item["number"]))
        self.path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
