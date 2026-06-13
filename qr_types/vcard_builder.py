"""vCard contact QR builder — BEGIN:VCARD … END:VCARD"""

from qr_types.base import BuildResult, FieldDef, QRBuilder
from validators.common import (
    validate_email,
    validate_non_empty,
    validate_phone,
    validate_text_length,
    validate_url,
)


class VCardBuilder(QRBuilder):
    type_id = "vcard"
    display_name = "vCard"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(key="name", label="Nombre", hint="Juan Pérez"),
            FieldDef(
                key="company",
                label="Empresa",
                hint="Mi Empresa",
                required=False,
            ),
            FieldDef(
                key="email",
                label="Email",
                hint="juan@empresa.cl",
                required=False,
            ),
            FieldDef(
                key="phone",
                label="Teléfono",
                hint="+56912345678",
                required=False,
            ),
            FieldDef(
                key="website",
                label="Sitio web",
                hint="https://empresa.cl",
                required=False,
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, name, err = validate_non_empty(fields.get("name", ""), "name")
        if not ok:
            return BuildResult(error=err, fields=fields)

        ok, name, err = validate_text_length(name, 200, "name")
        if not ok:
            return BuildResult(error=err, fields=fields)

        company = fields.get("company", "").strip()
        if company:
            ok, company, err = validate_text_length(
                company, 200, "company", required=False
            )
            if not ok:
                return BuildResult(error=err, fields=fields)

        email = fields.get("email", "").strip()
        if email:
            ok, email, err = validate_email(email, required=False)
            if not ok:
                return BuildResult(error=err, fields=fields)

        phone = fields.get("phone", "").strip()
        if phone:
            ok, phone, err = validate_phone(phone, required=False)
            if not ok:
                return BuildResult(error=err, fields=fields)
            if not phone.startswith("+"):
                phone = f"+{phone.lstrip('+')}"

        website = fields.get("website", "").strip()
        if website:
            ok, website, err = validate_url(website, required=False)
            if not ok:
                return BuildResult(error=err, fields=fields)

        # At least one contact method beyond name is recommended but not required
        lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{name}"]
        if company:
            lines.append(f"ORG:{company}")
        if email:
            lines.append(f"EMAIL:{email}")
        if phone:
            lines.append(f"TEL:{phone}")
        if website:
            lines.append(f"URL:{website}")
        lines.append("END:VCARD")

        content = "\n".join(lines)
        return BuildResult(
            content=content,
            fields={
                "name": name,
                "company": company,
                "email": email,
                "phone": phone,
                "website": website,
            },
        )

    def parse_from_content(self, content: str) -> dict[str, str]:
        if "BEGIN:VCARD" not in content.upper():
            return {}

        fields: dict[str, str] = {
            "name": "",
            "company": "",
            "email": "",
            "phone": "",
            "website": "",
        }
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("FN:"):
                fields["name"] = line[3:]
            elif line.startswith("ORG:"):
                fields["company"] = line[4:]
            elif line.startswith("EMAIL:"):
                fields["email"] = line[6:]
            elif line.startswith("TEL:"):
                fields["phone"] = line[4:]
            elif line.startswith("URL:"):
                fields["website"] = line[4:]
        return fields
