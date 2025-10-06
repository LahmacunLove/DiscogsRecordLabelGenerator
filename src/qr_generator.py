#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code Generator for Discogs Releases

Creates QR codes with cover background for Discogs releases
Based on the original createQRCode function with modern improvements

@author: ffx
"""

import os
import shutil
from logger import logger


def generate_qr_code(release_folder, release_id, cover_file=None):
    """
    Generates both simple and artistic QR codes for a Discogs release

    Args:
        release_folder: Path to the release folder
        release_id: Discogs Release ID
        cover_file: Path to cover image (optional, automatically searched)

    Returns:
        bool: True if successful, False on errors
    """

    # Check if segno is available, fallback to qrcode
    try:
        import segno

        return _generate_qr_segno_both(release_folder, release_id, cover_file)
    except ImportError:
        logger.debug("segno not available, trying qrcode library")
        try:
            import qrcode
            from PIL import Image

            return _generate_qr_standard(release_folder, release_id, cover_file)
        except ImportError:
            logger.warning("No QR code library available (segno or qrcode)")
            logger.info("Install with: pip install segno  or  pip install qrcode[pil]")
            return False


def _generate_qr_segno_both(release_folder, release_id, cover_file=None):
    """Segno-based QR code generation - creates both simple and artistic QR codes"""
    import segno

    qr_file = os.path.join(release_folder, "qrcode.png")
    qr_fancy_file = os.path.join(release_folder, "qrcode_fancy.png")

    # Find cover file if not specified
    if not cover_file:
        cover_file = os.path.join(release_folder, "cover.jpg")

    try:
        logger.process(f"Generating QR codes with segno for release {release_id}")

        # Create QR code with Discogs URL
        discogs_url = f"https://discogs.com/release/{release_id}"
        qr_code = segno.make_qr(discogs_url, error="l")

        success = False

        # 1. Create simple QR code (always)
        if not os.path.exists(qr_file):
            logger.debug("Creating simple QR code with segno")
            qr_code.save(qr_file, scale=10, border=2, dark="black", light="white")
            logger.success(f"Simple QR code created: {os.path.basename(qr_file)}")
            success = True
        else:
            logger.debug(f"Simple QR code already exists: {os.path.basename(qr_file)}")
            success = True

        # 2. Create artistic QR code with cover (if possible)
        if (
            not os.path.exists(qr_fancy_file)
            and os.path.exists(cover_file)
            and hasattr(qr_code, "to_artistic")
        ):
            try:
                logger.debug(
                    f"Creating fancy QR code with cover: {os.path.basename(cover_file)}"
                )
                qr_code.to_artistic(
                    background=cover_file, target=qr_fancy_file, scale=10, border=2
                )
                logger.success(
                    f"Fancy QR code with cover created: {os.path.basename(qr_fancy_file)}"
                )
            except Exception as e:
                logger.warning(f"Fancy QR creation failed: {e}")
        elif os.path.exists(qr_fancy_file):
            logger.debug(
                f"Fancy QR code already exists: {os.path.basename(qr_fancy_file)}"
            )
        elif not os.path.exists(cover_file):
            logger.debug("No cover image found - skipping fancy QR code")

        return success

    except Exception as e:
        logger.error(f"Error generating segno QR codes for release {release_id}: {e}")
        return False


def _generate_qr_segno(release_folder, release_id, cover_file=None):
    """Legacy function - kept for compatibility"""
    return _generate_qr_segno_both(release_folder, release_id, cover_file)


def _generate_qr_standard(release_folder, release_id, cover_file=None):
    """Standard qrcode library with PIL for cover integration"""
    import qrcode
    from PIL import Image, ImageDraw

    qr_file = os.path.join(release_folder, "qrcode.png")

    # Check if QR code already exists
    if os.path.exists(qr_file):
        logger.debug(f"QR code already exists: {os.path.basename(qr_file)}")
        return True

    # Find cover file if not specified
    if not cover_file:
        cover_file = os.path.join(release_folder, "cover.jpg")

    try:
        logger.process(
            f"Generating QR code with qrcode library for release {release_id}"
        )

        # Create QR code with Discogs URL
        discogs_url = f"https://discogs.com/release/{release_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(discogs_url)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # If cover is available, integrate it into the QR code
        if os.path.exists(cover_file):
            logger.debug(
                f"Integrating cover as center logo: {os.path.basename(cover_file)}"
            )

            # Load cover
            cover = Image.open(cover_file)

            # Calculate logo size (approximately 1/5 of QR code size)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 5

            # Resize cover to logo
            cover = cover.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Create white border around logo for better readability
            logo_with_border = Image.new(
                "RGB", (logo_size + 20, logo_size + 20), "white"
            )
            logo_with_border.paste(cover, (10, 10))

            # Calculate position for logo (center)
            logo_pos = (
                (qr_width - logo_with_border.width) // 2,
                (qr_height - logo_with_border.height) // 2,
            )

            # Add logo to QR code
            qr_img.paste(logo_with_border, logo_pos)

            logger.success(
                f"QR code with cover logo created: {os.path.basename(qr_file)}"
            )
        else:
            logger.debug("No cover found - creating simple QR code")
            logger.success(f"Simple QR code created: {os.path.basename(qr_file)}")

        # Save QR code
        qr_img.save(qr_file)

        return True

    except Exception as e:
        logger.error(f"Error generating standard QR code for release {release_id}: {e}")
        return False


def generate_qr_code_advanced(release_folder, release_id, metadata=None, tracker=None):
    """
    Advanced QR code generation with fallback between libraries

    Args:
        release_folder: Path to release folder
        release_id: Discogs Release ID
        metadata: Optional - Release metadata for advanced QR codes
        tracker: Optional - Progress tracker for status updates

    Returns:
        bool: True if successful, False on errors
    """

    if tracker:
        tracker.update_step("Generating QR code", 86)

    # Use automatic fallback between segno and qrcode
    result = generate_qr_code(release_folder, release_id)

    if tracker:
        tracker.update_step("QR code complete", 90)

    return result


def check_qr_dependencies():
    """Checks if QR code dependencies are available"""
    try:
        import segno

        logger.info("✅ segno library available for QR code generation")
        return True
    except ImportError:
        logger.warning("❌ segno library not installed")
        logger.info("💡 Install with: pip install segno")
        return False
