"""
UI Components
Reusable component factory for QR Generator SC.
All sizing, color, and spacing follow Flat tokens.
"""

import flet as ft

from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE


class FlatComponents:
    """
    Stateless factory — call methods to get pre-styled Flet controls.
    Pass the ThemeManager instance so components always read live tokens.
    """

    def __init__(self, theme: ThemeManager):
        self.theme = theme

    # ── Typography ────────────────────────────────────────────

    def heading(self, text: str, size: str = "xl") -> ft.Text:
        return ft.Text(
            text,
            size=FONT_SCALE[size],
            weight=ft.FontWeight.W_700,
            color=self.theme.c("text"),
            font_family=FONT_PRIMARY,
        )

    def label(self, text: str, size: str = "sm", color_token: str = "text2") -> ft.Text:
        return ft.Text(
            text,
            size=FONT_SCALE[size],
            weight=ft.FontWeight.W_500,
            color=self.theme.c(color_token),
            font_family=FONT_PRIMARY,
        )

    def caption(self, text: str) -> ft.Text:
        return ft.Text(
            text,
            size=FONT_SCALE["xs"],
            color=self.theme.c("text3"),
            font_family=FONT_PRIMARY,
        )

    # ── Inputs ────────────────────────────────────────────────

    def text_field(
        self,
        label: str = "",
        hint: str = "",
        multiline: bool = False,
        on_change=None,
        value: str = "",
    ) -> ft.TextField:
        return ft.TextField(
            label=label,
            hint_text=hint,
            value=value,
            multiline=multiline,
            min_lines=1 if not multiline else 3,
            max_lines=1 if not multiline else 6,
            border_color=self.theme.c("border"),
            focused_border_color=self.theme.c("primary"),
            label_style=ft.TextStyle(
                color=self.theme.c("text2"), size=FONT_SCALE["sm"]
            ),
            text_style=ft.TextStyle(
                color=self.theme.c("text"), size=FONT_SCALE["base"]
            ),
            hint_style=ft.TextStyle(color=self.theme.c("text3"), size=FONT_SCALE["sm"]),
            bgcolor=self.theme.c("input_bg"),
            border_radius=RADIUS["md"],
            cursor_color=self.theme.c("primary"),
            on_change=on_change,
        )

    def dropdown(
        self,
        options: list | None = None,
        value: str = "",
        on_change=None,
        labeled_options: list | None = None,
    ) -> ft.Dropdown:
        if labeled_options:
            dd_options = [
                ft.dropdown.Option(key=key, text=label)
                for key, label in labeled_options
            ]
        else:
            dd_options = [ft.dropdown.Option(key=o, text=o) for o in (options or [])]
        return ft.Dropdown(
            options=dd_options,
            value=value,
            border_color=self.theme.c("border"),
            focused_border_color=self.theme.c("primary"),
            bgcolor=self.theme.c("input_bg"),
            fill_color=self.theme.c("surface2"),
            hover_color=self.theme.c("hover"),
            color=self.theme.c("text"),
            text_style=ft.TextStyle(color=self.theme.c("text"), size=FONT_SCALE["sm"]),
            label_style=ft.TextStyle(
                color=self.theme.c("text2"), size=FONT_SCALE["sm"]
            ),
            menu_style=ft.MenuStyle(
                bgcolor=self.theme.c("surface"),
                side=ft.BorderSide(1, self.theme.c("border")),
                shadow_color=self.theme.c("border"),
            ),
            border_radius=RADIUS["md"],
            on_select=on_change,
        )

    # ── Buttons ───────────────────────────────────────────────

    def primary_button(
        self,
        text: str,
        icon=None,
        on_click=None,
        expand: bool = False,
    ) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            content=text,
            icon=icon,
            on_click=on_click,
            bgcolor=self.theme.c("primary"),
            color="#FFFFFF",
            elevation=0,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS["md"]),
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["lg"], vertical=SPACE["md"]
                ),
                text_style=ft.TextStyle(
                    size=FONT_SCALE["sm"],
                    weight=ft.FontWeight.W_600,
                    font_family=FONT_PRIMARY,
                ),
            ),
            expand=expand,
        )

    def ghost_button(self, text: str, icon=None, on_click=None) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            content=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, self.theme.c("border")),
                shape=ft.RoundedRectangleBorder(radius=RADIUS["md"]),
                color=self.theme.c("text"),
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["lg"], vertical=SPACE["md"]
                ),
                text_style=ft.TextStyle(
                    size=FONT_SCALE["sm"],
                    weight=ft.FontWeight.W_500,
                    font_family=FONT_PRIMARY,
                ),
            ),
        )

    def icon_button(self, icon, tooltip: str = "", on_click=None) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            icon_color=self.theme.c("text2"),
            tooltip=tooltip,
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"]),
            ),
        )

    # ── Cards ─────────────────────────────────────────────────

    def card(self, content: ft.Control, padding: int = SPACE["xl"]) -> ft.Container:
        return ft.Container(
            content=content,
            bgcolor=self.theme.c("card_bg"),
            border=ft.border.Border.all(1, self.theme.c("border")),
            border_radius=RADIUS["lg"],
            padding=padding,
        )

    def divider(self) -> ft.Divider:
        return ft.Divider(height=1, color=self.theme.c("border"), thickness=1)

    # ── Badges / Pills ────────────────────────────────────────

    def badge(
        self, text: str, color_token: str = "primary", text_token: str = None
    ) -> ft.Container:
        return ft.Container(
            content=ft.Text(
                text,
                size=FONT_SCALE["xs"],
                color=self.theme.c(text_token or color_token),
                weight=ft.FontWeight.W_600,
                font_family=FONT_PRIMARY,
            ),
            bgcolor=self.theme.c(color_token) + "1A",  # ~10% opacity
            border_radius=RADIUS["full"],
            padding=ft.Padding.symmetric(horizontal=SPACE["sm"], vertical=2),
        )

    # ── Snackbar ──────────────────────────────────────────────

    def snack(self, page: ft.Page, message: str, success: bool = True) -> None:
        color = self.theme.c("success") if success else self.theme.c("danger")
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="#FFFFFF", font_family=FONT_PRIMARY),
            bgcolor=color,
            duration=2500,
        )
        page.snack_bar.open = True
        page.update()
