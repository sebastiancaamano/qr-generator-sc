"""
Generator View — QR Generator SC
Main content: input form + QR preview card.
"""

import io
from importlib.metadata import files
from pathlib import Path

import flet as ft
from PIL import Image

try:
    from flet.file_picker import FilePicker
except ImportError:
    FilePicker = ft.FilePicker

from i18n.translation_manager import get_i18n
from i18n.translation_manager import t as tr
from qr_types import QR_TYPES
from qr_types.base import FieldKind
from services.logo_service import LogoService
from services.pdf_export_service import PdfExportError, PdfExportService
from services.qr_content_service import QRContentService
from services.qr_service import QRService
from services.svg_export_service import SvgExportError, SvgExportService
from storage.settings_storage import SettingsStorage
from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE
from ui.components import FlatComponents

QR_SIZE_OPTIONS = [128, 256, 512, 1024]
QR_MARGIN_OPTIONS = [0, 2, 4, 8]
LOGO_SIZE_OPTIONS = [5, 10, 15, 20, 25, 30, 35, 40]
COLOR_SWATCHES = [
    "#000000",
    "#FFFFFF",
    "#F2673C",
    "#8B5CF6",
    "#16A34A",
    "#D97706",
    "#374151",
    "#9CA3AF",
]


class GeneratorView(ft.Column):
    """
    Center panel:
      - QR type selector
      - Content text field
      - Customization settings
      - Live QR preview card
    """

    def __init__(
        self,
        theme: ThemeManager,
        qr_service: QRService,
        svg_service: SvgExportService,
        settings: SettingsStorage,
        on_exported,  # callback → refresh history
        page: ft.Page,
        project=None,
    ):
        super().__init__()
        self._theme = theme
        self._svc = qr_service
        self._svg_svc = svg_service
        self._settings = settings
        self._on_exported = on_exported
        self._page = page
        self._project = project
        self._comp = FlatComponents(theme)
        self._logo_svc = LogoService()
        self._content_svc = QRContentService()
        self._pdf_svc = PdfExportService(
            self._svc._storage,
            self._svc._project_storage,
        )

        self._content_value = ""
        self._build_error = None
        self._qr_type_value = self._settings.last_qr_type or "URL"
        if self._qr_type_value not in QR_TYPES:
            self._qr_type_value = "URL"
        self._field_values = self._content_svc.default_fields(self._qr_type_value)
        self._foreground_color = self._settings.qr_foreground_color
        self._background_color = self._settings.qr_background_color
        self._qr_size_value = self._settings.qr_size
        self._qr_margin_value = self._settings.qr_margin
        self._preview_bytes = None

        # Logo settings
        self._logo_image = None
        self._logo_preview_bytes = None
        self._logo_size_percent = self._settings.logo_size_percent
        self._logo_opacity = self._settings.logo_opacity / 100.0  # Convert to 0-1 range

        self._svc.set_colors(self._foreground_color, self._background_color)
        self._svc.set_size(self._qr_size_value)
        self._svc.set_margin(self._qr_margin_value)

        self.spacing = SPACE["xl"]
        self.expand = True
        self._build()

    def set_project(self, project) -> None:
        self._project = project
        self._rebuild_controls()
        self.update()

    # ── Public ────────────────────────────────────────────────

    def load_entry(self, entry) -> None:
        """Pre-fill form from a history entry."""
        display_name, fields = self._content_svc.parse_history_entry(
            entry.qr_type,
            entry.content,
        )
        self._qr_type_value = display_name
        self._field_values = {
            **self._content_svc.default_fields(display_name),
            **fields,
        }
        self._settings.set_last_qr_type(self._qr_type_value)
        self._sync_content_from_fields()
        self._refresh_preview()
        self._rebuild_controls()
        self.update()

    # ── Private ───────────────────────────────────────────────

    def _build(self) -> None:
        self._rebuild_controls()

    def _rebuild_controls(self) -> None:
        t = self._theme

        # ── Type Selector ─────────────────────────────────────
        self._type_dd = self._comp.dropdown(
            labeled_options=[
                (qr_type, get_i18n().translate_qr_type(qr_type)) for qr_type in QR_TYPES
            ],
            value=self._qr_type_value,
            on_change=self._on_type_change,
        )

        # ── Dynamic fields per QR type ──────────────────────
        dynamic_fields = self._build_dynamic_fields()
        self._error_text = ft.Text(
            (
                get_i18n().translate_validation(self._build_error)
                if self._build_error
                else ""
            ),
            size=FONT_SCALE["xs"],
            color=t.c("danger"),
            font_family=FONT_PRIMARY,
            visible=bool(self._build_error),
        )
        payload_preview = self._truncate_payload(self._content_value)
        self._payload_text = ft.Text(
            payload_preview,
            size=FONT_SCALE["xs"],
            color=t.c("text3"),
            font_family=FONT_PRIMARY,
            visible=bool(payload_preview),
            selectable=True,
        )

        # ── Logo Card ─────────────────────────────────────────
        logo_card = self._build_logo_card()

        # ── Customization Manager ─────────────────────────────
        customization_card = self._comp.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                tr("section_customization"),
                                size=FONT_SCALE["lg"],
                                weight=ft.FontWeight.W_700,
                                color=t.c("text"),
                                font_family=FONT_PRIMARY,
                            ),
                            ft.Container(expand=True),
                            self._comp.badge(
                                f"{self._qr_size_value}px",
                                "secondary",
                                text_token="label",
                            ),
                            self._comp.badge(
                                tr("badge_margin", value=self._qr_margin_value),
                                "secondary",
                                text_token="label",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=SPACE["sm"]),
                    ft.Row(
                        [
                            self._build_color_control(
                                tr("color_qr"),
                                self._foreground_color,
                                self._on_foreground_text_change,
                                self._on_foreground_palette,
                            ),
                            self._build_color_control(
                                tr("color_background"),
                                self._background_color,
                                self._on_background_text_change,
                                self._on_background_palette,
                            ),
                        ],
                        spacing=SPACE["lg"],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    self._comp.label(tr("label_size")),
                                    self._comp.dropdown(
                                        options=[str(size) for size in QR_SIZE_OPTIONS],
                                        value=str(self._qr_size_value),
                                        on_change=self._on_size_change,
                                    ),
                                    ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.INFO_OUTLINED,
                                                size=12,
                                                color=self._theme.c("text2"),
                                            ),
                                            ft.Text(
                                                tr("size_export_hint"),
                                                size=FONT_SCALE["xs"],
                                                color=self._theme.c("text2"),
                                                font_family=FONT_PRIMARY,
                                            ),
                                        ],
                                        spacing=SPACE["xs"],
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                ],
                                spacing=SPACE["sm"],
                                expand=True,
                            ),
                            ft.Column(
                                [
                                    self._comp.label(tr("label_margin")),
                                    self._comp.dropdown(
                                        options=[
                                            str(margin) for margin in QR_MARGIN_OPTIONS
                                        ],
                                        value=str(self._qr_margin_value),
                                        on_change=self._on_margin_change,
                                    ),
                                ],
                                spacing=SPACE["sm"],
                                expand=True,
                            ),
                        ],
                        spacing=SPACE["lg"],
                    ),
                ],
                spacing=SPACE["lg"],
            ),
            padding=SPACE["lg"],
        )

        # ── Buttons ───────────────────────────────────────────
        btn_generate = self._comp.primary_button(
            tr("generate_qr"),
            icon=ft.Icons.QR_CODE,
            on_click=self._on_generate,
            expand=True,
        )
        btn_download = self._comp.ghost_button(
            tr("download_png"),
            icon=ft.Icons.DOWNLOAD_OUTLINED,
            on_click=self._on_download,
        )

        form_card = self._comp.card(
            ft.Column(
                [
                    ft.Text(
                        tr("create_qr_code"),
                        size=FONT_SCALE["lg"],
                        weight=ft.FontWeight.W_700,
                        color=t.c("text"),
                        font_family=FONT_PRIMARY,
                    ),
                    ft.Text(
                        tr("create_qr_subtitle"),
                        size=FONT_SCALE["sm"],
                        color=t.c("text2"),
                        font_family=FONT_PRIMARY,
                    ),
                    ft.Container(height=SPACE["xs"]),
                    ft.Row(
                        [
                            ft.Text(
                                tr(
                                    "project_label",
                                    name=(
                                        self._project.name
                                        if self._project
                                        else tr("project_general")
                                    ),
                                ),
                                size=FONT_SCALE["xs"],
                                color=t.c("text2"),
                                font_family=FONT_PRIMARY,
                            ),
                        ],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    ft.Text(
                        tr("type_label"),
                        size=FONT_SCALE["xs"],
                        weight=ft.FontWeight.W_600,
                        color=t.c("text3"),
                        font_family=FONT_PRIMARY,
                    ),
                    self._type_dd,
                    ft.Container(height=4),
                    *dynamic_fields,
                    self._error_text,
                    ft.Container(height=2),
                    self._payload_text,
                    ft.Container(height=SPACE["sm"]),
                    customization_card,
                    ft.Container(height=SPACE["sm"]),
                    logo_card,
                    ft.Container(height=SPACE["sm"]),
                    ft.Row(
                        [btn_generate, btn_download],
                        spacing=SPACE["sm"],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    self._build_export_as_section(),
                ],
                spacing=SPACE["sm"],
            )
        )

        # ── Preview Card ──────────────────────────────────────
        preview_content = self._build_preview()
        preview_card = self._comp.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                tr("section_qr_preview"),
                                size=FONT_SCALE["base"],
                                weight=ft.FontWeight.W_600,
                                color=t.c("text"),
                                font_family=FONT_PRIMARY,
                            ),
                            ft.Container(expand=True),
                            self._comp.badge(
                                get_i18n().translate_qr_type(self._qr_type_value),
                                "primary",
                            ),
                        ],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    preview_content,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        self.controls = [form_card, preview_card]

    def _build_export_as_section(self) -> ft.Control:
        t_theme = self._theme

        svg_radio = ft.Radio(
            label=tr("export_format_svg"),
            value="svg",
            fill_color=t_theme.c("primary"),
            label_style=ft.TextStyle(
                color=t_theme.c("text"),
                size=FONT_SCALE["sm"],
                font_family=FONT_PRIMARY,
            ),
        )

        pdf_radio = ft.Radio(
            label=tr("export_format_pdf"),
            value="pdf",
            fill_color=t_theme.c("primary"),
            label_style=ft.TextStyle(
                color=t_theme.c("text"),
                size=FONT_SCALE["sm"],
                font_family=FONT_PRIMARY,
            ),
        )

        self._export_as_group = ft.RadioGroup(
            value=self._settings.last_export_format or "svg",
            on_change=self._on_export_format_change,
            content=ft.Row(
                [
                    svg_radio,
                    pdf_radio,
                ],
                spacing=SPACE["lg"],
            ),
        )

        btn_export = self._comp.primary_button(
            tr("export"),
            icon=ft.Icons.IMAGE_OUTLINED,
            on_click=self._on_export_selected,
        )

        return ft.Column(
            [
                ft.Text(
                    tr("export_as"),
                    size=FONT_SCALE["xs"],
                    weight=ft.FontWeight.W_600,
                    color=t_theme.c("text3"),
                    font_family=FONT_PRIMARY,
                ),
                self._export_as_group,
                btn_export,
            ],
            spacing=SPACE["sm"],
        )

    def _on_export_selected(self, e) -> None:

        export_type = self._export_as_group.value

        if export_type == "svg":
            self._on_export_svg(e)

        elif export_type == "pdf":
            self._on_export_pdf(e)

    def _prepare_logo_for_export(self):
        """Resize and apply opacity to logo for file export."""
        if not self._logo_image:
            return None
        try:
            logo = self._logo_svc.resize_logo(
                self._logo_image.copy(),
                self._qr_size_value,
                self._logo_size_percent,
            )
            return self._logo_svc.apply_opacity(logo, self._logo_opacity)
        except Exception:
            return None

    def _on_export_format_change(self, e) -> None:
        self._settings.set_last_export_format(e.control.value)

    def _build_dynamic_fields(self) -> list[ft.Control]:
        """Render form controls according to the selected QR type."""
        t_theme = self._theme
        i18n = get_i18n()
        controls: list[ft.Control] = []

        for field_def in self._content_svc.field_definitions(self._qr_type_value):
            value = self._field_values.get(field_def.key, "")
            label = i18n.translate_field_label(field_def.key, self._qr_type_value)
            hint = i18n.translate_field_hint(field_def.key, self._qr_type_value)

            if field_def.kind == FieldKind.SELECT:
                labeled = [
                    (opt, i18n.translate_wifi_security(opt))
                    for opt in field_def.options
                ]
                control = self._comp.dropdown(
                    labeled_options=labeled,
                    value=value or (field_def.options[0] if field_def.options else ""),
                    on_change=lambda e, key=field_def.key: self._on_field_change(
                        key, e.control.value
                    ),
                )
                controls.append(self._comp.label(label))
                controls.append(control)
                continue

            if field_def.kind == FieldKind.PASSWORD:
                control = ft.TextField(
                    label=label,
                    hint_text=hint,
                    value=value,
                    password=True,
                    can_reveal_password=True,
                    border_color=t_theme.c("border"),
                    focused_border_color=t_theme.c("primary"),
                    label_style=ft.TextStyle(
                        color=t_theme.c("text2"), size=FONT_SCALE["sm"]
                    ),
                    text_style=ft.TextStyle(
                        color=t_theme.c("text"), size=FONT_SCALE["base"]
                    ),
                    hint_style=ft.TextStyle(
                        color=t_theme.c("text3"), size=FONT_SCALE["sm"]
                    ),
                    bgcolor=t_theme.c("input_bg"),
                    border_radius=RADIUS["md"],
                    cursor_color=t_theme.c("primary"),
                    on_change=lambda e, key=field_def.key: self._on_field_change(
                        key, e.control.value
                    ),
                )
                controls.append(control)
                continue

            multiline = field_def.kind == FieldKind.MULTILINE
            control = self._comp.text_field(
                label=label,
                hint=hint,
                multiline=multiline,
                value=value,
                on_change=lambda e, key=field_def.key: self._on_field_change(
                    key, e.control.value
                ),
            )
            controls.append(control)

        return controls

    def _truncate_payload(self, payload: str, max_len: int = 120) -> str:
        if not payload:
            return ""
        one_line = payload.replace("\n", " ↵ ")
        if len(one_line) <= max_len:
            return tr("payload_preview", content=one_line)
        return tr("payload_preview", content=f"{one_line[: max_len - 1]}…")

    def _sync_content_from_fields(self) -> None:
        """Build encoded QR payload from current field values."""
        result = self._content_svc.build(self._qr_type_value, self._field_values)
        if result.ok:
            self._content_value = result.content
            self._build_error = None
        else:
            self._content_value = ""
            self._build_error = result.error

    def _update_validation_ui(self) -> None:
        if hasattr(self, "_error_text") and self._error_text:
            self._error_text.value = (
                get_i18n().translate_validation(self._build_error)
                if self._build_error
                else ""
            )
            self._error_text.visible = bool(self._build_error)
        if hasattr(self, "_payload_text") and self._payload_text:
            preview = self._truncate_payload(self._content_value)
            self._payload_text.value = preview
            self._payload_text.visible = bool(preview)

    def _build_preview(self) -> ft.Control:
        t = self._theme
        if self._preview_bytes:
            # Scale preview proportionally but cap at 300 pixels for UI
            preview_scale = min(300, max(180, self._qr_size_value / 8))
            return ft.Container(
                content=ft.Image(
                    src=self._preview_bytes,
                    width=preview_scale,
                    height=preview_scale,
                    fit=ft.BoxFit.CONTAIN,
                ),
                alignment=ft.Alignment.CENTER,
                padding=SPACE["sm"],
            )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.QR_CODE_2_OUTLINED,
                        color=t.c("text3"),
                        size=124,
                    ),
                    ft.Text(
                        tr("preview_empty"),
                        size=FONT_SCALE["sm"],
                        color=t.c("text3"),
                        font_family=FONT_PRIMARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=SPACE["md"],
            ),
            width=240,
            height=240,
            bgcolor=t.c("surface3"),
            border_radius=RADIUS["md"],
            alignment=ft.Alignment.CENTER,
        )

    def _build_logo_card(self) -> ft.Control:
        """Build logo configuration card."""
        t = self._theme

        return self._comp.card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                tr("section_logo"),
                                size=FONT_SCALE["lg"],
                                weight=ft.FontWeight.W_700,
                                color=t.c("text"),
                                font_family=FONT_PRIMARY,
                            ),
                            ft.Container(expand=True),
                            self._comp.badge(
                                tr("badge_size_percent", value=self._logo_size_percent),
                                "secondary",
                                text_token="label",
                            ),
                            self._comp.badge(
                                tr(
                                    "badge_opacity", value=int(self._logo_opacity * 100)
                                ),
                                "secondary",
                                text_token="label",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=SPACE["sm"]),
                    # Logo preview
                    ft.Container(
                        content=self._build_logo_preview(),
                        height=80,
                        bgcolor=t.c("surface3"),
                        border_radius=RADIUS["md"],
                        border=ft.border.Border.all(1, t.c("border")),
                    ),
                    ft.Container(height=SPACE["sm"]),
                    # Upload section
                    ft.Row(
                        [
                            self._comp.ghost_button(
                                tr("from_file"),
                                icon=ft.Icons.UPLOAD_FILE_OUTLINED,
                                on_click=self._on_logo_file_pick,
                            ),
                            self._comp.ghost_button(
                                tr("from_url"),
                                icon=ft.Icons.LINK_OUTLINED,
                                on_click=self._on_logo_url_pick,
                            ),
                            self._comp.ghost_button(
                                tr("remove"),
                                icon=ft.Icons.CLOSE_OUTLINED,
                                on_click=self._on_logo_remove,
                            ),
                        ],
                        spacing=SPACE["sm"],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    # Size control
                    ft.Column(
                        [
                            self._comp.label(tr("logo_size_label")),
                            ft.Row(
                                [
                                    self._comp.dropdown(
                                        options=[f"{s}%" for s in LOGO_SIZE_OPTIONS],
                                        value=f"{self._logo_size_percent}%",
                                        on_change=self._on_logo_size_change,
                                    ),
                                    ft.Text(
                                        tr("logo_size_hint"),
                                        size=FONT_SCALE["xs"],
                                        color=t.c("text3"),
                                        font_family=FONT_PRIMARY,
                                    ),
                                ],
                                spacing=SPACE["sm"],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=SPACE["sm"],
                    ),
                    ft.Container(height=SPACE["sm"]),
                    # Opacity control
                    ft.Column(
                        [
                            self._comp.label(
                                tr("opacity_label", value=int(self._logo_opacity * 100))
                            ),
                            ft.Slider(
                                min=0,
                                max=100,
                                value=int(self._logo_opacity * 100),
                                on_change=self._on_logo_opacity_change,
                                active_color=t.c("primary"),
                                inactive_color=t.c("border"),
                            ),
                        ],
                        spacing=SPACE["sm"],
                    ),
                ],
                spacing=SPACE["lg"],
            ),
            padding=SPACE["lg"],
        )

    def _build_logo_preview(self) -> ft.Control:
        """Build logo preview display."""
        t = self._theme
        if self._logo_preview_bytes:
            return ft.Image(
                src=self._logo_preview_bytes,
                width=80,
                height=80,
                fit=ft.BoxFit.CONTAIN,
            )
        return ft.Column(
            [
                ft.Icon(
                    ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                    color=t.c("text3"),
                    size=32,
                ),
                ft.Text(
                    tr("no_logo"),
                    size=FONT_SCALE["xs"],
                    color=t.c("text3"),
                    font_family=FONT_PRIMARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=SPACE["xs"],
        )

    def _build_color_control(
        self,
        label: str,
        value: str,
        on_text_change,
        on_palette_select,
    ) -> ft.Column:
        t = self._theme
        return ft.Column(
            [
                self._comp.label(label),
                ft.Row(
                    [
                        ft.Container(
                            width=36,
                            height=36,
                            bgcolor=value,
                            border=ft.border.Border.all(1, t.c("border")),
                            border_radius=RADIUS["md"],
                        ),
                        ft.TextField(
                            value=value,
                            on_change=on_text_change,
                            border_color=t.c("border"),
                            focused_border_color=t.c("primary"),
                            text_style=ft.TextStyle(
                                color=t.c("text"), size=FONT_SCALE["sm"]
                            ),
                            label_style=ft.TextStyle(
                                color=t.c("text2"), size=FONT_SCALE["sm"]
                            ),
                            bgcolor=self._theme.c("input_bg"),
                            border_radius=RADIUS["md"],
                            cursor_color=t.c("primary"),
                        ),
                    ],
                    spacing=SPACE["sm"],
                ),
                ft.Row(
                    [
                        ft.Container(
                            width=24,
                            height=24,
                            bgcolor=color,
                            border=ft.border.Border.all(1, t.c("border")),
                            border_radius=RADIUS["full"],
                            on_click=lambda e, c=color: on_palette_select(c),
                            tooltip=color,
                        )
                        for color in COLOR_SWATCHES
                    ],
                    spacing=SPACE["xs"],
                ),
            ],
            spacing=SPACE["sm"],
            expand=True,
        )

    # ── Event Handlers ────────────────────────────────────────

    def _on_type_change(self, e) -> None:
        self._qr_type_value = e.control.value
        self._field_values = self._content_svc.default_fields(self._qr_type_value)
        self._settings.set_last_qr_type(self._qr_type_value)
        self._sync_content_from_fields()
        self._refresh_preview()
        self._rebuild_controls()
        self.update()

    def _on_field_change(self, key: str, value: str) -> None:
        field_defs = {
            f.key: f for f in self._content_svc.field_definitions(self._qr_type_value)
        }
        field_def = field_defs.get(key)
        if field_def and field_def.max_length and len(value) > field_def.max_length:
            value = value[: field_def.max_length]
            self._comp.snack(
                self._page,
                tr(
                    "msg_field_max_chars",
                    field=get_i18n().translate_field_label(key, self._qr_type_value),
                    max=field_def.max_length,
                ),
                success=False,
            )
        self._field_values[key] = value
        self._sync_content_from_fields()
        self._refresh_preview()
        self._update_validation_ui()
        self.update()

    def _on_foreground_text_change(self, e) -> None:
        self._update_color("foreground", e.control.value)

    def _on_background_text_change(self, e) -> None:
        self._update_color("background", e.control.value)

    def _on_foreground_palette(self, color: str) -> None:
        self._update_color("foreground", color)

    def _on_background_palette(self, color: str) -> None:
        self._update_color("background", color)

    def _on_size_change(self, e) -> None:
        new_size = int(e.control.value)
        self._qr_size_value = new_size
        self._settings.set_qr_size(new_size)
        self._svc.set_size(new_size)
        self._refresh_preview()
        self._rebuild_controls()
        self.update()

    def _on_margin_change(self, e) -> None:
        new_margin = int(e.control.value)
        self._qr_margin_value = new_margin
        self._settings.set_qr_margin(new_margin)
        self._svc.set_margin(new_margin)
        self._refresh_preview()
        self._rebuild_controls()
        self.update()

    def _update_color(self, kind: str, color_value: str) -> None:
        candidate = color_value.strip().upper()
        if not candidate.startswith("#"):
            candidate = f"#{candidate}"
        if len(candidate) == 7 and all(c in "0123456789ABCDEF" for c in candidate[1:]):
            if kind == "foreground":
                self._foreground_color = candidate
                self._settings.set_qr_colors(
                    self._foreground_color, self._background_color
                )
            else:
                self._background_color = candidate
                self._settings.set_qr_colors(
                    self._foreground_color, self._background_color
                )
            self._svc.set_colors(self._foreground_color, self._background_color)
            self._refresh_preview()
            self._rebuild_controls()
            self.update()

    def _on_logo_file_pick(self, _) -> None:
        """Handle local file logo upload."""
        self._file_picker.pick_files(
            allowed_extensions=["png", "jpg", "jpeg", "webp"],
        )

    async def _on_logo_file_pick(self, _) -> None:
        """Handle local file logo upload."""
        files = await ft.FilePicker().pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png", "jpg", "jpeg", "webp"],
        )
        if files:
            try:
                filepath = files[0].path
                logo_img = self._logo_svc.load_from_file(filepath)
                if not logo_img:
                    self._comp.snack(
                        self._page, tr("msg_logo_invalid_format"), success=False
                    )
                    return
                if not self._logo_svc.validate_image(logo_img):
                    self._comp.snack(
                        self._page, tr("msg_logo_invalid_dimensions"), success=False
                    )
                    return
                self._logo_image = logo_img
                self._update_logo_preview()
                self._refresh_preview()
                self._rebuild_controls()
                self.update()
                self._comp.snack(self._page, tr("msg_logo_loaded"), success=True)
            except Exception as exc:
                self._comp.snack(
                    self._page, tr("msg_logo_load_error", error=exc), success=False
                )

    def _on_logo_url_pick(self, _) -> None:
        dlg = ft.AlertDialog(
            title=ft.Text(tr("dialog_load_logo_url")),
            content=ft.Column(
                [
                    ft.TextField(
                        label=tr("field_image_url"),
                        hint_text=tr("hint_image_url"),
                        min_lines=2,
                        bgcolor=self._theme.c("input_bg"),
                        border_color=self._theme.c("border"),
                        focused_border_color=self._theme.c("primary"),
                        text_style=ft.TextStyle(
                            color=self._theme.c("text"),
                            size=FONT_SCALE["sm"],
                        ),
                    ),
                ],
                width=300,
            ),
            actions=[
                ft.TextButton(
                    tr("cancel"), on_click=lambda e: self._on_url_dialog_cancel(dlg)
                ),
                ft.TextButton(
                    tr("load"),
                    on_click=lambda e: self._on_url_dialog_confirm(
                        dlg,
                        dlg.content.controls[0].value if dlg.content.controls else "",
                    ),
                ),
            ],
            open=True,
        )
        self._page.overlay.append(dlg)
        self._page.update()

    def _on_url_dialog_cancel(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        self._page.update()

    def _on_url_dialog_confirm(self, dlg: ft.AlertDialog, url: str) -> None:
        dlg.open = False
        try:
            if not url.strip():
                self._comp.snack(self._page, tr("msg_logo_url_invalid"), success=False)
                return

            logo_img = self._logo_svc.load_from_url(url)
            if not logo_img:
                self._comp.snack(self._page, tr("msg_logo_url_failed"), success=False)
                return

            if not self._logo_svc.validate_image(logo_img):
                self._comp.snack(
                    self._page, tr("msg_logo_invalid_dimensions"), success=False
                )
                return

            self._logo_image = logo_img
            self._update_logo_preview()
            self._refresh_preview()
            self._rebuild_controls()
            self.update()
            self._comp.snack(self._page, tr("msg_logo_url_loaded"), success=True)
        except Exception as exc:
            self._comp.snack(
                self._page, tr("msg_error_generic", error=exc), success=False
            )
        finally:
            self._page.update()

    def _on_logo_remove(self, _) -> None:
        """Remove current logo."""
        self._logo_image = None
        self._logo_preview_bytes = None
        self._refresh_preview()
        self._rebuild_controls()
        self.update()
        self._comp.snack(self._page, tr("msg_logo_removed"), success=True)

    def _on_logo_size_change(self, e) -> None:
        """Handle logo size change."""
        try:
            size_percent = int(e.control.value.replace("%", ""))
            if size_percent in LOGO_SIZE_OPTIONS:
                self._logo_size_percent = size_percent
                self._settings.set_logo_size_percent(size_percent)
                self._refresh_preview()
                self._rebuild_controls()
                self.update()
        except Exception:
            pass

    def _on_logo_opacity_change(self, e) -> None:
        """Handle logo opacity slider change."""
        try:
            opacity_int = int(e.control.value)
            self._logo_opacity = opacity_int / 100.0
            self._settings.set_logo_opacity(opacity_int)
            self._refresh_preview()
            self._rebuild_controls()
            self.update()
        except Exception:
            pass

    def _update_logo_preview(self) -> None:
        """Generate preview bytes for logo thumbnail."""
        try:
            if not self._logo_image:
                self._logo_preview_bytes = None
                return

            # Create a small preview
            preview_img = self._logo_image.copy()
            preview_img.thumbnail((80, 80), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            preview_img.save(buf, format="PNG")
            self._logo_preview_bytes = buf.getvalue()
        except Exception:
            self._logo_preview_bytes = None

    def _refresh_preview(self) -> None:
        if not self._content_value.strip():
            self._preview_bytes = None
            return

        # Scale preview size proportionally to QR size but cap at reasonable UI bounds
        preview_scale = min(300, max(180, self._qr_size_value / 8))

        # Prepare logo for preview if available
        logo_for_preview = None
        if self._logo_image:
            try:
                logo_for_preview = self._logo_svc.resize_logo(
                    self._logo_image.copy(),
                    int(preview_scale),  # Use scaled preview size
                    self._logo_size_percent,
                )
                logo_for_preview = self._logo_svc.apply_opacity(
                    logo_for_preview, self._logo_opacity
                )
            except Exception:
                logo_for_preview = None

        raw = self._svc.generate_preview_bytes(
            self._content_value,
            logo=logo_for_preview,
            logo_opacity=1.0,  # Already applied in resize_logo
        )
        self._preview_bytes = raw if raw else None

    def _on_generate(self, _) -> None:
        self._sync_content_from_fields()
        if self._build_error:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(self._build_error),
                success=False,
            )
            self._update_validation_ui()
            self.update()
            return
        if not self._content_value.strip():
            self._comp.snack(self._page, tr("msg_fill_required_fields"), success=False)
            return
        self._refresh_preview()
        self._rebuild_controls()
        self.update()
        self._comp.snack(self._page, tr("msg_qr_generated"), success=True)

    def _on_download(self, _) -> None:
        self._sync_content_from_fields()
        if self._build_error:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(self._build_error),
                success=False,
            )
            self._update_validation_ui()
            self.update()
            return
        if not self._content_value.strip():
            self._comp.snack(self._page, tr("msg_generate_valid_first"), success=False)
            return
        try:
            logo_for_export = self._prepare_logo_for_export()

            entry = self._svc.export_png(
                self._content_value,
                self._content_svc.type_id_for(self._qr_type_value),
                logo=logo_for_export,
                logo_opacity=1.0,
                project_id=self._project.id if self._project else "",
                project_name=self._project.name if self._project else "General",
                project_folder_name=self._project.folder_name if self._project else "",
            )
            self._settings.set_last_export_format("png")
            self._comp.snack(
                self._page,
                tr("msg_saved_to", path=entry.filepath),
            )
            self._on_exported()
        except Exception as exc:
            self._comp.snack(
                self._page, tr("msg_export_failed", error=exc), success=False
            )

    def _on_export_svg(self, _) -> None:
        self._sync_content_from_fields()
        if self._build_error:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(self._build_error),
                success=False,
            )
            self._update_validation_ui()
            self.update()
            return
        if not self._content_value.strip():
            self._comp.snack(self._page, tr("msg_generate_valid_first"), success=False)
            return
        try:
            logo_for_export = self._prepare_logo_for_export()
            entry = self._svg_svc.export_svg(
                content=self._content_value,
                qr_type=self._content_svc.type_id_for(self._qr_type_value),
                foreground_color=self._foreground_color,
                background_color=self._background_color,
                size=self._qr_size_value,
                margin=self._qr_margin_value,
                logo=logo_for_export,
                logo_opacity=1.0,
                logo_size_percent=self._logo_size_percent,
                project_id=self._project.id if self._project else "",
                project_name=self._project.name if self._project else "General",
                project_folder_name=self._project.folder_name if self._project else "",
            )
            self._settings.set_last_export_format("svg")
            self._comp.snack(
                self._page,
                tr("msg_svg_saved", path=entry.filepath),
            )
            self._on_exported()
        except SvgExportError as exc:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(str(exc)),
                success=False,
            )
        except Exception as exc:
            self._comp.snack(
                self._page, tr("msg_export_failed", error=exc), success=False
            )

    def _on_export_pdf(self, _) -> None:
        self._sync_content_from_fields()
        if self._build_error:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(self._build_error),
                success=False,
            )
            self._update_validation_ui()
            self.update()
            return
        if not self._content_value.strip():
            self._comp.snack(self._page, tr("msg_generate_valid_first"), success=False)
            return
        try:
            logo_for_export = self._prepare_logo_for_export()
            entry = self._pdf_svc.export_pdf(
                content=self._content_value,
                qr_type=self._content_svc.type_id_for(self._qr_type_value),
                foreground_color=self._foreground_color,
                background_color=self._background_color,
                size=self._qr_size_value,
                margin=self._qr_margin_value,
                logo=logo_for_export,
                logo_opacity=1.0,
                logo_size_percent=self._logo_size_percent,
                project_id=self._project.id if self._project else "",
                project_name=self._project.name if self._project else "General",
                project_folder_name=self._project.folder_name if self._project else "",
            )
            self._settings.set_last_export_format("pdf")
            self._comp.snack(
                self._page,
                tr("msg_pdf_saved", path=entry.filepath),
            )
            self._on_exported()
        except PdfExportError as exc:
            self._comp.snack(
                self._page,
                get_i18n().translate_validation(str(exc)),
                success=False,
            )
        except Exception as exc:
            self._comp.snack(
                self._page, tr("msg_export_failed", error=exc), success=False
            )
