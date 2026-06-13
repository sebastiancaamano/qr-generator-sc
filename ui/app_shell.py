"""
App Shell — QR Generator SC
Top navigation bar + sidebar + main content layout.
Follows Flat Design System tokens throughout.
"""

import flet as ft

from i18n.translation_manager import TranslationManager, init_i18n, t
from services.qr_service import QRService
from services.svg_export_service import SvgExportService
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage
from storage.settings_storage import SettingsStorage
from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE
from ui.components import FlatComponents
from ui.generator_view import GeneratorView
from ui.history_panel import HistoryPanel
from ui.project_panel import ProjectPanel


class AppShell:
    """
    Root layout builder.
    Wires ThemeManager → all child views.
    """

    SIDEBAR_W = 240

    def __init__(self, page: ft.Page):
        self._page = page
        self._settings = SettingsStorage()
        self._i18n = TranslationManager(
            self._settings, language=self._settings.language
        )
        init_i18n(self._i18n)
        self._theme = ThemeManager(self._settings.theme_mode, storage=self._settings)
        self._storage = HistoryStorage()
        self._project_storage = ProjectStorage()
        self._current_project = self._project_storage.selected()
        self._svc = QRService(
            self._storage,
            project_storage=self._project_storage,
            foreground_color=self._settings.qr_foreground_color,
            background_color=self._settings.qr_background_color,
            size=self._settings.qr_size,
            margin=self._settings.qr_margin,
        )
        self._svg_svc = SvgExportService(
            self._storage,
            project_storage=self._project_storage,
        )
        self._comp = FlatComponents(self._theme)

        self._setup_page()
        self._build()

    # ── Page Setup ────────────────────────────────────────────

    def _setup_page(self) -> None:
        p = self._page
        p.title = "QR Generator SC"
        p.window.icon = "/logo_qr_generator_sc.ico"
        p.window.width = 980
        p.window.height = 680
        p.window.min_width = 820
        p.window.min_height = 560
        p.window.maximized = True
        p.padding = 0
        p.spacing = 0
        p.bgcolor = self._theme.c("surface")
        p.fonts = {
            "Inter": "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2"
        }
        p.theme = ft.Theme(font_family="Inter")
        p.theme_mode = self._theme.theme_mode

    # ── Build ─────────────────────────────────────────────────

    def _build(self) -> None:
        t_theme = self._theme

        # ── TopBar ────────────────────────────────────────────
        topbar = self._build_topbar()

        # ── Sidebar (project + history) ─────────────────────────
        self._project_panel = ProjectPanel(
            theme=t_theme,
            storage=self._project_storage,
            page=self._page,
            on_select=self._on_project_select,
        )

        self._history_panel = HistoryPanel(
            theme=t_theme,
            storage=self._storage,
            on_select=self._on_history_select,
            active_project_id=self._current_project.id,
            active_project_name=self._current_project.name,
            project_storage=self._project_storage,
            page=self._page,
        )

        sidebar = ft.Container(
            content=ft.Column(
                [self._project_panel, self._comp.divider(), self._history_panel],
                spacing=0,
                expand=True,
            ),
            width=self.SIDEBAR_W,
            bgcolor=t_theme.c("sidebar_bg"),
            border=ft.border.Border.only(
                right=ft.border.BorderSide(1, t_theme.c("border"))
            ),
        )

        # ── Generator (main content) ──────────────────────────
        self._gen_view = GeneratorView(
            theme=t_theme,
            qr_service=self._svc,
            svg_service=self._svg_svc,
            settings=self._settings,
            on_exported=self._on_exported,
            page=self._page,
            project=self._current_project,
        )

        main = ft.Container(
            content=ft.Column(
                [self._gen_view],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=SPACE["xl"],
            bgcolor=t_theme.c("surface"),
        )

        body = ft.Row(
            [sidebar, main],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        self._root = ft.Column(
            [topbar, body],
            spacing=0,
            expand=True,
        )

        self._page.controls = [self._root]
        self._page.update()

    def _active_flag(self) -> str:
        """Return emoji for the currently active language."""
        return "🇺🇸" if self._i18n.language == "en" else "🇪🇸"

    def _build_topbar(self) -> ft.Container:
        t_theme = self._theme

        logo = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.QR_CODE, color="#FFFFFF", size=18),
                    bgcolor=t_theme.c("primary"),
                    border_radius=RADIUS["sm"],
                    padding=SPACE["xs"],
                ),
                ft.Text(
                    "QR Generator SC",
                    size=FONT_SCALE["base"],
                    weight=ft.FontWeight.W_700,
                    color=t_theme.c("text"),
                    font_family=FONT_PRIMARY,
                ),
            ],
            spacing=SPACE["sm"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        icon_btn_style = ft.ButtonStyle(
            shape=ft.CircleBorder(),
            padding=SPACE["xs"],
            overlay_color=t_theme.c("hover"),
        )

        self._theme_icon = (
            ft.Icons.DARK_MODE_OUTLINED
            if self._theme.mode == "light"
            else ft.Icons.LIGHT_MODE_OUTLINED
        )

        self._theme_btn = ft.IconButton(
            icon=self._theme_icon,
            icon_color=t_theme.c("text2"),
            tooltip=t("tooltip_toggle_theme"),
            on_click=self._on_theme_toggle,
            style=icon_btn_style,
        )

        self._language_btn = ft.Container(
            content=ft.Row(
                [ft.Text(self._active_flag(), size=18)],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=40,
            height=40,
            border_radius=20,
            bgcolor=t_theme.c("surface"),
            on_click=self._on_language_toggle,
        )

        topbar_actions = ft.Row(
            [self._theme_btn, self._language_btn],
            spacing=SPACE["xs"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Row(
                [logo, ft.Container(expand=True), topbar_actions],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=t_theme.c("surface"),
            border=ft.border.Border.only(
                bottom=ft.border.BorderSide(1, t_theme.c("border"))
            ),
            padding=ft.Padding.symmetric(horizontal=SPACE["xl"], vertical=SPACE["md"]),
            height=56,
        )

    def _save_generator_state(self) -> dict:
        """Preserve form and preview state across UI rebuilds."""
        return {
            "content": self._gen_view._content_value,
            "qr_type": self._gen_view._qr_type_value,
            "field_values": dict(self._gen_view._field_values),
            "build_error": self._gen_view._build_error,
            "fg_color": self._gen_view._foreground_color,
            "bg_color": self._gen_view._background_color,
            "size": self._gen_view._qr_size_value,
            "margin": self._gen_view._qr_margin_value,
            "preview": self._gen_view._preview_bytes,
            "logo_image": self._gen_view._logo_image,
            "logo_preview": self._gen_view._logo_preview_bytes,
            "logo_size_percent": self._gen_view._logo_size_percent,
            "logo_opacity": self._gen_view._logo_opacity,
        }

    def _restore_generator_state(self, saved_state: dict) -> None:
        self._gen_view._content_value = saved_state["content"]
        self._gen_view._qr_type_value = saved_state["qr_type"]
        self._gen_view._field_values = saved_state["field_values"]
        self._gen_view._build_error = saved_state["build_error"]
        self._gen_view._foreground_color = saved_state["fg_color"]
        self._gen_view._background_color = saved_state["bg_color"]
        self._gen_view._qr_size_value = saved_state["size"]
        self._gen_view._qr_margin_value = saved_state["margin"]
        self._gen_view._preview_bytes = saved_state["preview"]
        self._gen_view._logo_image = saved_state["logo_image"]
        self._gen_view._logo_preview_bytes = saved_state["logo_preview"]
        self._gen_view._logo_size_percent = saved_state["logo_size_percent"]
        self._gen_view._logo_opacity = saved_state["logo_opacity"]
        self._gen_view.update()

    def _rebuild_preserve_state(self) -> None:
        saved_state = self._save_generator_state()
        self._build()
        self._restore_generator_state(saved_state)

    # ── Callbacks ─────────────────────────────────────────────

    def _on_exported(self) -> None:
        self._history_panel.refresh(
            active_project_id=self._current_project.id,
            active_project_name=self._current_project.name,
        )
        self._project_panel.refresh()

    def _on_history_select(self, entry) -> None:
        self._gen_view.load_entry(entry)

    def _on_project_select(self, project) -> None:
        self._current_project = project
        self._history_panel.refresh(
            active_project_id=project.id,
            active_project_name=project.name,
        )
        self._gen_view.set_project(project)

    def _on_theme_toggle(self, _) -> None:
        self._theme.toggle()
        self._page.theme_mode = self._theme.theme_mode
        self._page.bgcolor = self._theme.c("surface")
        self._rebuild_preserve_state()

    def _on_language_toggle(self, _) -> None:
        new_language = "es" if self._i18n.language == "en" else "en"
        self._i18n.set_language(new_language)
        self._rebuild_preserve_state()
