"""
Domain Models — QR Generator SC
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QREntry:
    """Represents one generated QR code stored in history."""

    id: str
    content: str
    qr_type: str
    filename: str
    project_id: str = ""
    project_name: str = ""
    filepath: str = ""
    size: int = 0
    foreground_color: str = "#000000"
    background_color: str = "#FFFFFF"
    export_format: str = "png"
    created_at: datetime = field(default_factory=datetime.now)

    def date_str(self) -> str:
        return self.created_at.strftime("%d %b %Y")

    def time_str(self) -> str:
        return self.created_at.strftime("%H:%M")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "qr_type": self.qr_type,
            "filename": self.filename,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "filepath": self.filepath,
            "size": self.size,
            "foreground_color": self.foreground_color,
            "background_color": self.background_color,
            "export_format": self.export_format,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QREntry":
        data = dict(data)
        data["project_id"] = data.get("project_id", "")
        data["project_name"] = data.get("project_name", "")
        data["filepath"] = data.get("filepath", "")
        data["size"] = int(data.get("size", 0))
        data["foreground_color"] = data.get("foreground_color", "#000000")
        data["background_color"] = data.get("background_color", "#FFFFFF")
        data["export_format"] = data.get("export_format", "png")
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            data["created_at"] = datetime.fromisoformat(created_at)
        else:
            data["created_at"] = datetime.now()
        return cls(**data)
