"""
Storage Service — QR Generator SC
JSON-based local persistence for QR history.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from models.qr_entry import QREntry

HISTORY_FILE = Path.home() / ".qr_generator_sc" / "history.json"


class HistoryStorage:
    """CRUD over a local JSON file. Thread-safe for single-user desktop use."""

    def __init__(self, path: Path = HISTORY_FILE):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write([])

    # ── Public API ────────────────────────────────────────────

    def all(self, project_id: Optional[str] = None) -> List[QREntry]:
        entries = [QREntry.from_dict(d) for d in self._read()]
        if project_id:
            return [entry for entry in entries if entry.project_id == project_id]
        return entries

    def add(self, entry: QREntry) -> None:
        entries = self._read()
        entries.insert(0, entry.to_dict())  # newest first
        self._write(entries)

    def delete(self, entry_id: str) -> None:
        entries = [e for e in self._read() if e["id"] != entry_id]
        self._write(entries)

    def clear(self) -> None:
        self._write([])

    # ── Private ───────────────────────────────────────────────

    def _read(self) -> list:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write(self, data: list) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
