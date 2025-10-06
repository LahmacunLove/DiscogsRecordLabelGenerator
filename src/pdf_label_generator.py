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
import numpy as np
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
    """
    Register system fonts for ReportLab with optimized fallback chain

    Priority order:
    1. Inter - Modern, designed for small sizes and high readability
    2. Source Sans Pro - Professional Adobe font
    3. Fira Sans - Mozilla's professional font
    4. Liberation Sans - Free Helvetica alternative
    5. DejaVu Sans - Fallback with good Unicode support
    6. Helvetica - Built-in PDF font (last resort)
    """
    # Try Inter (most loved modern font, optimized for small sizes)
    try:
        pdfmetrics.registerFont(
            TTFont("Inter", "/usr/share/fonts/inter/Inter-Regular.ttf")
        )
        pdfmetrics.registerFont(
            TTFont("Inter-Bold", "/usr/share/fonts/inter/Inter-Bold.ttf")
        )
        logger.info("Using Inter font for PDF labels")
        return "Inter"
    except:
        pass

    # Try Source Sans Pro (Adobe, professional)
    try:
        pdfmetrics.registerFont(
            TTFont(
                "SourceSansPro",
                "/usr/share/fonts/adobe-source-sans-pro/SourceSansPro-Regular.otf",
            )
        )
        pdfmetrics.registerFont(
            TTFont(
                "SourceSansPro-Bold",
                "/usr/share/fonts/adobe-source-sans-pro/SourceSansPro-Bold.otf",
            )
        )
        logger.info("Using Source Sans Pro font for PDF labels")
        return "SourceSansPro"
    except:
        pass

    # Try Fira Sans (Mozilla, professional)
    try:
        pdfmetrics.registerFont(
            TTFont("FiraSans", "/usr/share/fonts/fira-sans/FiraSans-Regular.otf")
        )
        pdfmetrics.registerFont(
            TTFont("FiraSans-Bold", "/usr/share/fonts/fira-sans/FiraSans-Bold.otf")
        )
        logger.info("Using Fira Sans font for PDF labels")
        return "FiraSans"
    except:
        pass

    # Try Liberation Sans (Helvetica alternative)
    try:
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
        logger.info("Using Liberation Sans font for PDF labels")
        return "LiberationSans"
    except:
        pass

    # Try DejaVu Sans (good Unicode support)
    try:
        pdfmetrics.registerFont(
            TTFont("DejaVuSans", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf")
        )
        pdfmetrics.registerFont(
            TTFont(
                "DejaVuSans-Bold",
                "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
            )
        )
        logger.info("Using DejaVu Sans font for PDF labels")
        return "DejaVuSans"
    except:
        pass

    # Use Helvetica as last resort (built-in to PDF)
    logger.warning(
        "No preferred fonts found, using Helvetica. Install Inter for best results: "
        "https://github.com/rsms/inter/releases"
    )
    return "Helvetica"


def truncate_text(text, max_length):
    """Truncate text to max_length and add ellipsis if needed"""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def draw_vector_waveform(c, x, y, width, height, audio_file_path):
    """
    Draw a simple, clean vector waveform directly in the PDF

    Args:
        c: ReportLab canvas
        x, y: Bottom-left position
        width, height: Dimensions in mm
        audio_file_path: Path to audio file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import subprocess

        # Use FFmpeg to get audio samples (much faster than loading full file)
        # Downsample to ~200-400 points for clean, simple waveform
        target_samples = 300

        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            str(audio_file_path),
            "-ac",
            "1",  # Mono
            "-ar",
            str(target_samples * 10),  # Sample rate for target points
            "-f",
            "f32le",  # 32-bit float
            "-acodec",
            "pcm_f32le",
            "-t",
            "30",  # Only first 30 seconds for speed
            "-hide_banner",
            "-loglevel",
            "error",
            "-",
        ]

        # Get audio data
        process = subprocess.Popen(
            ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        audio_data, _ = process.communicate()

        if not audio_data:
            return False

        # Convert to numpy array
        samples = np.frombuffer(audio_data, dtype=np.float32)

        if len(samples) == 0:
            return False

        # Downsample to target points by taking peaks
        chunk_size = max(1, len(samples) // target_samples)
        downsampled = []

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i : i + chunk_size]
            if len(chunk) > 0:
                # Use RMS for smoother waveform
                rms = np.sqrt(np.mean(chunk**2))
                downsampled.append(rms)

        if len(downsampled) < 2:
            return False

        # Normalize to -1 to 1 range
        max_val = max(abs(min(downsampled)), abs(max(downsampled)))
        if max_val > 0:
            downsampled = [s / max_val for s in downsampled]

        # Draw the waveform as vector paths
        c.setStrokeColor(black)
        c.setLineWidth(0.3)

        # Calculate positions
        num_points = len(downsampled)
        x_step = width / num_points
        y_center = y + height / 2
        y_scale = height / 2 * 0.9  # Use 90% of height

        # Draw waveform as a path (much cleaner than individual lines)
        path = c.beginPath()

        # Start from first point
        first_x = x
        first_y = y_center + (downsampled[0] * y_scale)
        path.moveTo(first_x, first_y)

        # Draw to each subsequent point
        for i, amplitude in enumerate(downsampled):
            point_x = x + (i * x_step)
            point_y = y_center + (amplitude * y_scale)
            path.lineTo(point_x, point_y)

        # Draw the path
        c.drawPath(path, stroke=1, fill=0)

        # Optionally draw mirrored waveform below center for symmetry
        path_mirror = c.beginPath()
        path_mirror.moveTo(first_x, y_center - (downsampled[0] * y_scale))

        for i, amplitude in enumerate(downsampled):
            point_x = x + (i * x_step)
            point_y = y_center - (amplitude * y_scale)
            path_mirror.lineTo(point_x, point_y)

        c.drawPath(path_mirror, stroke=1, fill=0)

        return True

    except Exception as e:
        logger.debug(f"Could not generate vector waveform: {e}")
        return False


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

            # Draw waveform - try vector first, fallback to PNG
            waveform_x = col_pos + 70 * mm
            waveform_y = row_y - 0.5 * mm
            waveform_width = 18 * mm
            waveform_height = 3 * mm

            # Try to find audio file for vector waveform
            audio_file = None
            for ext in [".opus", ".flac", ".mp3", ".m4a", ".wav"]:
                audio_path = Path(release_folder) / f"{position}{ext}"
                if audio_path.exists():
                    audio_file = audio_path
                    break

            # Try vector waveform first (crisp, no pixelation)
            if audio_file and draw_vector_waveform(
                c, waveform_x, waveform_y, waveform_width, waveform_height, audio_file
            ):
                pass  # Successfully drew vector waveform
            else:
                # Fallback to PNG waveform if available
                waveform_path = Path(release_folder) / f"{position}_waveform.png"
                if waveform_path.exists():
                    try:
                        c.drawImage(
                            str(waveform_path),
                            waveform_x,
                            waveform_y,
                            width=waveform_width,
                            height=waveform_height,
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
