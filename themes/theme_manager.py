"""
Theme Manager
Handles light/dark mode token resolution and user preference persistence.
"""

import flet as ft

from themes.tokens import DARK, LIGHT


class ThemeManager:
    """Single source of truth for the active color tokens."""

    def __init__(self, mode: str = "light", storage=None):
        self._mode = mode if mode in ("light", "dark") else "light"
        self._storage = storage

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def theme_mode(self) -> ft.ThemeMode:
        return ft.ThemeMode.DARK if self._mode == "dark" else ft.ThemeMode.LIGHT

    @property
    def colors(self) -> dict:
        return DARK if self._mode == "dark" else LIGHT

    def toggle(self) -> str:
        new_mode = "dark" if self._mode == "light" else "light"
        self.set_mode(new_mode)
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode in ("light", "dark"):
            self._mode = mode
            if self._storage is not None:
                try:
                    self._storage.set_theme_mode(mode)
                except Exception:
                    pass

    def c(self, token: str) -> str:
        """Shorthand: theme.c('primary')"""
        return self.colors.get(token, "#000000")

    def is_dark(self) -> bool:
        return self._mode == "dark"
