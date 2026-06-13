"""
Storage Service — Project persistence for QR Generator SC.
"""

import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.project import Project

PROJECTS_FILE = Path.home() / ".qr_generator_sc" / "projects.json"
PROJECTS_ROOT = Path.home() / "Downloads" / "QR Generator SC"
PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)


class ProjectStorage:
    """JSON-backed persistence for projects and the currently selected project."""

    def __init__(self, path: Path = PROJECTS_FILE):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._projects: List[Project] = []
        self._selected_project_id: Optional[str] = None
        self._load()
        self._ensure_default_project()

    def all(self) -> List[Project]:
        return sorted(self._projects, key=lambda p: p.created_at)

    def add(self, name: str, description: str = "") -> Project:
        cleaned_name = name.strip() or "Untitled Project"
        if self._name_exists(cleaned_name):
            raise ValueError("Project name already exists.")

        folder_name = self._safe_folder_name(cleaned_name)
        project = Project(
            id=str(uuid.uuid4()),
            name=cleaned_name,
            description=description.strip(),
            folder_name=folder_name,
        )
        self._projects.append(project)
        self._selected_project_id = project.id
        self._ensure_project_directory(project)
        self._save()
        return project

    def update(
        self, project_id: str, name: str = None, description: str = None
    ) -> Optional[Project]:
        project = self.get(project_id)
        if not project:
            return None
        updated = False
        if name is not None and name.strip() and name.strip() != project.name:
            new_name = name.strip()
            if self._name_exists(new_name, exclude_id=project_id):
                raise ValueError("Project name already exists.")
            new_folder_name = self._safe_folder_name(new_name)
            self._rename_project_directory(project, new_folder_name)
            project.name = new_name
            project.folder_name = new_folder_name
            updated = True
        if description is not None and description.strip() != project.description:
            project.description = description.strip()
            updated = True
        if updated:
            project.modified_at = datetime.now()
            self._ensure_project_directory(project)
            self._save()
        return project

    def delete(self, project_id: str) -> bool:
        project = self.get(project_id)
        if not project:
            return False

        project_path = self._project_path(project)
        if project_path.exists() and project_path.is_dir():
            shutil.rmtree(project_path)

        self._projects = [p for p in self._projects if p.id != project_id]
        if self._selected_project_id == project_id:
            self._selected_project_id = self._projects[0].id if self._projects else None
        self._ensure_default_project()
        self._save()
        return True

    def get(self, project_id: str) -> Optional[Project]:
        return next((p for p in self._projects if p.id == project_id), None)

    def select(self, project_id: str) -> Optional[Project]:
        project = self.get(project_id)
        if project:
            self._selected_project_id = project_id
            self._save()
        return project

    def selected(self) -> Project:
        project = (
            self.get(self._selected_project_id) if self._selected_project_id else None
        )
        if project:
            return project
        return self._ensure_default_project()

    def increment_qr_count(self, project_id: str) -> None:
        project = self.get(project_id)
        if project:
            project.qr_count += 1
            project.modified_at = datetime.now()
            self._save()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._selected_project_id = raw.get("selected_project_id")
                self._projects = [
                    Project.from_dict(data)
                    for data in raw.get("projects", [])
                    if isinstance(data, dict)
                ]
                updated = False
                for project in self._projects:
                    if not project.folder_name:
                        project.folder_name = self._safe_folder_name(project.name)
                        updated = True
                if updated:
                    self._save()
        except (json.JSONDecodeError, FileNotFoundError, AttributeError):
            self._projects = []
            self._selected_project_id = None

    def _save(self) -> None:
        data: Dict[str, object] = {
            "selected_project_id": self._selected_project_id,
            "projects": [project.to_dict() for project in self._projects],
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _ensure_default_project(self) -> Project:
        if not self._projects:
            default = Project(
                id=str(uuid.uuid4()),
                name="General",
                description="Default project for your QR codes.",
                folder_name=self._safe_folder_name("General"),
            )
            self._projects.append(default)
            self._selected_project_id = default.id
            self._save()
            self._ensure_project_directory(default)
            return default
        if not self._selected_project_id or not self.get(self._selected_project_id):
            self._selected_project_id = self._projects[0].id
            self._save()
        return self.get(self._selected_project_id)

    def _ensure_all_project_directories(self) -> None:
        for project in self._projects:
            self._ensure_project_directory(project)

    def _project_path(self, project: Project) -> Path:
        folder_name = project.folder_name or self._safe_folder_name(project.name)
        return PROJECTS_ROOT / folder_name

    def _ensure_project_directory(self, project: Project) -> Path:
        path = self._project_path(project)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _rename_project_directory(self, project: Project, new_folder_name: str) -> None:
        old_dir = self._project_path(project)
        new_dir = PROJECTS_ROOT / new_folder_name
        if old_dir == new_dir:
            return
        if old_dir.exists() and old_dir.is_dir():
            old_dir.rename(new_dir)
        else:
            new_dir.mkdir(parents=True, exist_ok=True)

    def _safe_folder_name(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9 _-]", "", value).strip() or "General"

    def _name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        normalized = name.strip().lower()
        return any(
            p.name.strip().lower() == normalized and p.id != exclude_id
            for p in self._projects
        )
