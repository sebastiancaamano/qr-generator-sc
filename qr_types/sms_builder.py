"""SMS QR builder — SMSTO:<phone>:<message>"""

import re

from qr_types.base import BuildResult, FieldDef, FieldKind, QRBuilder
from validators.common import normalize_phone, validate_phone, validate_text_length


class SMSBuilder(QRBuilder):
    type_id = "sms"
    display_name = "SMS"

    # Conservative limit for SMS QR payloads
    MAX_MESSAGE_LENGTH = 160

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="phone",
                label="Número telefónico",
                hint="+56912345678",
            ),
            FieldDef(
                key="message",
                label="Mensaje",
                hint="Hola, te escribo desde…",
                kind=FieldKind.MULTILINE,
                max_length=self.MAX_MESSAGE_LENGTH,
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, normalized, err = validate_phone(fields.get("phone", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)

        ok, message, err = validate_text_length(
            fields.get("message", ""),
            max_length=self.MAX_MESSAGE_LENGTH,
            field_key="message",
        )
        if not ok:
            return BuildResult(error=err, fields=fields)

        digits = normalize_phone(normalized, keep_plus=False)
        content = f"SMSTO:{digits}:{message}"
        return BuildResult(
            content=content,
            fields={"phone": normalized, "message": message},
        )

    def parse_from_content(self, content: str) -> dict[str, str]:
        match = re.match(r"SMSTO:([0-9+]+):(.+)", content, re.DOTALL | re.IGNORECASE)
        if match:
            phone = match.group(1)
            if not phone.startswith("+"):
                phone = f"+{phone}"
            return {"phone": phone, "message": match.group(2)}
        return {}
