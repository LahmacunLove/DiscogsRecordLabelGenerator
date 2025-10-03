#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReportLab PDF Label Generator for Discogs Releases

Creates PDF labels directly without LaTeX dependency.
Supports Avery Zweckform L4744REV-65 format (96mm x 50.8mm, 2x5 grid on A4).

@author: ffx
"""

import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from logger import logger


# Label dimensions for Avery Zweckform L4744REV-65
LABEL_WIDTH = 96 * mm
LABEL_HEIGHT = 50.8 * mm
LABELS_PER_ROW = 2
LABELS_PER_COL = 5
MARGIN_LEFT = 7 * mm
MARGIN_TOP = 21.5 * mm
HORIZONTAL_GAP = 4 * mm  # Gap between columns


def register_fonts():
    """Register system fonts for ReportLab"""
    try:
        # Try to register Liberation Sans (Helvetica alternative)
        pdfmetrics.registerFont(
            TTFont(
                "LiberationSans",
                "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
            )
        )
        pdfmetrics.registerFont(
            TTFont(
                "LiberationSans-Bold",
                "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
            )
        )
        return "LiberationSans"
    except:
        try:
            # Fallback to DejaVu Sans
            pdfmetrics.registerFont(
                TTFont(
                    "DejaVuSans", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
                )
            )
            pdfmetrics.registerFont(
                TTFont(
                    "DejaVuSans-Bold",
                    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
                )
            )
            return "DejaVuSans"
        except:
            # Use Helvetica as last resort (built-in)
            return "Helvetica"


def truncate_text(text, max_length):
    """Truncate text to max_length and add ellipsis if needed"""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def draw_label(c, x, y, metadata, release_folder, font_family):
    """
    Draw a single label at position (x, y) on the canvas

    Args:
        c: ReportLab canvas
        x, y: Bottom-left position of label
        metadata: Release metadata dict
        release_folder: Path to release folder
        font_family: Font family name to use
    """
    # Constants
    padding = 2 * mm
    cover_size = 8 * mm  # Reduced to not overflow artist/title height

    # Extract metadata
    artist = ", ".join(metadata.get("artist", ["Unknown Artist"]))[:45]
    title = metadata.get("title", "Unknown Title")[:45]
    label_name = ", ".join(metadata.get("label", [""]))[:30]
    catalog_no = ", ".join(metadata.get("catalog_numbers", [""]))[:20]
    year = metadata.get("year", "")
    genres = ", ".join(metadata.get("genres", [])[:2])[:30]
    release_id = metadata.get("release_id", "")
    tracklist = metadata.get("tracklist", [])

    # Header section
    header_y = y + LABEL_HEIGHT - padding

    # Draw cover image (top-left)
    cover_path = Path(release_folder) / "cover.jpg"
    if cover_path.exists():
        try:
            c.drawImage(
                str(cover_path),
                x + padding,
                header_y - cover_size,
                width=cover_size,
                height=cover_size,
                preserveAspectRatio=True,
                anchor="sw",
            )
        except Exception as e:
            logger.debug(f"Could not load cover image: {e}")

    # Draw artist and title (next to cover)
    text_x = x + padding + cover_size + 2 * mm
    text_y = header_y - 3 * mm

    c.setFont(font_family, 8)
    c.drawString(text_x, text_y, artist)

    c.setFont(f"{font_family}-Bold", 8)
    text_y -= 3.5 * mm
    c.drawString(text_x, text_y, title)

    # Track table section
    table_y = text_y - 4 * mm

    # Table headers (very small)
    c.setFont(font_family, 5)
    col_pos = x + padding

    # Draw up to 10 tracks
    max_tracks = 10
    row_height = 3.5 * mm

    for i in range(max_tracks):
        row_y = table_y - (i * row_height)

        if i < len(tracklist):
            track = tracklist[i]
            position = str(track.get("position", ""))[:3]
            track_title = str(track.get("title", ""))[:30]

            # Try to get BPM and Key from analysis
            bpm = ""
            key = ""
            analysis_file = Path(release_folder) / f"{position}.json"
            if analysis_file.exists():
                try:
                    with open(analysis_file) as f:
                        analysis = json.load(f)
                        bpm = (
                            str(int(analysis.get("bpm", 0)))
                            if analysis.get("bpm")
                            else ""
                        )
                        key = analysis.get("key", "")
                except:
                    pass

            # Draw track info
            c.setFont(font_family, 5.5)
            c.drawString(col_pos, row_y, position)
            c.drawString(col_pos + 8 * mm, row_y, track_title)
            c.drawString(col_pos + 50 * mm, row_y, bpm)
            c.drawString(col_pos + 60 * mm, row_y, key)

            # Draw waveform if available
            waveform_path = Path(release_folder) / f"{position}_waveform.png"
            if waveform_path.exists():
                try:
                    c.drawImage(
                        str(waveform_path),
                        col_pos + 70 * mm,
                        row_y - 0.5 * mm,
                        width=18 * mm,
                        height=3 * mm,
                        preserveAspectRatio=True,
                        anchor="sw",
                    )
                except Exception as e:
                    logger.debug(f"Could not load waveform: {e}")

    # Footer section
    footer_y = y + padding
    c.setFont(font_family, 4.5)
    footer_text = f"{label_name}, {catalog_no}, {year}, {genres}, ID: {release_id}"
    footer_text = truncate_text(footer_text, 120)
    c.drawString(x + padding, footer_y, footer_text)

    # Draw QR code if available (top-right corner)
    qr_path = Path(release_folder) / "qrcode.png"
    if qr_path.exists():
        try:
            qr_size = 4 * mm  # Reduced to 1/3 of original size (12mm / 3 = 4mm)
            c.drawImage(
                str(qr_path),
                x + LABEL_WIDTH - qr_size - padding,
                y + LABEL_HEIGHT - qr_size - padding,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                anchor="sw",
            )
        except Exception as e:
            logger.debug(f"Could not load QR code: {e}")


def create_label_pdf(
    library_path, output_dir, max_labels=None, specific_release=None, since_date=None
):
    """
    Create PDF labels from library releases

    Args:
        library_path: Path to library directory
        output_dir: Output directory for PDF
        max_labels: Maximum number of labels to generate
        specific_release: Specific release ID to generate
        since_date: Only generate labels for releases added since this date

    Returns:
        bool: True if successful
    """
    library_path = Path(library_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Register fonts
    font_family = register_fonts()
    logger.info(f"Using font: {font_family}")

    # Find releases with metadata
    releases = []
    for release_dir in library_path.iterdir():
        if not release_dir.is_dir():
            continue

        metadata_file = release_dir / "metadata.json"
        if not metadata_file.exists():
            continue

        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

            # Apply filters
            if specific_release and metadata.get("release_id") != specific_release:
                continue

            if since_date:
                timestamp = metadata.get("timestamp", "")
                if timestamp < since_date:
                    continue

            releases.append((release_dir, metadata))

            if max_labels and len(releases) >= max_labels:
                break

        except Exception as e:
            logger.warning(f"Could not load metadata from {release_dir}: {e}")

    if not releases:
        logger.warning("No releases found with metadata")
        return False

    logger.info(f"Generating PDF for {len(releases)} releases...")

    # Calculate pages needed
    labels_per_page = LABELS_PER_ROW * LABELS_PER_COL
    num_pages = (len(releases) + labels_per_page - 1) // labels_per_page

    # Create PDF
    pdf_filename = output_dir / f"vinyl_labels_{len(releases)}_releases.pdf"
    c = canvas.Canvas(str(pdf_filename), pagesize=A4)

    label_index = 0
    for page in range(num_pages):
        for row in range(LABELS_PER_COL):
            for col in range(LABELS_PER_ROW):
                if label_index >= len(releases):
                    break

                release_folder, metadata = releases[label_index]

                # Calculate position (ReportLab uses bottom-left origin)
                x = MARGIN_LEFT + col * (LABEL_WIDTH + HORIZONTAL_GAP)
                y = A4[1] - MARGIN_TOP - (row + 1) * LABEL_HEIGHT

                # Draw label
                draw_label(c, x, y, metadata, release_folder, font_family)

                # Debug: Draw border (optional)
                # c.rect(x, y, LABEL_WIDTH, LABEL_HEIGHT)

                label_index += 1

        # Add new page if more labels to come
        if label_index < len(releases):
            c.showPage()

    # Save PDF
    c.save()

    logger.success(f"✅ PDF generated: {pdf_filename}")
    logger.info(f"📄 {num_pages} pages with {len(releases)} labels")

    return True


def create_single_label_pdf(release_folder, metadata, output_path=None):
    """
    Create a PDF for a single release label

    Args:
        release_folder: Path to release folder
        metadata: Release metadata dict
        output_path: Optional output path (default: release_folder/label.pdf)

    Returns:
        bool: True if successful
    """
    release_folder = Path(release_folder)

    if not output_path:
        output_path = release_folder / "label.pdf"

    # Register fonts
    font_family = register_fonts()

    # Create single-label PDF
    c = canvas.Canvas(str(output_path), pagesize=A4)

    # Draw label at top-left position
    x = MARGIN_LEFT
    y = A4[1] - MARGIN_TOP - LABEL_HEIGHT

    draw_label(c, x, y, metadata, release_folder, font_family)

    c.save()

    logger.info(f"✅ Single label PDF created: {output_path}")
    return True
