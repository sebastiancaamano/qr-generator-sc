"""Simple QR builders for legacy types (URL, Text, Email)."""

from qr_types.base import BuildResult, FieldDef, FieldKind, QRBuilder
from validators.common import validate_email, validate_text_length, validate_url


class URLBuilder(QRBuilder):
    type_id = "url"
    display_name = "URL"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="content",
                label="URL",
                hint="https://example.com",
                max_length=2953,
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, value, err = validate_url(fields.get("content", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)
        return BuildResult(content=value, fields={"content": value})

    def parse_from_content(self, content: str) -> dict[str, str]:
        return {"content": content}


class TextBuilder(QRBuilder):
    type_id = "text"
    display_name = "Text"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="content",
                label="Texto",
                hint="Escribe cualquier texto…",
                kind=FieldKind.MULTILINE,
                max_length=2953,
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, value, err = validate_text_length(
            fields.get("content", ""),
            max_length=2953,
            field_key="text",
        )
        if not ok:
            return BuildResult(error=err, fields=fields)
        return BuildResult(content=value, fields={"content": value})

    def parse_from_content(self, content: str) -> dict[str, str]:
        return {"content": content}


class EmailBuilder(QRBuilder):
    type_id = "email"
    display_name = "Email"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="content",
                label="Email",
                hint="hello@example.com",
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, value, err = validate_email(fields.get("content", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)
        # mailto: prefix improves scanner compatibility
        payload = value if value.startswith("mailto:") else f"mailto:{value}"
        return BuildResult(content=payload, fields={"content": value})

    def parse_from_content(self, content: str) -> dict[str, str]:
        return {"content": content.removeprefix("mailto:")}
