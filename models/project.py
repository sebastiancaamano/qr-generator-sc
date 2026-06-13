"""
Domain Models — QR Generator SC
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Project:
    """Represents a project that groups generated QR entries."""

    id: str
    name: str
    description: str = ""
    folder_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    qr_count: int = 0

    def date_str(self) -> str:
        return self.created_at.strftime("%d %b %Y")

    def modified_str(self) -> str:
        return self.modified_at.strftime("%d %b %Y")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "folder_name": self.folder_name,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "qr_count": self.qr_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        data = dict(data)
        data["folder_name"] = data.get("folder_name", "")
        data["created_at"] = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        data["modified_at"] = datetime.fromisoformat(
            data.get("modified_at", data["created_at"].isoformat())
        )
        data["qr_count"] = int(data.get("qr_count", 0))
        return cls(**data)
