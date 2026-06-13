"""
QR Content Service — validates form fields and builds QR payloads.

Sits between the UI layer and QRService (image generation).
"""

from qr_types import QR_TYPES, get_builder, get_builder_by_id
from qr_types.base import BuildResult, FieldDef, QRBuilder


class QRContentService:
    """Orchestrates QR type builders and field validation."""

    @property
    def available_types(self) -> list[str]:
        return list(QR_TYPES)

    def get_builder(self, display_name: str) -> QRBuilder | None:
        return get_builder(display_name)

    def field_definitions(self, display_name: str) -> list[FieldDef]:
        builder = get_builder(display_name)
        if not builder:
            return []
        return builder.field_definitions()

    def build(self, display_name: str, fields: dict[str, str]) -> BuildResult:
        """Validate fields and return encoded QR payload."""
        builder = get_builder(display_name)
        if not builder:
            return BuildResult(error=f"validation.unknown_qr_type|{display_name}")
        return builder.build(fields)

    def parse_history_entry(
        self, qr_type: str, content: str
    ) -> tuple[str, dict[str, str]]:
        """
        Resolve display name and form fields from a stored history entry.
        Supports legacy lowercase type ids (url, text, email) and new ones.
        """
        type_map = {
            "url": "URL",
            "text": "Text",
            "email": "Email",
            "wifi": "WiFi",
            "whatsapp": "WhatsApp",
            "sms": "SMS",
            "phone": "Teléfono",
            "gps": "GPS",
            "vcard": "vCard",
        }
        display_name = type_map.get(qr_type.lower(), qr_type)
        builder = get_builder(display_name) or get_builder_by_id(qr_type)
        if not builder:
            display_name = "URL"
            builder = get_builder("URL")

        fields = builder.parse_from_content(content) if builder else {}
        if not fields:
            # Fallback for simple types: put raw content in first field
            defs = builder.field_definitions() if builder else []
            if defs:
                fields = {defs[0].key: content}
        return display_name, fields

    def default_fields(self, display_name: str) -> dict[str, str]:
        """Empty field values with sensible defaults for select fields."""
        builder = get_builder(display_name)
        if not builder:
            return {}
        values: dict[str, str] = {}
        for field_def in builder.field_definitions():
            if field_def.options:
                values[field_def.key] = field_def.options[0]
            else:
                values[field_def.key] = ""
        return values

    def type_id_for(self, display_name: str) -> str:
        """Return persisted type id (e.g. 'wifi') for a display name."""
        builder = get_builder(display_name)
        return builder.type_id if builder else display_name.lower()
