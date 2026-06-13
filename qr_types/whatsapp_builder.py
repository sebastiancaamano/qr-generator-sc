"""WhatsApp deep-link QR builder — https://wa.me/<phone>"""

import re

from qr_types.base import BuildResult, FieldDef, QRBuilder
from validators.common import normalize_phone, validate_phone


class WhatsAppBuilder(QRBuilder):
    type_id = "whatsapp"
    display_name = "WhatsApp"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="phone",
                label="Número telefónico",
                hint="+56912345678 (código de país sin espacios)",
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, normalized, err = validate_phone(fields.get("phone", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)

        # wa.me requires digits only (no +)
        digits = normalize_phone(normalized, keep_plus=False)
        content = f"https://wa.me/{digits}"
        return BuildResult(content=content, fields={"phone": normalized})

    def parse_from_content(self, content: str) -> dict[str, str]:
        match = re.search(r"wa\.me/(\+?[0-9]+)", content, re.IGNORECASE)
        if match:
            phone = match.group(1)
            if not phone.startswith("+"):
                phone = f"+{phone}"
            return {"phone": phone}
        return {}
