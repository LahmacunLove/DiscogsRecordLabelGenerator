#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for DiscogsRecordLabelGenerator

@author: ffx
"""

import re

try:
    from pathvalidate import sanitize_filename as _pathvalidate_sanitize

    PATHVALIDATE_AVAILABLE = True
except ImportError:
    PATHVALIDATE_AVAILABLE = False


def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing problematic characters.
    Uses pathvalidate library if available, falls back to manual approach.

    Args:
        filename (str): The original filename/foldername

    Returns:
        str: Sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed"

    if PATHVALIDATE_AVAILABLE:
        # Use pathvalidate library - handles all edge cases automatically
        try:
            # pathvalidate handles filesystem restrictions and Unicode issues
            sanitized = _pathvalidate_sanitize(
                str(filename),
                replacement_text="_",  # Replace invalid chars with underscore
                platform="auto",  # Auto-detect platform restrictions
            )

            # Additional cleanup for filesystem and path consistency
            # pathvalidate handles filesystem safety, but we need additional cleanup
            # These characters can cause issues in file paths
            # Also include colon for consistency (pathvalidate allows it on Linux but we want it replaced)
            problematic = ["#", "%", "&", "$", "^", "{", "}", "~", "°", ":"]
            for char in problematic:
                if char in sanitized:
                    sanitized = sanitized.replace(char, "_")

            # Handle different types of apostrophes and quotes
            apostrophe_variants = [
                "'",  # U+2019 - Right single quotation mark (curly apostrophe)
                "'",  # U+2018 - Left single quotation mark
                "ʼ",  # U+02BC - Modifier letter apostrophe
                "'",  # U+0027 - Standard ASCII apostrophe (already handled by pathvalidate)
            ]
            for char in apostrophe_variants:
                if char in sanitized:
                    sanitized = sanitized.replace(char, "_")

            # Clean up multiple underscores
            sanitized = re.sub(r"_+", "_", sanitized)
            # Remove trailing spaces and dots (Windows compatibility) but keep internal spaces
            sanitized = sanitized.rstrip(" .")

            return sanitized if sanitized else "unnamed"

        except Exception:
            # Fall back to manual approach if pathvalidate fails
            pass

    # Fallback manual approach (original implementation)
    sanitized = str(filename)

    # Remove zero-width characters and other invisibles
    invisible_chars = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\u2060",  # Word joiner
        "\ufeff",  # Byte order mark
        "\u00ad",  # Soft hyphen
    ]

    for char in invisible_chars:
        sanitized = sanitized.replace(char, "")

    # Replace problematic characters with underscores (but keep spaces)
    # Include Unicode apostrophe variants in the pattern
    sanitized = re.sub(r'[\\/:*?"<>|\'"' "ʼ#%&$^{}~°†‡§¶]", "_", sanitized)

    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove trailing spaces and dots (Windows compatibility) but keep internal spaces
    sanitized = sanitized.rstrip(" .")
    # Remove leading underscores
    sanitized = sanitized.lstrip("_")

    # Ensure we don't have an empty string
    if not sanitized:
        return "unnamed"

    return sanitized
