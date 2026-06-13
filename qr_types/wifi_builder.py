"""WiFi network QR builder — WIFI:T:…;S:…;P:…;;"""

from qr_types.base import BuildResult, FieldDef, FieldKind, QRBuilder
from validators.common import validate_non_empty, validate_text_length

WIFI_SECURITY_OPTIONS = ("WPA", "WPA2", "WEP", "Sin contraseña")

# Maps UI label → WiFi QR T: parameter
_SECURITY_MAP = {
    "WPA": "WPA",
    "WPA2": "WPA",  # WPA2 uses T:WPA per de-facto standard
    "WEP": "WEP",
    "Sin contraseña": "nopass",
}


class WiFiBuilder(QRBuilder):
    type_id = "wifi"
    display_name = "WiFi"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="ssid",
                label="SSID (nombre de red)",
                hint="MiRed",
                max_length=32,
            ),
            FieldDef(
                key="password",
                label="Contraseña",
                hint="Opcional si la red es abierta",
                kind=FieldKind.PASSWORD,
                required=False,
                max_length=63,
            ),
            FieldDef(
                key="security",
                label="Tipo de seguridad",
                kind=FieldKind.SELECT,
                options=WIFI_SECURITY_OPTIONS,
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, ssid, err = validate_non_empty(fields.get("ssid", ""), "ssid")
        if not ok:
            return BuildResult(error=err, fields=fields)

        ok, ssid, err = validate_text_length(ssid, 32, "ssid")
        if not ok:
            return BuildResult(error=err, fields=fields)

        security = fields.get("security", "WPA2") or "WPA2"
        if security not in _SECURITY_MAP:
            return BuildResult(error="validation.wifi_security_invalid", fields=fields)

        t_param = _SECURITY_MAP[security]
        password = fields.get("password", "").strip()

        if t_param != "nopass":
            ok, password, err = validate_non_empty(password, "password")
            if not ok:
                return BuildResult(error=err, fields=fields)
            ok, password, err = validate_text_length(password, 63, "password")
            if not ok:
                return BuildResult(error=err, fields=fields)
        else:
            password = ""

        ssid_esc = self._escape_wifi_value(ssid)
        parts = [f"WIFI:T:{t_param}", f"S:{ssid_esc}"]
        if t_param != "nopass":
            parts.append(f"P:{self._escape_wifi_value(password)}")
        content = ";".join(parts) + ";;"

        return BuildResult(
            content=content,
            fields={"ssid": ssid, "password": password, "security": security},
        )

    def parse_from_content(self, content: str) -> dict[str, str]:
        """Parse WIFI:T:…;S:…;P:…;; back into form fields."""
        if not content.upper().startswith("WIFI:"):
            return {}

        fields: dict[str, str] = {"security": "WPA2", "password": "", "ssid": ""}
        body = content[5:].rstrip(";")
        for part in body.split(";"):
            if not part or ":" not in part:
                continue
            key, _, value = part.partition(":")
            value = value.replace("\\;", ";").replace("\\:", ":").replace("\\,", ",")
            value = value.replace("\\\\", "\\")
            if key == "T":
                reverse = {v: k for k, v in _SECURITY_MAP.items()}
                fields["security"] = reverse.get(value, "WPA2")
            elif key == "S":
                fields["ssid"] = value
            elif key == "P":
                fields["password"] = value
        return fields
