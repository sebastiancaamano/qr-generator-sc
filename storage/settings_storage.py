"""
Settings Storage — QR Generator SC
Stores user preferences such as theme mode and QR color configuration.
"""

import json
from pathlib import Path

DEFAULT_SETTINGS = {
    "theme_mode": "light",
    "qr_foreground_color": "#000000",
    "qr_background_color": "#FFFFFF",
    "qr_size": 512,
    "qr_margin": 4,
    "last_qr_type": "URL",
    "logo_size_percent": 20,
    "logo_opacity": 100,
    "language": "en",
    "last_export_format": "png",
}

SETTINGS_FILE = Path.home() / ".qr_generator_sc" / "settings.json"


class SettingsStorage:
    """JSON-backed local settings storage."""

    def __init__(self, path: Path = SETTINGS_FILE):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = self._read()

    def _read(self) -> dict:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return DEFAULT_SETTINGS.copy()
                return {**DEFAULT_SETTINGS, **data}
        except (json.JSONDecodeError, FileNotFoundError):
            return DEFAULT_SETTINGS.copy()

    def _write(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, ensure_ascii=False, indent=2)

    @property
    def theme_mode(self) -> str:
        return self._settings.get("theme_mode", DEFAULT_SETTINGS["theme_mode"])

    def set_theme_mode(self, mode: str) -> None:
        if mode in ("light", "dark"):
            self._settings["theme_mode"] = mode
            self._write()

    @property
    def qr_foreground_color(self) -> str:
        return self._settings.get(
            "qr_foreground_color", DEFAULT_SETTINGS["qr_foreground_color"]
        )

    @property
    def qr_background_color(self) -> str:
        return self._settings.get(
            "qr_background_color", DEFAULT_SETTINGS["qr_background_color"]
        )

    def set_qr_colors(self, foreground_color: str, background_color: str) -> None:
        self._settings["qr_foreground_color"] = foreground_color
        self._settings["qr_background_color"] = background_color
        self._write()

    @property
    def qr_size(self) -> int:
        return int(self._settings.get("qr_size", DEFAULT_SETTINGS["qr_size"]))

    def set_qr_size(self, size: int) -> None:
        if size in (256, 512, 1024, 2048):
            self._settings["qr_size"] = size
            self._write()

    @property
    def qr_margin(self) -> int:
        return int(self._settings.get("qr_margin", DEFAULT_SETTINGS["qr_margin"]))

    def set_qr_margin(self, margin: int) -> None:
        if margin in (0, 2, 4, 8):
            self._settings["qr_margin"] = margin
            self._write()

    @property
    def last_qr_type(self) -> str:
        return self._settings.get("last_qr_type", DEFAULT_SETTINGS["last_qr_type"])

    def set_last_qr_type(self, qr_type: str) -> None:
        # V3: all registered QR types are valid
        from qr_types import QR_TYPES

        if qr_type in QR_TYPES:
            self._settings["last_qr_type"] = qr_type
            self._write()

    @property
    def logo_size_percent(self) -> int:
        return int(
            self._settings.get(
                "logo_size_percent", DEFAULT_SETTINGS["logo_size_percent"]
            )
        )

    def set_logo_size_percent(self, size_percent: int) -> None:
        if size_percent in (10, 15, 20, 25):
            self._settings["logo_size_percent"] = size_percent
            self._write()

    @property
    def logo_opacity(self) -> int:
        return int(self._settings.get("logo_opacity", DEFAULT_SETTINGS["logo_opacity"]))

    def set_logo_opacity(self, opacity: int) -> None:
        if 0 <= opacity <= 100:
            self._settings["logo_opacity"] = opacity
            self._write()

    @property
    def language(self) -> str:
        return self._settings.get("language", DEFAULT_SETTINGS["language"])

    def set_language(self, language: str) -> None:
        if language in ("en", "es"):
            self._settings["language"] = language
            self._write()

    @property
    def last_export_format(self) -> str:
        return self._settings.get(
            "last_export_format", DEFAULT_SETTINGS["last_export_format"]
        )

    def set_last_export_format(self, export_format: str) -> None:
        if export_format in ("png", "svg"):
            self._settings["last_export_format"] = export_format
            self._write()
