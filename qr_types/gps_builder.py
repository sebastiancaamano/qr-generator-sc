"""GPS / geo-location QR builder — geo:<lat>,<lng>"""

import re

from qr_types.base import BuildResult, FieldDef, QRBuilder
from validators.common import validate_latitude, validate_longitude


class GPSBuilder(QRBuilder):
    type_id = "gps"
    display_name = "GPS"

    def field_definitions(self) -> list[FieldDef]:
        return [
            FieldDef(
                key="latitude",
                label="Latitud",
                hint="-33.4489",
            ),
            FieldDef(
                key="longitude",
                label="Longitud",
                hint="-70.6693",
            ),
        ]

    def build(self, fields: dict[str, str]) -> BuildResult:
        ok, lat, err = validate_latitude(fields.get("latitude", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)

        ok, lng, err = validate_longitude(fields.get("longitude", ""))
        if not ok:
            return BuildResult(error=err, fields=fields)

        content = f"geo:{lat},{lng}"
        return BuildResult(
            content=content,
            fields={"latitude": lat, "longitude": lng},
        )

    def parse_from_content(self, content: str) -> dict[str, str]:
        match = re.match(r"geo:([-\d.]+),([-\d.]+)", content, re.IGNORECASE)
        if match:
            return {"latitude": match.group(1), "longitude": match.group(2)}
        return {}
