"""
QR Generator SC — Entry Point
Run: python main.py
"""

import flet as ft

from ui.app_shell import AppShell


def main(page: ft.Page) -> None:
    AppShell(page)


if __name__ == "__main__":
    ft.run(main)
