"""
QR type registry — all available builders in display order.
"""

from qr_types.base import QRBuilder
from qr_types.gps_builder import GPSBuilder
from qr_types.phone_builder import PhoneBuilder
from qr_types.simple_builders import EmailBuilder, TextBuilder, URLBuilder
from qr_types.sms_builder import SMSBuilder
from qr_types.vcard_builder import VCardBuilder
from qr_types.whatsapp_builder import WhatsAppBuilder
from qr_types.wifi_builder import WiFiBuilder

# Ordered list used by the type selector ComboBox
ALL_BUILDERS: list[QRBuilder] = [
    URLBuilder(),
    TextBuilder(),
    EmailBuilder(),
    WiFiBuilder(),
    WhatsAppBuilder(),
    SMSBuilder(),
    PhoneBuilder(),
    GPSBuilder(),
    VCardBuilder(),
]

QR_TYPES: list[str] = [b.display_name for b in ALL_BUILDERS]

_BUILDERS_BY_NAME: dict[str, QRBuilder] = {b.display_name: b for b in ALL_BUILDERS}
_BUILDERS_BY_ID: dict[str, QRBuilder] = {b.type_id: b for b in ALL_BUILDERS}


def get_builder(display_name: str) -> QRBuilder | None:
    """Return builder by UI display name (e.g. 'WiFi')."""
    return _BUILDERS_BY_NAME.get(display_name)


def get_builder_by_id(type_id: str) -> QRBuilder | None:
    """Return builder by stored type id (e.g. 'wifi')."""
    return _BUILDERS_BY_ID.get(type_id.lower())
