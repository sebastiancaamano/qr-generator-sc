"""
SVG Export Service — QR Generator SC (V4)
Generates vector QR exports independent of the UI layer.
"""

import base64
import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image
from qrcode.image.svg import SvgPathImage

from models.qr_entry import QREntry
from services.qr_service import EXPORT_DIR
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage


class SvgExportError(Exception):
    """Raised when SVG export validation or generation fails."""


class SvgExportService:
    """Builds, validates, and persists QR code SVG files."""

    EXPORT_FORMAT = "svg"

    def __init__(
        self,
        storage: HistoryStorage,
        project_storage: Optional[ProjectStorage] = None,
    ):
        self._storage = storage
        self._project_storage = project_storage
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────

    def validate_export(self, content: str) -> None:
        """Ensure payload is suitable for SVG export."""
        if not content or not content.strip():
            raise SvgExportError("validation.export_content_required")

    def export_svg(
        self,
        content: str,
        qr_type: str,
        foreground_color: str,
        background_color: str,
        size: int,
        margin: int,
        logo: Optional[Image.Image] = None,
        logo_opacity: float = 1.0,
        logo_size_percent: int = 20,
        project_id: str = "",
        project_name: str = "General",
        project_folder_name: str = "",
    ) -> QREntry:
        """
        Save QR as SVG, persist to history, return QREntry.
        Uses the same folder layout and naming rules as PNG export.
        """
        self.validate_export(content)

        folder_name = self._safe_folder_name(
            project_folder_name or project_name or "General"
        )
        project_folder = EXPORT_DIR / folder_name
        project_folder.mkdir(parents=True, exist_ok=True)

        filename = self._format_filename(content, qr_type)
        filepath = project_folder / filename
        filepath = self._ensure_unique_filepath(filepath)

        svg_data = self._build_svg(
            content=content,
            foreground_color=foreground_color,
            background_color=background_color,
            size=size,
            margin=margin,
            logo=logo,
            logo_opacity=logo_opacity,
            logo_size_percent=logo_size_percent,
        )
        filepath.write_text(svg_data, encoding="utf-8")

        entry = QREntry(
            id=str(uuid.uuid4()),
            content=content,
            qr_type=qr_type,
            filename=filename,
            project_id=project_id,
            project_name=project_name,
            filepath=str(filepath),
            size=size,
            foreground_color=foreground_color,
            background_color=background_color,
            export_format=self.EXPORT_FORMAT,
        )
        self._storage.add(entry)
        if self._project_storage and project_id:
            self._project_storage.increment_qr_count(project_id)
        return entry

    # ── SVG generation ────────────────────────────────────────

    def _build_svg(
        self,
        content: str,
        foreground_color: str,
        background_color: str,
        size: int,
        margin: int,
        logo: Optional[Image.Image],
        logo_opacity: float,
        logo_size_percent: int,
    ) -> str:
        """Produce final SVG string with configured size and optional logo."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=margin,
        )
        qr.add_data(content)
        qr.make(fit=True)

        buffer = io.BytesIO()
        qr.make_image(
            image_factory=SvgPathImage,
            fill_color=foreground_color,
            back_color=background_color,
        ).save(buffer)
        svg = buffer.getvalue().decode("utf-8")
        svg = self._add_background_rect(svg, background_color)
        svg = self._apply_export_size(svg, size)
        if logo is not None:
            svg = self._embed_logo(svg, logo, logo_opacity, logo_size_percent)
        return svg

    def _apply_export_size(self, svg: str, size: int) -> str:
        """Set explicit pixel dimensions while preserving vector viewBox."""
        return re.sub(
            r'(<svg[^>]*)\s+width="[^"]*"\s+height="[^"]*"',
            rf'\1 width="{size}px" height="{size}px"',
            svg,
            count=1,
        )

    def _embed_logo(
        self,
        svg: str,
        logo: Image.Image,
        logo_opacity: float,
        logo_size_percent: int,
    ) -> str:
        """Insert centered raster logo as embedded PNG inside the SVG."""
        try:
            viewbox = self._parse_viewbox(svg)
            if not viewbox:
                return svg

            vb_w, vb_h = viewbox
            logo_side = vb_w * max(1, min(logo_size_percent, 30)) / 100.0
            x = (vb_w - logo_side) / 2.0
            y = (vb_h - logo_side) / 2.0
            opacity = max(0.0, min(1.0, logo_opacity))

            logo_rgba = logo.convert("RGBA") if logo.mode != "RGBA" else logo.copy()
            pixel_size = max(32, int(logo_side * 8))
            logo_rgba = logo_rgba.resize(
                (pixel_size, pixel_size), Image.Resampling.LANCZOS
            )

            if opacity < 1.0:
                alpha = logo_rgba.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                logo_rgba.putalpha(alpha)

            png_buf = io.BytesIO()
            logo_rgba.save(png_buf, format="PNG")
            encoded = base64.b64encode(png_buf.getvalue()).decode("ascii")

            image_tag = (
                f"<image "
                f'href="data:image/png;base64,{encoded}" '
                f'x="{x:.4f}" '
                f'y="{y:.4f}" '
                f'width="{logo_side:.4f}" '
                f'height="{logo_side:.4f}" '
                f'opacity="{opacity}" '
                f'preserveAspectRatio="xMidYMid meet"/>'
            )
            return svg.replace("</svg>", f"{image_tag}</svg>")
        except Exception:
            return svg

    def _parse_viewbox(self, svg: str) -> Optional[tuple[float, float]]:
        match = re.search(r'viewBox="0\s+0\s+([\d.]+)\s+([\d.]+)"', svg)
        if not match:
            return None
        return float(match.group(1)), float(match.group(2))

    # ── Path helpers (aligned with QRService) ─────────────────

    def _format_filename(self, content: str, qr_type: str) -> str:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        safe_content = self._slugify(content) or "qr"
        safe_type = self._slugify(qr_type.upper()) or "QR"
        return f"{date_prefix}_{safe_type}_{safe_content}.svg"

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
            candidate = filepath.with_name(
                f"{filepath.stem}_{counter}{filepath.suffix}"
            )
            counter += 1
        return candidate

    def _add_background_rect(
        self,
        svg: str,
        background_color: str,
    ) -> str:

        match = re.search(
            r'viewBox="0\s+0\s+([\d.]+)\s+([\d.]+)"',
            svg,
        )

        if not match:
            return svg

        width = match.group(1)
        height = match.group(2)

        rect = (
            f"<rect "
            f'x="0" '
            f'y="0" '
            f'width="{width}" '
            f'height="{height}" '
            f'fill="{background_color}"'
            f"/>"
        )

        svg = re.sub(
            r"(<svg[^>]*>)",
            r"\1\n" + rect,
            svg,
            count=1,
        )

        return svg
