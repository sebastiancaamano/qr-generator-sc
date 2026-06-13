"""Phone call QR builder — TEL:+<phone>"""

import re

from qr_types.base import BuildResult, FieldDef, QRBuilder
from validators.common import validate_phone


class PhoneBuilder(QRBuilder):
    type_id = "phone"
    display_name = "Teléfono"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="phone",
                label="Número telefónico",
                hint="+56912345678",
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, normalized, err = validate_phone(fields.get("phone", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)

        # Ensure E.164 with leading +
        tel = normalized if normalized.startswith("+") else f"+{normalized}"
        content = f"TEL:{tel}"
        return BuildResult(content=content, fields={"phone": tel})

    def parse_from_content(self, content: str) -> dict[str, str]:
        match = re.match(r"TEL:(\+?[0-9]+)", content, re.IGNORECASE)
        if match:
            phone = match.group(1)
            if not phone.startswith("+"):
                phone = f"+{phone}"
            return {"phone": phone}
        return {}
