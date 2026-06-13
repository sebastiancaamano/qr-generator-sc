"""
PDF Export Service — QR Generator SC (V4.1)
Generates professional PDF exports independent of the UI layer.
"""

import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from models.qr_entry import QREntry
from services.qr_service import EXPORT_DIR
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage


class PdfExportError(Exception):
    """Raised when PDF export validation fails."""


class PdfExportService:
    """Builds, validates and persists PDF exports."""

    EXPORT_FORMAT = "pdf"

    FONT_NAME = "VictorMono"

    FONT_PATH = Path("assets/fonts/VictorMono-Regular.ttf")

    def __init__(
        self,
        storage: HistoryStorage,
        project_storage: Optional[ProjectStorage] = None,
    ):
        self._storage = storage
        self._project_storage = project_storage

        EXPORT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self.FONT_PATH.exists():
            pdfmetrics.registerFont(
                TTFont(
                    self.FONT_NAME,
                    str(self.FONT_PATH),
                )
            )

    # ─────────────────────────────────────────────
    # Validation
    # ─────────────────────────────────────────────

    def validate_export(
        self,
        content: str,
        qr_png_path: str,
    ) -> None:

        if not content or not content.strip():
            raise PdfExportError("validation.export_content_required")

        if not qr_png_path:
            raise PdfExportError("validation.qr_image_required")

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def export_pdf(
        self,
        content: str,
        qr_type: str,
        foreground_color: str,
        background_color: str,
        size: int,
        margin: int,
        logo=None,
        logo_opacity: float = 1.0,
        logo_size_percent: int = 20,
        project_id: str = "",
        project_name: str = "General",
        project_folder_name: str = "",
    ) -> QREntry:

        if not content.strip():
            raise PdfExportError("validation.export_content_required")

        folder_name = self._safe_folder_name(
            project_folder_name or project_name or "General"
        )

        project_folder = EXPORT_DIR / folder_name

        project_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = self._format_filename(
            content,
            qr_type,
        )

        filepath = project_folder / filename

        filepath = self._ensure_unique_filepath(filepath)

        self._build_pdf(
            pdf_path=filepath,
            content=content,
            qr_type=qr_type,
            foreground_color=foreground_color,
            background_color=background_color,
            size=size,
            margin=margin,
            logo=logo,
            logo_opacity=logo_opacity,
            logo_size_percent=logo_size_percent,
        )

        entry = QREntry(
            id=str(uuid.uuid4()),
            content=content,
            qr_type=qr_type,
            filename=filename,
            filepath=str(filepath),
            project_id=project_id,
            project_name=project_name,
            foreground_color=foreground_color,
            background_color=background_color,
            export_format=self.EXPORT_FORMAT,
        )

        self._storage.add(entry)

        if self._project_storage and project_id:
            self._project_storage.increment_qr_count(project_id)

        return entry

    # ─────────────────────────────────────────────
    # PDF Generation
    # ─────────────────────────────────────────────

    def _build_pdf(
        self,
        pdf_path: Path,
        content: str,
        qr_type: str,
        foreground_color: str,
        background_color: str,
        size: int,
        margin: int,
        logo,
        logo_opacity: float,
        logo_size_percent: int,
    ) -> None:

        doc = SimpleDocTemplate(
            str(pdf_path),
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        title_style = ParagraphStyle(
            name="title",
            fontName=self.FONT_NAME,
            fontSize=20,
            leading=28,
        )

        body_style = ParagraphStyle(
            name="body",
            fontName=self.FONT_NAME,
            fontSize=8,
            leading=14,
        )

        story = []

        # Header

        story.append(
            Paragraph(
                "QR GENERATOR SC",
                title_style,
            )
        )

        story.append(
            Spacer(
                1,
                10,
            )
        )

        story.append(
            Paragraph(
                f"TYPE: {qr_type.upper()}",
                body_style,
            )
        )

        story.append(
            Paragraph(
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                15,
            )
        )

        # QR Image

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=margin,
        )

        qr.add_data(content)
        qr.make(fit=True)

        qr_img = qr.make_image(
            fill_color=foreground_color,
            back_color=background_color,
        ).convert("RGBA")

        # Aplicar logo si existe
        if logo:

            logo_side = int(qr_img.size[0] * min(max(logo_size_percent, 1), 40) / 100)

            logo_resized = logo.resize(
                (logo_side, logo_side),
                Image.Resampling.LANCZOS,
            )

            pos = (
                (qr_img.size[0] - logo_side) // 2,
                (qr_img.size[1] - logo_side) // 2,
            )

            qr_img.paste(
                logo_resized,
                pos,
                logo_resized,
            )

        temp_qr = pdf_path.with_suffix(".png")

        qr_img.save(
            temp_qr,
            format="PNG",
        )

        pdf_qr_size = max(40 * mm, min(120 * mm, (size / 512) * 90 * mm))

        qr_image = RLImage(
            str(temp_qr),
            width=pdf_qr_size,
            height=pdf_qr_size,
        )

        story.append(qr_image)

        story.append(
            Spacer(
                1,
                20,
            )
        )

        story.append(
            Paragraph(
                "CONTENT",
                body_style,
            )
        )

        story.append(
            Paragraph(
                content,
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                15,
            )
        )

        story.append(
            Paragraph(
                f"FOREGROUND: {foreground_color}",
                body_style,
            )
        )

        story.append(
            Paragraph(
                f"BACKGROUND: {background_color}",
                body_style,
            )
        )

        story.append(
            Spacer(
                1,
                25,
            )
        )

        story.append(
            Paragraph(
                "GENERATED WITH QR GENERATOR SC",
                body_style,
            )
        )

        doc.build(story)

        try:
            temp_qr.unlink()
        except Exception:
            pass

    def _format_filename(
        self,
        content: str,
        qr_type: str,
    ) -> str:
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        safe_content = self._slugify(content) or "qr"
        safe_type = self._slugify(qr_type.upper()) or "QR"
        return f"{date_prefix}_{safe_type}_{safe_content}.pdf"

    def _safe_folder_name(
        self,
        value: str,
    ) -> str:

        return (
            re.sub(
                r"[^A-Za-z0-9 _-]",
                "",
                value,
            ).strip()
            or "General"
        )

    def _slugify(
        self,
        value: str,
        max_length: int = 40,
    ) -> str:

        value = value.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "-",
            value,
        )

        value = value.strip("-")

        return value[:max_length]

    def _ensure_unique_filepath(
        self,
        filepath: Path,
    ) -> Path:

        candidate = filepath

        counter = 1

        while candidate.exists():
            candidate = filepath.with_name(
                f"{filepath.stem}_{counter}{filepath.suffix}"
            )
            counter += 1

        return candidate
