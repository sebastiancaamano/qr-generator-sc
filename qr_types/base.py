"""
Base types for QR content builders.

Each QR type implements QRBuilder to transform form fields into the
encoded payload string consumed by qrcode.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class FieldKind(str, Enum):
    TEXT = "text"
    PASSWORD = "password"
    MULTILINE = "multiline"
    SELECT = "select"


@dataclass(frozen=True)
class FieldDef:
    """Describes one dynamic form field for a QR type."""

    key: str
    label: str
    hint: str = ""
    kind: FieldKind = FieldKind.TEXT
    required: bool = True
    options: tuple[str, ...] = ()
    max_length: Optional[int] = None


@dataclass
class BuildResult:
    """Outcome of building QR payload from form fields."""

    content: str = ""
    error: Optional[str] = None
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.content.strip())


class QRBuilder(ABC):
    """Abstract builder: form fields → QR payload string."""

    type_id: str
    display_name: str

    @abstractmethod
    def field_definitions(self) -> list[FieldDef]:
        """Return ordered field definitions for the UI."""

    @abstractmethod
    def build(self, fields: dict[str, str]) -> BuildResult:
        """Validate fields and produce the QR payload."""

    def parse_from_content(self, content: str) -> dict[str, str]:
        """Restore form fields from a stored payload (history reload)."""
        return {}

    def _escape_wifi_value(self, value: str) -> str:
        """Escape special chars per WiFi QR spec (backslash, semicolon, comma, colon)."""
        return (
            value.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace(":", "\\:")
        )
