"""
Batch Export Dialog — QR Generator SC
Dialog for multi-page PDF export with batch support.
"""

import flet as ft

from i18n.translation_manager import t
from models.qr_entry import QREntry
from services.multipage_pdf_export_service import MultipagePdfExportService
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage
from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE
from ui.components import FlatComponents


class BatchExportDialog:
    """
    Dialog for configuring and executing multi-page PDF batch exports.
    Supports export by selection, project, or all history.
    """

    def __init__(
        self,
        page: ft.Page,
        theme: ThemeManager,
        storage: HistoryStorage,
        project_storage: ProjectStorage,
        on_complete: callable,
    ):
        self._page = page
        self._theme = theme
        self._storage = storage
        self._project_storage = project_storage
        self._on_complete = on_complete
        self._comp = FlatComponents(theme)
        
        self._dialog = None
        self._qr_per_page = ft.Dropdown()
        self._show_labels = ft.Switch()
        self._show_content = ft.Switch()
        self._show_type = ft.Switch()
        self._progress_bar = ft.ProgressBar(visible=False)
        self._progress_text = ft.Text(visible=False)
        self._export_button = None
        self._selected_entries = []
        self._export_mode = "all"  # all, project, selection
        self._project_id = ""
        self._project_name = ""

    def show(
        self,
        export_mode: str = "all",
        selected_entries: list = None,
        project_id: str = "",
        project_name: str = "",
    ) -> None:
        """
        Show the batch export dialog.
        
        Args:
            export_mode: Export mode - "all", "project", or "selection"
            selected_entries: List of selected QREntry objects (for selection mode)
            project_id: Project ID (for project mode)
            project_name: Project name (for project mode)
        """
        self._export_mode = export_mode
        self._selected_entries = selected_entries or []
        self._project_id = project_id
        self._project_name = project_name
        
        self._build_dialog()
        self._page.show_dialog(self._dialog)

    def _build_dialog(self) -> None:
        theme = self._theme
        
        # QR per page selector
        self._qr_per_page = self._comp.dropdown(
            labeled_options=[
                ("10", "10"),
                ("20", "20"),
                ("50", "50"),
            ],
            value="10",
        )
        
        # Label toggles
        self._show_labels = ft.Switch(
            value=True,
            label=t("batch_show_labels"),
            active_color=theme.c("primary"),
        )
        
        self._show_type = ft.Switch(
            value=True,
            label=t("batch_show_type"),
            active_color=theme.c("primary"),
        )
        
        self._show_content = ft.Switch(
            value=False,
            label=t("batch_show_content"),
            active_color=theme.c("primary"),
        )
        
        # Progress indicators
        self._progress_bar = ft.ProgressBar(visible=False, width=400)
        self._progress_text = ft.Text(
            visible=False,
            size=FONT_SCALE["sm"],
            color=theme.c("text2"),
            font_family=FONT_PRIMARY,
        )
        
        # Export button
        self._export_button = self._comp.primary_button(
            text=t("batch_export_button"),
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=self._on_export_click,
        )
        
        # Cancel button
        cancel_button = self._comp.ghost_button(
            text=t("cancel"),
            on_click=self._on_cancel_click,
        )
        
        # Build dialog content
        content = ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.PICTURE_AS_PDF,
                                color=theme.c("primary"),
                                size=24,
                            ),
                            ft.Text(
                                t("batch_export_title"),
                                size=FONT_SCALE["lg"],
                                weight=ft.FontWeight.W_700,
                                color=theme.c("text"),
                                font_family=FONT_PRIMARY,
                            ),
                        ],
                        spacing=SPACE["sm"],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._comp.divider(),
                    
                    # Export mode info
                    ft.Container(
                        content=ft.Text(
                            self._get_export_mode_description(),
                            size=FONT_SCALE["sm"],
                            color=theme.c("text2"),
                            font_family=FONT_PRIMARY,
                        ),
                        padding=ft.Padding(
                            left=SPACE["md"],
                            top=SPACE["sm"],
                            bottom=SPACE["sm"],
                            right=SPACE["md"],
                        ),
                        bgcolor=theme.c("surface2"),
                        border_radius=RADIUS["md"],
                    ),
                    
                    ft.Container(height=SPACE["md"]),
                    
                    # QR per page selector
                    ft.Column(
                        [
                            self._comp.label(t("batch_qr_per_page")),
                            self._qr_per_page,
                        ],
                        spacing=SPACE["xs"],
                    ),
                    
                    ft.Container(height=SPACE["md"]),
                    
                    # Label options
                    ft.Column(
                        [
                            self._comp.label(t("batch_label_options")),
                            ft.Column(
                                [
                                    self._show_labels,
                                    self._show_type,
                                    self._show_content,
                                ],
                                spacing=SPACE["sm"],
                            ),
                        ],
                        spacing=SPACE["xs"],
                    ),
                    
                    ft.Container(height=SPACE["lg"]),
                    
                    # Progress section
                    ft.Column(
                        [
                            self._progress_bar,
                            self._progress_text,
                        ],
                        spacing=SPACE["sm"],
                        visible=False,
                    ),
                    
                    ft.Container(height=SPACE["lg"]),
                    
                    # Action buttons
                    ft.Row(
                        [
                            cancel_button,
                            ft.Container(width=SPACE["md"]),
                            self._export_button,
                        ],
                        spacing=0,
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=500,
            padding=SPACE["xl"],
            bgcolor=theme.c("surface"),
        )
        
        self._dialog = ft.AlertDialog(
            modal=True,
            content=content,
            actions=[],
            actions_padding=0,
            shape=ft.RoundedRectangleBorder(radius=RADIUS["lg"]),
        )

    def _get_export_mode_description(self) -> str:
        """Get description text for current export mode."""
        if self._export_mode == "selection":
            count = len(self._selected_entries)
            return t("batch_mode_selection", count=count)
        elif self._export_mode == "project":
            return t("batch_mode_project", name=self._project_name)
        else:
            all_count = len(self._storage.all())
            return t("batch_mode_all", count=all_count)

    def _on_export_click(self, e) -> None:
        """Handle export button click."""
        # Validate
        qr_per_page = int(self._qr_per_page.value)
        
        if self._export_mode == "selection" and not self._selected_entries:
            self._comp.snack(self._page, t("validation.no_qr_selected"), success=False)
            return
        
        # Show progress
        self._progress_bar.visible = True
        self._progress_text.visible = True
        self._export_button.disabled = True
        self._dialog.update()
        
        # Create service and export
        service = MultipagePdfExportService(
            self._storage,
            project_storage=self._project_storage,
        )
        
        try:
            def progress_callback(current: int, total: int):
                self._progress_bar.value = current / total if total > 0 else 0
                self._progress_text.text = t("batch_progress", current=current, total=total)
                self._dialog.update()
            
            if self._export_mode == "selection":
                entry_ids = [e.id for e in self._selected_entries]
                filepath = service.export_batch_by_selection(
                    entry_ids=entry_ids,
                    qr_per_page=qr_per_page,
                    show_labels=self._show_labels.value,
                    show_content=self._show_content.value,
                    show_type=self._show_type.value,
                    project_name="SelectionExport",
                    progress_callback=progress_callback,
                )
            elif self._export_mode == "project":
                filepath = service.export_batch_by_project(
                    project_id=self._project_id,
                    project_name=self._project_name,
                    qr_per_page=qr_per_page,
                    show_labels=self._show_labels.value,
                    show_content=self._show_content.value,
                    show_type=self._show_type.value,
                    progress_callback=progress_callback,
                )
            else:  # all
                all_entries = self._storage.all()
                filepath = service.export_multipage_pdf(
                    entries=all_entries,
                    qr_per_page=qr_per_page,
                    show_labels=self._show_labels.value,
                    show_content=self._show_content.value,
                    show_type=self._show_type.value,
                    project_name="AllHistory",
                    progress_callback=progress_callback,
                )
            
            # Success
            self._page.pop_dialog()
            self._comp.snack(self._page, t("batch_export_success", path=filepath))
            if self._on_complete:
                self._on_complete()
                
        except Exception as ex:
            self._progress_bar.visible = False
            self._progress_text.visible = False
            self._export_button.disabled = False
            self._dialog.update()
            error_msg = str(ex)
            if error_msg.startswith("validation."):
                error_msg = t(error_msg)
            else:
                error_msg = t("msg_error_generic", error=error_msg)
            self._comp.snack(self._page, error_msg, success=False)

    def _on_cancel_click(self, e) -> None:
        """Handle cancel button click."""
        self._page.pop_dialog()
