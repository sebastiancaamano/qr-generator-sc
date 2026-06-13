"""
Translation Manager — centralized i18n for QR Generator SC.

Only affects visible UI strings. Internal identifiers (type ids, field keys,
storage keys) remain unchanged.
"""

from __future__ import annotations

from typing import Callable, Optional

from i18n.translations_en import TRANSLATIONS_EN
from i18n.translations_es import TRANSLATIONS_ES

SUPPORTED_LANGUAGES = ("en", "es")

# Internal QR type id (dropdown value) → translation key
QR_TYPE_I18N_KEYS: dict[str, str] = {
    "URL": "qr_type_url",
    "Text": "qr_type_text",
    "Email": "qr_type_email",
    "WiFi": "qr_type_wifi",
    "WhatsApp": "qr_type_whatsapp",
    "SMS": "qr_type_sms",
    "Teléfono": "qr_type_phone",
    "GPS": "qr_type_gps",
    "vCard": "qr_type_vcard",
}

# Form field key → label translation key
FIELD_LABEL_KEYS: dict[str, str] = {
    "content": "field_url",  # overridden per QR type in UI helper
    "ssid": "field_ssid",
    "password": "field_password",
    "security": "field_security_type",
    "phone": "field_phone",
    "message": "field_message",
    "latitude": "field_latitude",
    "longitude": "field_longitude",
    "name": "field_name",
    "company": "field_company",
    "email": "field_email",
    "website": "field_website",
}

# Form field key → hint translation key (per QR type where needed)
FIELD_HINT_KEYS: dict[tuple[str, str], str] = {
    ("URL", "content"): "hint_url",
    ("Text", "content"): "hint_text",
    ("Email", "content"): "hint_email",
    ("WiFi", "ssid"): "hint_ssid",
    ("WiFi", "password"): "hint_password_optional",
    ("WhatsApp", "phone"): "hint_phone_intl",
    ("SMS", "phone"): "hint_phone",
    ("SMS", "message"): "hint_message",
    ("Teléfono", "phone"): "hint_phone",
    ("GPS", "latitude"): "hint_latitude",
    ("GPS", "longitude"): "hint_longitude",
    ("vCard", "name"): "hint_name",
    ("vCard", "company"): "hint_company",
    ("vCard", "email"): "hint_email",
    ("vCard", "phone"): "hint_phone",
    ("vCard", "website"): "hint_website",
}

# WiFi security internal value → translation key
WIFI_SECURITY_I18N: dict[str, str] = {
    "WPA": "wifi_security_wpa",
    "WPA2": "wifi_security_wpa2",
    "WEP": "wifi_security_wep",
    "Sin contraseña": "wifi_security_none",
}

# Reverse map: translated WiFi security label → internal value
WIFI_SECURITY_INTERNAL: dict[str, str] = {v: k for k, v in WIFI_SECURITY_I18N.items()}


class TranslationManager:
    """Loads catalogs, persists language, and notifies UI on change."""

    _catalogs = {
        "en": TRANSLATIONS_EN,
        "es": TRANSLATIONS_ES,
    }

    def __init__(self, storage=None, language: str = "en"):
        self._storage = storage
        self._language = language if language in SUPPORTED_LANGUAGES else "en"
        self._listeners: list[Callable[[], None]] = []

    @property
    def language(self) -> str:
        return self._language

    def translate(self, key: str, **kwargs) -> str:
        """Resolve a translation key to localized visible text."""
        catalog = self._catalogs.get(self._language, TRANSLATIONS_EN)
        text = catalog.get(key) or TRANSLATIONS_EN.get(key) or key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    def translate_validation(self, error: str | None) -> str:
        """Translate validation error keys, including max-length suffix."""
        if not error:
            return ""
        if "|" in error:
            key, param = error.split("|", 1)
            if key.endswith("_max_length"):
                return self.translate(key, max=param)
            if key == "validation.unknown_qr_type":
                return self.translate(key, type=param)
            return self.translate(key)
        return self.translate(error)

    def translate_qr_type(self, internal_type: str) -> str:
        key = QR_TYPE_I18N_KEYS.get(internal_type, internal_type)
        return self.translate(key)

    def translate_field_label(self, field_key: str, qr_type: str) -> str:
        if field_key == "content":
            type_key = QR_TYPE_I18N_KEYS.get(qr_type, "field_text")
            if qr_type == "URL":
                return self.translate("field_url")
            if qr_type == "Text":
                return self.translate("field_text")
            if qr_type == "Email":
                return self.translate("field_email")
        label_key = FIELD_LABEL_KEYS.get(field_key, field_key)
        return self.translate(label_key)

    def translate_field_hint(self, field_key: str, qr_type: str) -> str:
        hint_key = FIELD_HINT_KEYS.get((qr_type, field_key), "")
        return self.translate(hint_key) if hint_key else ""

    def translate_wifi_security(self, internal_value: str) -> str:
        key = WIFI_SECURITY_I18N.get(internal_value, internal_value)
        return self.translate(key)

    def wifi_security_internal(self, display_value: str) -> str:
        """Map localized dropdown label back to internal security token."""
        for internal, i18n_key in WIFI_SECURITY_I18N.items():
            if self.translate(i18n_key) == display_value:
                return internal
        return WIFI_SECURITY_INTERNAL.get(display_value, display_value)

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        if language == self._language:
            return
        self._language = language
        if self._storage is not None:
            try:
                self._storage.set_language(language)
            except Exception:
                pass
        for listener in self._listeners:
            try:
                listener()
            except Exception:
                pass

    def on_change(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)


# Module-level singleton for convenient translate() access from UI layers
_manager: Optional[TranslationManager] = None


def init_i18n(manager: TranslationManager) -> None:
    global _manager
    _manager = manager


def get_i18n() -> TranslationManager:
    if _manager is None:
        return TranslationManager()
    return _manager


def translate(key: str, **kwargs) -> str:
    return get_i18n().translate(key, **kwargs)


def t(key: str, **kwargs) -> str:
    """Short alias used in UI code."""
    return translate(key, **kwargs)
