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
    cover_size = 10 * mm  # Increased cover size
    track_index_width = cover_size  # Make track index column same width as cover

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

    # Footer section at top
    footer_y = header_y - 2 * mm
    c.setFont(font_family, 6.5)
    footer_text = f"{label_name}, {catalog_no}, {year}, {genres}, ID: {release_id}"
    footer_text = truncate_text(footer_text, 120)
    c.drawString(x + padding, footer_y, footer_text)

    # Draw cover image (below footer)
    cover_y = footer_y - 3 * mm - cover_size
    cover_path = Path(release_folder) / "cover.jpg"
    if cover_path.exists():
        try:
            c.drawImage(
                str(cover_path),
                x + padding,
                cover_y,
                width=cover_size,
                height=cover_size,
                preserveAspectRatio=True,
                anchor="sw",
            )
        except Exception as e:
            logger.debug(f"Could not load cover image: {e}")

    # Draw artist and title (next to cover)
    # Align with track title start position (after track index column)
    text_x = x + padding + track_index_width + 2 * mm
    # Push down 4pt (approximately 1.4mm)
    text_y = cover_y + cover_size - 3 * mm - 1.4 * mm

    # Calculate available width for text (label width - cover - padding - qr code space)
    available_width = (
        LABEL_WIDTH - track_index_width - 4 * mm - 6 * mm
    )  # 6mm for QR code

    # Artist name with overflow protection
    c.setFont(font_family, 10)
    artist_width = c.stringWidth(artist, font_family, 10)
    if artist_width > available_width:
        # Truncate artist to fit
        while (
            c.stringWidth(artist + "...", font_family, 10) > available_width
            and len(artist) > 1
        ):
            artist = artist[:-1]
        artist = artist + "..."
    c.drawString(text_x, text_y, artist)

    # Title with overflow protection
    c.setFont(f"{font_family}-Bold", 14)
    text_y -= (
        5.5 * mm
    )  # Increased spacing from 3.5mm to 5.5mm (added 4pt ≈ 1.4mm extra + original spacing)
    title_width = c.stringWidth(title, f"{font_family}-Bold", 14)
    if title_width > available_width:
        # Truncate title to fit
        while (
            c.stringWidth(title + "...", f"{font_family}-Bold", 14) > available_width
            and len(title) > 1
        ):
            title = title[:-1]
        title = title + "..."
    c.drawString(text_x, text_y, title)

    # Track table section
    table_y = text_y - 7 * mm  # Adjusted for larger title

    # Table headers (very small)
    c.setFont(font_family, 7)
    col_pos = x + padding
    track_title_x = col_pos + track_index_width + 2 * mm  # Align with album title

    # Draw up to 8 tracks
    max_tracks = 8
    row_height = 3.5 * mm

    for i in range(max_tracks):
        row_y = table_y - (i * row_height)

        if i < len(tracklist):
            track = tracklist[i]
            position = str(track.get("position", ""))[:3]
            track_title = str(track.get("title", ""))[:28]

            # Try to get BPM and Key from analysis
            bpm = ""
            key = ""
            analysis_file = Path(release_folder) / f"{position}.json"
            if analysis_file.exists():
                try:
                    with open(analysis_file) as f:
                        analysis = json.load(f)
                        # Extract BPM from rhythm section
                        bpm_value = analysis.get("rhythm", {}).get("bpm", 0)
                        if bpm_value:
                            bpm = str(int(bpm_value))
                        # Extract key and scale from tonal section
                        key_info = analysis.get("tonal", {}).get("key_temperley", {})
                        key_note = key_info.get("key", "")
                        key_scale = key_info.get("scale", "")
                        if key_note and key_scale:
                            # Format as "C maj" or "A min"
                            scale_abbr = "maj" if key_scale == "major" else "min"
                            key = f"{key_note} {scale_abbr}"
                        elif key_note:
                            key = key_note
                except:
                    pass

            # Draw track info
            c.setFont(font_family, 7.5)

            # Right-align track position within the track index column
            position_width = c.stringWidth(position, font_family, 7.5)
            position_x = col_pos + track_index_width - position_width
            c.drawString(position_x, row_y, position)

            # Draw track title aligned with album title
            c.drawString(track_title_x, row_y, track_title)

            # Draw BPM and Key if available
            if bpm:
                c.drawString(col_pos + 48 * mm, row_y, bpm)
            if key:
                c.drawString(col_pos + 58 * mm, row_y, key)

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

    # Draw QR code if available (top-right corner)
    qr_path = Path(release_folder) / "qrcode.png"
    if qr_path.exists():
        try:
            qr_size = 6 * mm  # Increased slightly for better scannability
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
