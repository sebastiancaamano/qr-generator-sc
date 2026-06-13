"""
Shared validation helpers for QR field values.

Returns i18n keys as error messages (third tuple element) for UI translation.
Validation logic is unchanged; only error payloads use translation keys.
"""

import re
from typing import Tuple

# E.164-ish: optional +, 7–15 digits
_PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_URL_PATTERN = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$",
    re.IGNORECASE,
)


def normalize_phone(raw: str, keep_plus: bool = True) -> str:
    """Strip spaces and invalid chars; keep leading + when requested."""
    raw = raw.strip()
    has_plus = raw.startswith("+")
    digits = re.sub(r"[^\d]", "", raw)
    if keep_plus and has_plus:
        return f"+{digits}"
    return digits


def validate_phone(raw: str, required: bool = True) -> Tuple[bool, str, str]:
    """Validate international phone number."""
    stripped = raw.strip()
    if not stripped:
        if required:
            return False, "", "validation.phone_required"
        return True, "", ""

    normalized = normalize_phone(stripped)
    if not _PHONE_PATTERN.match(normalized):
        return False, normalized, "validation.phone_invalid"
    return True, normalized, ""


def validate_email(raw: str, required: bool = True) -> Tuple[bool, str, str]:
    """Validate email address."""
    value = raw.strip()
    if not value:
        if required:
            return False, "", "validation.email_required"
        return True, "", ""

    if not _EMAIL_PATTERN.match(value):
        return False, value, "validation.email_invalid"
    return True, value, ""


def validate_url(raw: str, required: bool = True) -> Tuple[bool, str, str]:
    """Validate HTTP/HTTPS URL."""
    value = raw.strip()
    if not value:
        if required:
            return False, "", "validation.url_required"
        return True, "", ""

    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"

    if not _URL_PATTERN.match(value):
        return False, value, "validation.url_invalid"
    return True, value, ""


def validate_latitude(raw: str) -> Tuple[bool, str, str]:
    """Validate latitude in decimal degrees (-90 to 90)."""
    value = raw.strip().replace(",", ".")
    if not value:
        return False, "", "validation.latitude_required"

    try:
        lat = float(value)
    except ValueError:
        return False, value, "validation.latitude_invalid"

    if not -90.0 <= lat <= 90.0:
        return False, value, "validation.latitude_range"
    return True, str(lat), ""


def validate_longitude(raw: str) -> Tuple[bool, str, str]:
    """Validate longitude in decimal degrees (-180 to 180)."""
    value = raw.strip().replace(",", ".")
    if not value:
        return False, "", "validation.longitude_required"

    try:
        lng = float(value)
    except ValueError:
        return False, value, "validation.longitude_invalid"

    if not -180.0 <= lng <= 180.0:
        return False, value, "validation.longitude_range"
    return True, str(lng), ""


def validate_text_length(
    raw: str,
    max_length: int,
    field_key: str,
    required: bool = True,
) -> Tuple[bool, str, str]:
    """Validate plain text length."""
    value = raw.strip()
    if not value:
        if required:
            return False, "", f"validation.{field_key}_required"
        return True, "", ""

    if len(value) > max_length:
        return False, value, f"validation.{field_key}_max_length|{max_length}"
    return True, value, ""


def validate_non_empty(raw: str, field_key: str) -> Tuple[bool, str, str]:
    """Ensure a field is not blank."""
    value = raw.strip()
    if not value:
        return False, "", f"validation.{field_key}_required"
    return True, value, ""
