"""
QR Service — QR Generator SC
Handles QR code generation, preview bytes, and file export.
"""

import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image
from qrcode.image.pil import PilImage

from models.qr_entry import QREntry
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage

EXPORT_DIR = Path.home() / "Downloads" / "QR Generator SC"
DEFAULT_QR_FOREGROUND = "#000000"
DEFAULT_QR_BACKGROUND = "#FFFFFF"
DEFAULT_QR_SIZE = 512
DEFAULT_QR_MARGIN = 4


class QRService:
    """Generates QR images and delegates persistence to HistoryStorage."""

    def __init__(
        self,
        storage: HistoryStorage,
        project_storage: Optional[ProjectStorage] = None,
        foreground_color: str = DEFAULT_QR_FOREGROUND,
        background_color: str = DEFAULT_QR_BACKGROUND,
        size: int = DEFAULT_QR_SIZE,
        margin: int = DEFAULT_QR_MARGIN,
    ):
        self._storage = storage
        self._project_storage = project_storage
        self._foreground_color = foreground_color
        self._background_color = background_color
        self._size = size
        self._margin = margin
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────

    def set_colors(self, foreground_color: str, background_color: str) -> None:
        self._foreground_color = foreground_color
        self._background_color = background_color

    def set_size(self, size: int) -> None:
        if size in (128, 256, 512, 1024):
            self._size = size

    def set_margin(self, margin: int) -> None:
        if margin in (0, 2, 4, 8):
            self._margin = margin

    def generate_preview_bytes(
        self,
        content: str,
        logo: Optional[Image.Image] = None,
        logo_opacity: float = 1.0,
    ) -> Optional[bytes]:
        """Return PNG bytes for in-app preview. Returns None on error."""
        if not content.strip():
            return None
        img = self._build_image(content, logo=logo, logo_opacity=logo_opacity)
        preview = img.resize((240, 240), Image.NEAREST)
        buf = io.BytesIO()
        preview.save(buf, format="PNG")
        return buf.getvalue()

    def export_png(
        self,
        content: str,
        qr_type: str,
        logo: Optional[Image.Image] = None,
        logo_opacity: float = 1.0,
        project_id: str = "",
        project_name: str = "General",
        project_folder_name: str = "",
    ) -> QREntry:
        """Save QR as PNG, persist to history, return QREntry."""
        folder_name = project_folder_name or self._safe_folder_name(
            project_name or "General"
        )
        project_folder = EXPORT_DIR / folder_name
        project_folder.mkdir(parents=True, exist_ok=True)

        filename = self._format_filename(content, qr_type)
        filepath = project_folder / filename
        filepath = self._ensure_unique_filepath(filepath)

        img = self._build_image(content, logo=logo, logo_opacity=logo_opacity)
        export_img = img.resize((self._size, self._size), Image.NEAREST)
        export_img.save(str(filepath), format="PNG")

        entry = QREntry(
            id=str(uuid.uuid4()),
            content=content,
            qr_type=qr_type,
            filename=filename,
            project_id=project_id,
            project_name=project_name,
            filepath=str(filepath),
            size=self._size,
            foreground_color=self._foreground_color,
            background_color=self._background_color,
            export_format="png",
        )
        self._storage.add(entry)
        if self._project_storage and project_id:
            self._project_storage.increment_qr_count(project_id)
        return entry

    def _format_filename(self, content: str, qr_type: str) -> str:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        safe_content = self._slugify(content) or "qr"
        safe_type = self._slugify(qr_type.upper()) or "QR"
        return f"{date_prefix}_{safe_type}_{safe_content}.png"

    def _safe_folder_name(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9 _-]", "", value).strip() or "General"

    def _slugify(self, value: str, max_length: int = 40) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = value.strip("-")
        return value[:max_length]

    def _ensure_unique_filepath(self, filepath: Path) -> Path:
        candidate = filepath
        counter = 1
        while candidate.exists():
            suffix = f"_{counter}"
            candidate = filepath.with_name(f"{filepath.stem}{suffix}{filepath.suffix}")
            counter += 1
        return candidate

    # ── Private ───────────────────────────────────────────────

    def _build_image(
        self,
        content: str,
        logo: Optional[Image.Image] = None,
        logo_opacity: float = 1.0,
    ) -> Image.Image:
        fill = self._foreground_color
        back = self._background_color

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=self._margin,
        )
        qr.add_data(content)
        qr.make(fit=True)
        img: Image.Image = qr.make_image(
            image_factory=PilImage,
            fill_color=fill,
            back_color=back,
        ).get_image()
        img = img.convert("RGB")

        # Apply logo if provided
        if logo:
            img = self._apply_logo(img, logo, logo_opacity)

        return img

    def _apply_logo(
        self,
        qr_img: Image.Image,
        logo_img: Image.Image,
        opacity: float,
    ) -> Image.Image:
        """Apply logo to center of QR code with opacity."""
        try:
            # Clamp opacity
            opacity = max(0.0, min(1.0, opacity))

            # Convert logo to RGBA with opacity
            if logo_img.mode != "RGBA":
                logo_img = logo_img.convert("RGBA")

            # Apply opacity to logo
            alpha = (
                logo_img.split()[3]
                if len(logo_img.split()) == 4
                else Image.new("L", logo_img.size, 255)
            )
            alpha = alpha.point(lambda p: int(p * opacity))
            logo_with_opacity = logo_img.copy()
            logo_with_opacity.putalpha(alpha)

            # Create temporary RGBA version of QR for composition
            qr_rgba = qr_img.convert("RGBA")

            # Calculate center position
            qr_w, qr_h = qr_rgba.size
            logo_w, logo_h = logo_with_opacity.size
            x = (qr_w - logo_w) // 2
            y = (qr_h - logo_h) // 2

            # Composite logo onto QR
            qr_rgba.paste(logo_with_opacity, (x, y), logo_with_opacity)

            # Convert back to RGB
            return qr_rgba.convert("RGB")
        except Exception:
            return qr_img
