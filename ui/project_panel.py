"""
Project Panel — QR Generator SC
Sidebar access for project selection and management.
"""

import flet as ft

from i18n.translation_manager import t
from models.project import Project
from storage.project_storage import ProjectStorage
from themes.theme_manager import ThemeManager
from themes.tokens import FONT_PRIMARY, FONT_SCALE, RADIUS, SPACE
from ui.components import FlatComponents


class ProjectPanel(ft.Column):
    def __init__(
        self, theme: ThemeManager, storage: ProjectStorage, page: ft.Page, on_select
    ):
        super().__init__()
        self._theme = theme
        self._storage = storage
        self._page = page
        self._on_select = on_select
        self._comp = FlatComponents(theme)
        self._selected_project_id = self._storage.selected().id

        self.spacing = 0
        self.expand = False
        self._build()

    def refresh(self) -> None:
        self._selected_project_id = self._storage.selected().id
        self._build()
        self.update()
        current_project = self._storage.get(self._selected_project_id)
        if current_project:
            self._on_select(current_project)

    def _build(self) -> None:
        t_theme = self._theme
        projects = self._storage.all()

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        t("section_projects"),
                        size=FONT_SCALE["sm"],
                        weight=ft.FontWeight.W_700,
                        color=t_theme.c("text2"),
                        font_family=FONT_PRIMARY,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        icon_color=t_theme.c("primary"),
                        tooltip=t("tooltip_new_project"),
                        on_click=self._open_create_project,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"]),
                        ),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACE["sm"],
            ),
            padding=ft.Padding.symmetric(horizontal=SPACE["lg"], vertical=SPACE["md"]),
        )

        if not projects:
            empty = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.FOLDER_OPEN, color=t_theme.c("text3"), size=28
                        ),
                        ft.Text(
                            t("no_projects"),
                            size=FONT_SCALE["sm"],
                            color=t_theme.c("text3"),
                            font_family=FONT_PRIMARY,
                        ),
                    ],
                    spacing=SPACE["sm"],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["lg"], vertical=SPACE["xl"]
                ),
            )
            self.controls = [header, empty]
            return

        rows = [self._project_row(project) for project in projects]
        self.controls = [header, self._comp.divider(), ft.Column(rows, spacing=0)]

    def _project_row(self, project: Project) -> ft.Container:
        t_theme = self._theme
        is_active = project.id == self._selected_project_id
        select_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        project.name,
                        size=FONT_SCALE["sm"],
                        weight=ft.FontWeight.W_600,
                        color=t_theme.c("text"),
                        font_family=FONT_PRIMARY,
                    ),
                    ft.Text(
                        project.description or t("no_description"),
                        size=FONT_SCALE["xs"],
                        color=t_theme.c("text2"),
                        font_family=FONT_PRIMARY,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        max_lines=1,
                    ),
                ],
                spacing=2,
                expand=True,
            ),
            expand=True,
            on_click=lambda e, p_id=project.id: self._select_project(p_id),
        )

        row = ft.Container(
            content=ft.Row(
                [
                    select_block,
                    self._comp.badge(
                        t("badge_qr_count", count=project.qr_count),
                        "secondary",
                        text_token="label",
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        tooltip=t("tooltip_edit_project"),
                        icon_color=t_theme.c("text2"),
                        on_click=lambda e, p=project: self._open_edit_project(p),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"])
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip=t("tooltip_delete_project"),
                        icon_color=t_theme.c("danger"),
                        on_click=lambda e, p=project: self._confirm_delete_project(p),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"])
                        ),
                    ),
                ],
                spacing=SPACE["sm"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=SPACE["lg"], vertical=SPACE["md"]),
            bgcolor=t_theme.c("hover") if is_active else None,
            border=ft.border.Border.all(1, t_theme.c("border")),
            border_radius=RADIUS["md"],
        )
        return row

    def _select_project(self, project_id: str) -> None:
        project = self._storage.select(project_id)
        if project:
            self._selected_project_id = project.id
            self._build()
            self.update()
            self._on_select(project)

    def _open_create_project(self, _) -> None:
        self._show_project_dialog(t("new_project"), t("create"), self._create_project)

    def _open_edit_project(self, project: Project) -> None:
        self._show_project_dialog(
            t("edit_project_title", name=project.name),
            t("save"),
            lambda name, description: self._edit_project(project.id, name, description),
            project,
        )

    def _show_project_dialog(
        self, title: str, action_label: str, action_callback, project: Project = None
    ) -> None:
        name_field = ft.TextField(
            label=t("field_project_name"),
            value=project.name if project else "",
            autofocus=True,
            border_color=self._theme.c("border"),
            focused_border_color=self._theme.c("primary"),
            bgcolor=self._theme.c("input_bg"),
            text_style=ft.TextStyle(color=self._theme.c("text"), size=FONT_SCALE["sm"]),
        )
        desc_field = ft.TextField(
            label=t("field_description"),
            value=project.description if project else "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=self._theme.c("border"),
            focused_border_color=self._theme.c("primary"),
            bgcolor=self._theme.c("input_bg"),
            text_style=ft.TextStyle(color=self._theme.c("text"), size=FONT_SCALE["sm"]),
        )

        def on_action_click(e) -> None:
            result = action_callback(name_field.value, desc_field.value)
            if result is not False:
                self._close_dialog(dlg, refresh=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                title,
                size=FONT_SCALE["lg"],
                weight=ft.FontWeight.W_700,
                color=self._theme.c("text"),
            ),
            content=ft.Column(
                [name_field, desc_field],
                spacing=SPACE["sm"],
            ),
            actions=[
                ft.TextButton(
                    t("cancel"),
                    on_click=lambda e: self._close_dialog(dlg, refresh=False),
                ),
                ft.TextButton(
                    action_label,
                    on_click=on_action_click,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    def _create_project(self, name: str, description: str) -> bool:
        if not name.strip():
            self._comp.snack(self._page, t("msg_project_name_empty"), success=False)
            return False
        try:
            project = self._storage.add(name, description)
            self._comp.snack(self._page, t("msg_project_created", name=project.name))
            return True
        except ValueError as exc:
            self._comp.snack(self._page, str(exc), success=False)
            return False

    def _edit_project(self, project_id: str, name: str, description: str) -> bool:
        if not name.strip():
            self._comp.snack(self._page, t("msg_project_name_empty"), success=False)
            return False
        try:
            project = self._storage.update(project_id, name, description)
            if project:
                self._comp.snack(
                    self._page, t("msg_project_updated", name=project.name)
                )
                return True
            return False
        except ValueError as exc:
            self._comp.snack(self._page, str(exc), success=False)
            return False

    def _confirm_delete_project(self, project: Project) -> None:
        dlg = ft.AlertDialog(
            title=ft.Text(
                t("delete_project"),
                size=FONT_SCALE["lg"],
                weight=ft.FontWeight.W_700,
                color=self._theme.c("text"),
            ),
            content=ft.Text(
                t("delete_project_confirm", name=project.name),
                size=FONT_SCALE["sm"],
                color=self._theme.c("text2"),
                font_family=FONT_PRIMARY,
            ),
            actions=[
                ft.TextButton(
                    t("cancel"),
                    on_click=lambda e: self._close_dialog(dlg, refresh=False),
                ),
                ft.TextButton(
                    t("delete"),
                    on_click=lambda e: self._delete_project(project.id, dlg),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dlg)

    def _delete_project(self, project_id: str, dlg: ft.AlertDialog) -> None:
        deleted = self._storage.delete(project_id)
        if deleted:
            self._selected_project_id = self._storage.selected().id
            self._comp.snack(self._page, t("msg_project_deleted"))
        self._close_dialog(dlg, refresh=True)

    def _close_dialog(self, dlg: ft.AlertDialog, refresh: bool = True) -> None:
        self._page.pop_dialog()
        if refresh:
            self.refresh()
