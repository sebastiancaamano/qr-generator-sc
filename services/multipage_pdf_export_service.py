"""
Multipage PDF Export Service — QR Generator SC (V4.1)
Generates professional multi-page PDF exports with batch support.
"""

import io
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

import qrcode
from PIL import Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models.qr_entry import QREntry
from services.qr_service import EXPORT_DIR
from storage.history_storage import HistoryStorage
from storage.project_storage import ProjectStorage


class MultipagePdfExportError(Exception):
    """Raised when multipage PDF export validation fails."""


class MultipagePdfExportService:
    """Builds, validates and persists multi-page PDF exports."""

    EXPORT_FORMAT = "pdf"

    FONT_NAME = "VictorMono"

    FONT_PATH = Path("assets/fonts/VictorMono-Regular.ttf")

    # Page distribution configurations
    PAGE_CONFIGS = {
        10: {"cols": 2, "rows": 5},
        20: {"cols": 4, "rows": 5},
        50: {"cols": 5, "rows": 10},
    }

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
        entries: List[QREntry],
    ) -> None:
        if not entries:
            raise MultipagePdfExportError("validation.no_qr_selected")
        
        if len(entries) == 0:
            raise MultipagePdfExportError("validation.empty_selection")

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def export_multipage_pdf(
        self,
        entries: List[QREntry],
        qr_per_page: int = 10,
        show_labels: bool = True,
        show_content: bool = False,
        show_type: bool = True,
        project_name: str = "BatchExport",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Export multiple QR codes to a multi-page PDF.
        
        Args:
            entries: List of QREntry objects to export
            qr_per_page: Number of QR codes per page (10, 20, or 50)
            show_labels: Whether to show labels under each QR
            show_content: Whether to show QR content under labels
            show_type: Whether to show QR type under labels
            project_name: Name for the export folder
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Path to the generated PDF file
        """
        self.validate_export(entries)

        if qr_per_page not in self.PAGE_CONFIGS:
            raise MultipagePdfExportError("validation.invalid_qr_per_page")

        folder_name = self._safe_folder_name(project_name or "BatchExport")
        project_folder = EXPORT_DIR / folder_name
        project_folder.mkdir(parents=True, exist_ok=True)

        date_prefix = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_prefix}_multipage_qr_export.pdf"
        filepath = project_folder / filename
        filepath = self._ensure_unique_filepath(filepath)

        self._build_multipage_pdf(
            pdf_path=filepath,
            entries=entries,
            qr_per_page=qr_per_page,
            show_labels=show_labels,
            show_content=show_content,
            show_type=show_type,
            progress_callback=progress_callback,
        )

        return str(filepath)

    def export_batch_by_project(
        self,
        project_id: str,
        project_name: str,
        qr_per_page: int = 10,
        show_labels: bool = True,
        show_content: bool = False,
        show_type: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Export all QR codes from a specific project to a multi-page PDF.
        
        Args:
            project_id: ID of the project to export
            project_name: Name of the project
            qr_per_page: Number of QR codes per page
            show_labels: Whether to show labels under each QR
            show_content: Whether to show QR content under labels
            show_type: Whether to show QR type under labels
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to the generated PDF file
        """
        entries = self._storage.all(project_id)
        
        if not entries:
            raise MultipagePdfExportError("validation.project_no_qr")

        return self.export_multipage_pdf(
            entries=entries,
            qr_per_page=qr_per_page,
            show_labels=show_labels,
            show_content=show_content,
            show_type=show_type,
            project_name=project_name,
            progress_callback=progress_callback,
        )

    def export_batch_by_selection(
        self,
        entry_ids: List[str],
        qr_per_page: int = 10,
        show_labels: bool = True,
        show_content: bool = False,
        show_type: bool = True,
        project_name: str = "SelectionExport",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Export selected QR codes by their IDs to a multi-page PDF.
        
        Args:
            entry_ids: List of QR entry IDs to export
            qr_per_page: Number of QR codes per page
            show_labels: Whether to show labels under each QR
            show_content: Whether to show QR content under labels
            show_type: Whether to show QR type under labels
            project_name: Name for the export folder
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to the generated PDF file
        """
        all_entries = self._storage.all()
        entries = [e for e in all_entries if e.id in entry_ids]
        
        if not entries:
            raise MultipagePdfExportError("validation.no_qr_selected")

        return self.export_multipage_pdf(
            entries=entries,
            qr_per_page=qr_per_page,
            show_labels=show_labels,
            show_content=show_content,
            show_type=show_type,
            project_name=project_name,
            progress_callback=progress_callback,
        )

    # ─────────────────────────────────────────────
    # PDF Generation
    # ─────────────────────────────────────────────

    def _build_multipage_pdf(
        self,
        pdf_path: Path,
        entries: List[QREntry],
        qr_per_page: int,
        show_labels: bool,
        show_content: bool,
        show_type: bool,
        progress_callback: Optional[Callable[[int, int], None]],
    ) -> None:
        doc = SimpleDocTemplate(
            str(pdf_path),
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        title_style = ParagraphStyle(
            name="title",
            fontName=self.FONT_NAME,
            fontSize=16,
            leading=22,
        )

        label_style = ParagraphStyle(
            name="label",
            fontName=self.FONT_NAME,
            fontSize=7,
            leading=10,
            alignment=1,  # Center alignment
        )

        content_style = ParagraphStyle(
            name="content",
            fontName=self.FONT_NAME,
            fontSize=6,
            leading=8,
            alignment=1,
        )

        config = self.PAGE_CONFIGS[qr_per_page]
        cols = config["cols"]
        rows = config["rows"]

        story = []
        total_entries = len(entries)

        # Process entries in pages
        for page_idx in range(0, total_entries, qr_per_page):
            page_entries = entries[page_idx:page_idx + qr_per_page]
            
            # Add page header
            if page_idx == 0:
                story.append(
                    Paragraph(
                        "QR GENERATOR SC - MULTIPAGE EXPORT",
                        title_style,
                    )
                )
                story.append(Spacer(1, 5 * mm))
                story.append(
                    Paragraph(
                        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        label_style,
                    )
                )
                story.append(Spacer(1, 10 * mm))
            else:
                story.append(
                    Paragraph(
                        f"Page {page_idx // qr_per_page + 1}",
                        title_style,
                    )
                )
                story.append(Spacer(1, 10 * mm))

            # Create grid for this page
            grid_data = []
            for row_idx in range(rows):
                row_data = []
                for col_idx in range(cols):
                    entry_idx = page_idx + row_idx * cols + col_idx
                    if entry_idx < len(page_entries):
                        entry = page_entries[row_idx * cols + col_idx]
                        cell_content = self._create_qr_cell(
                            entry,
                            show_labels,
                            show_content,
                            show_type,
                            label_style,
                            content_style,
                        )
                        row_data.append(cell_content)
                    else:
                        row_data.append("")
                grid_data.append(row_data)

            # Create table with proper spacing
            table = Table(
                grid_data,
                colWidths=[None] * cols,
                rowHeights=[None] * rows,
            )

            table_style = TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ])
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 10 * mm))

            # Report progress
            if progress_callback:
                progress_callback(min(page_idx + qr_per_page, total_entries), total_entries)

        doc.build(story)

    def _create_qr_cell(
        self,
        entry: QREntry,
        show_labels: bool,
        show_content: bool,
        show_type: bool,
        label_style: ParagraphStyle,
        content_style: ParagraphStyle,
    ) -> list:
        """Create a cell content for a single QR in the grid."""
        cell_content = []

        # Generate QR image
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(entry.content)
        qr.make(fit=True)
        qr_img = qr.make_image(
            fill_color=entry.foreground_color,
            back_color=entry.background_color,
        ).convert("RGBA")

        # Save to temporary buffer
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Create reportlab image (smaller for grid)
        qr_image = RLImage(img_buffer, width=35 * mm, height=35 * mm)
        cell_content.append(qr_image)

        # Add labels if enabled
        if show_labels:
            label_parts = []
            if show_type:
                label_parts.append(f"{entry.qr_type.upper()}")
            
            if label_parts:
                cell_content.append(Spacer(1, 2 * mm))
                cell_content.append(
                    Paragraph(" · ".join(label_parts), label_style)
                )

            if show_content:
                content_preview = entry.content if len(entry.content) <= 30 else entry.content[:27] + "…"
                cell_content.append(Spacer(1, 1 * mm))
                cell_content.append(Paragraph(content_preview, content_style))

        return cell_content

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
