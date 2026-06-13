"""
History Panel — QR Generator SC
Left sidebar showing local QR history entries.
"""

import flet as ft

from i18n.translation_manager import t
from models.qr_entry import QREntry
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage
from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE
from ui.batch_export_dialog import BatchExportDialog
from ui.components import FlatComponents


class HistoryPanel(ft.Column):
    """
    Scrollable list of past QR entries.
    Calls on_select(entry) when user clicks a row.
    """

    def __init__(
        self,
        theme: ThemeManager,
        storage: HistoryStorage,
        on_select,
        active_project_id: str = "",
        active_project_name: str = "All Projects",
        project_storage: ProjectStorage = None,
        page: ft.Page = None,
    ):
        super().__init__()
        self._theme = theme
        self._storage = storage
        self._on_select = on_select
        self._active_project_id = active_project_id
        self._active_project_name = active_project_name
        self._project_storage = project_storage
        self._page = page
        self._comp = FlatComponents(theme)

        # Initialize batch export dialog
        self._batch_dialog = None
        if self._page and self._project_storage:
            self._batch_dialog = BatchExportDialog(
                page=self._page,
                theme=theme,
                storage=storage,
                project_storage=project_storage,
                on_complete=self._on_batch_complete,
            )

        # Selection state
        self._selected_ids = set()
        self._selection_mode = False

        self.spacing = 0
        self.expand = True
        self._build()

    # ── Public ────────────────────────────────────────────────

    def refresh(
        self, active_project_id: str = "", active_project_name: str = "All Projects"
    ) -> None:
        self._active_project_id = active_project_id
        self._active_project_name = active_project_name
        self._selected_ids.clear()
        self._build()
        self.update()

    # ── Private ───────────────────────────────────────────────

    def _build(self) -> None:
        theme = self._theme
        entries = self._storage.all(self._active_project_id)

        # Selection mode toggle button
        selection_toggle_btn = self._comp.icon_button(
            icon=(
                ft.Icons.CHECKLIST
                if not self._selection_mode
                else ft.Icons.CHECK_CIRCLE
            ),
            tooltip=(
                t("tooltip_selection_mode")
                if not self._selection_mode
                else t("tooltip_exit_selection")
            ),
            on_click=self._on_selection_toggle,
        )

        # Select all / deselect all button (only visible in selection mode)
        select_all_btn = None
        if self._selection_mode and entries:
            all_selected = len(self._selected_ids) == len(entries)
            select_all_btn = self._comp.icon_button(
                icon=ft.Icons.SELECT_ALL if not all_selected else ft.Icons.CLEAR,
                tooltip=t("tooltip_select_all") if not all_selected else t("tooltip_deselect_all"),
                on_click=self._on_select_all_click,
            )

        # Batch export button
        batch_export_btn = self._comp.icon_button(
            icon=ft.Icons.PICTURE_AS_PDF,
            tooltip=t("tooltip_batch_export"),
            on_click=self._on_batch_export_click,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.HISTORY, color=theme.c("text2"), size=16),
                    ft.Text(
                        t("history_count", name=self._active_project_name),
                        size=FONT_SCALE["sm"],
                        weight=ft.FontWeight.W_600,
                        color=theme.c("text2"),
                        font_family=FONT_PRIMARY,
                        expand=True,
                    ),
                    selection_toggle_btn,
                    select_all_btn if select_all_btn else ft.Container(width=0),
                    batch_export_btn,
                    ft.Text(
                        str(len(entries)),
                        size=FONT_SCALE["xs"],
                        color=theme.c("text3"),
                        font_family=FONT_PRIMARY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=1,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=2, vertical=SPACE["md"]),
        )

        if not entries:
            empty = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.QR_CODE_2_OUTLINED, color=theme.c("text3"), size=32
                        ),
                        ft.Text(
                            t("no_history"),
                            size=FONT_SCALE["sm"],
                            color=theme.c("text3"),
                            font_family=FONT_PRIMARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
                padding=SPACE["xl"],
            )
            self.controls = [header, empty]
            return

        rows = [self._entry_row(e) for e in entries]

        list_col = ft.Column(
            rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.controls = [header, self._comp.divider(), list_col]

    def _entry_row(self, entry: QREntry) -> ft.Container:
        theme = self._theme
        icon_map = {
            "url": ft.Icons.LINK,
            "email": ft.Icons.EMAIL_OUTLINED,
            "text": ft.Icons.TEXT_FIELDS,
        }
        icon = icon_map.get(entry.qr_type.lower(), ft.Icons.QR_CODE)

        content_preview = (
            entry.content if len(entry.content) <= 28 else entry.content[:25] + "…"
        )

        # Checkbox for selection mode
        checkbox = None
        if self._selection_mode:
            is_selected = entry.id in self._selected_ids
            checkbox = ft.Checkbox(
                value=is_selected,
                on_change=lambda _, e=entry: self._on_checkbox_change(e),
            )

        row_content = []
        if checkbox:
            row_content.append(checkbox)
            row_content.append(ft.Container(width=SPACE["sm"]))

        row_content.extend([
            ft.Icon(icon, color=theme.c("primary"), size=14),
            ft.Column(
                [
                    ft.Text(
                        content_preview,
                        size=FONT_SCALE["xs"],
                        color=theme.c("text"),
                        weight=ft.FontWeight.W_500,
                        font_family=FONT_PRIMARY,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"{entry.date_str()} · {entry.time_str()} · {entry.export_format.upper()}",
                        size=10,
                        color=theme.c("text3"),
                        font_family=FONT_PRIMARY,
                    ),
                ],
                spacing=2,
                expand=True,
            ),
        ])

        return ft.Container(
            content=ft.Row(
                row_content,
                spacing=SPACE["sm"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=SPACE["lg"], vertical=SPACE["md"]),
            border_radius=RADIUS["sm"],
            on_click=lambda _, e=entry: self._on_row_click(e),
            on_hover=lambda ev, c=None: self._on_hover(ev),
            data=entry.id,
        )

    def _on_hover(self, event) -> None:
        event.control.bgcolor = self._theme.c("hover") if event.data == "true" else None
        event.control.update()

    def _on_selection_toggle(self, e) -> None:
        """Toggle selection mode."""
        self._selection_mode = not self._selection_mode
        if not self._selection_mode:
            self._selected_ids.clear()
        self._build()
        self.update()

    def _on_select_all_click(self, e) -> None:
        """Select or deselect all entries."""
        entries = self._storage.all(self._active_project_id)
        all_selected = len(self._selected_ids) == len(entries)
        
        if all_selected:
            self._selected_ids.clear()
        else:
            self._selected_ids = {e.id for e in entries}
        
        self._build()
        self.update()

    def _on_checkbox_change(self, entry: QREntry) -> None:
        """Handle checkbox change."""
        if entry.id in self._selected_ids:
            self._selected_ids.remove(entry.id)
        else:
            self._selected_ids.add(entry.id)
        self._build()
        self.update()

    def _on_row_click(self, entry: QREntry) -> None:
        """Handle row click - select entry if in selection mode, otherwise load it."""
        if self._selection_mode:
            self._on_checkbox_change(entry)
        else:
            self._on_select(entry)

    def _on_batch_export_click(self, e) -> None:
        """Handle batch export button click."""
        if not self._batch_dialog:
            return
        
        # If in selection mode and items are selected, use selection mode
        if self._selection_mode and self._selected_ids:
            selected_entries = [e for e in self._storage.all(self._active_project_id) if e.id in self._selected_ids]
            self._batch_dialog.show(
                export_mode="selection",
                selected_entries=selected_entries,
            )
        elif self._active_project_id:
            # Export current project
            self._batch_dialog.show(
                export_mode="project",
                project_id=self._active_project_id,
                project_name=self._active_project_name,
            )
        else:
            # Export all history
            self._batch_dialog.show(
                export_mode="all",
            )

    def _on_batch_complete(self) -> None:
        """Callback when batch export completes."""
        # Refresh the history panel to show any updates
        self.refresh(
            active_project_id=self._active_project_id,
            active_project_name=self._active_project_name,
        )
