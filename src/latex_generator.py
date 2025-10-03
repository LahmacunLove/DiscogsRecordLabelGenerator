#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX Label Generator for Discogs Releases

Creates LaTeX-based labels for vinyl releases with:
- Track table with waveforms, BPM, Key
- Release information
- Optimized sizing with fitbox

@author: ffx
"""

import os
import json
import pandas as pd
from datetime import datetime
from dateutil import parser as date_parser
from logger import logger
from tqdm import tqdm


def detect_script(text):
    """Detect the script/writing system of text"""
    import re

    # Define Unicode ranges for different scripts
    # Order matters - check specific scripts before general CJK
    script_ranges = {
        "arabic": r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]",
        "cyrillic": r"[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]",  # Russian, Bulgarian, Serbian, etc.
        "greek": r"[\u0370-\u03FF\u1F00-\u1FFF]",  # Greek and extended Greek
        "georgian": r"[\u10A0-\u10FF\u2D00-\u2D2F]",  # Georgian
        "hiragana": r"[\u3040-\u309F]",  # Japanese Hiragana
        "katakana": r"[\u30A0-\u30FF\u31F0-\u31FF]",  # Japanese Katakana
        "hangul": r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]",  # Korean
        "cjk": r"[\u4E00-\u9FFF]",  # Chinese/Japanese Kanji (main block only)
    }

    detected_scripts = []
    for script, pattern in script_ranges.items():
        if re.search(pattern, text):
            detected_scripts.append(script)

    return detected_scripts


def wrap_multilingual_text(text):
    """Wrap text with appropriate XeLaTeX language commands for multiple scripts"""
    import re

    # Split text around = signs and handle each part separately
    if "=" in text:
        parts = text.split("=")
        wrapped_parts = []
        for part in parts:
            wrapped_parts.append(process_text_part(part))
        return " = ".join(wrapped_parts)
    else:
        return process_text_part(text)


def process_text_part(text):
    """Process a text part for multilingual content"""
    import re

    scripts = detect_script(text)

    if not scripts:
        return text  # No special scripts detected, return as-is

    # Process each script type
    result = text

    # Arabic (RTL script)
    if "arabic" in scripts:
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\u200C\u200D\s،؟؛]+"
        )

        def replace_arabic(match):
            arabic_text = match.group(0).strip()
            if arabic_text:
                return f"\\textarabic{{{arabic_text}}}"
            return match.group(0)

        result = arabic_pattern.sub(replace_arabic, result)

    # Cyrillic (Russian, etc.)
    if "cyrillic" in scripts:
        cyrillic_pattern = re.compile(
            r"[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\s]+"
        )

        def replace_cyrillic(match):
            cyrillic_text = match.group(0).strip()
            if cyrillic_text:
                return f"\\textrussian{{{cyrillic_text}}}"
            return match.group(0)

        result = cyrillic_pattern.sub(replace_cyrillic, result)

    # Greek
    if "greek" in scripts:
        greek_pattern = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF\s]+")

        def replace_greek(match):
            greek_text = match.group(0).strip()
            if greek_text:
                return f"\\textgreek{{{greek_text}}}"
            return match.group(0)

        result = greek_pattern.sub(replace_greek, result)

    # Georgian
    if "georgian" in scripts:
        georgian_pattern = re.compile(r"[\u10A0-\u10FF\u2D00-\u2D2F\s]+")

        def replace_georgian(match):
            georgian_text = match.group(0).strip()
            if georgian_text:
                return f"\\textgeorgian{{{georgian_text}}}"
            return match.group(0)

        result = georgian_pattern.sub(replace_georgian, result)

    # CJK (Chinese/Japanese Kanji)
    if "cjk" in scripts:
        cjk_pattern = re.compile(
            r"[\u4E00-\u9FFF\u3400-\u4DBF\u20000-\u2A6DF\u2A700-\u2B73F\u2B740-\u2B81F\u2B820-\u2CEAF\s]+"
        )

        def replace_cjk(match):
            cjk_text = match.group(0).strip()
            if cjk_text:
                # Determine if it's more likely Chinese or Japanese context
                # For now, default to Chinese. Could be enhanced with language detection
                return f"\\textchinese{{{cjk_text}}}"
            return match.group(0)

        result = cjk_pattern.sub(replace_cjk, result)

    # Japanese Hiragana
    if "hiragana" in scripts:
        hiragana_pattern = re.compile(r"[\u3040-\u309F\s]+")

        def replace_hiragana(match):
            hiragana_text = match.group(0).strip()
            if hiragana_text:
                return f"\\textjapanese{{{hiragana_text}}}"
            return match.group(0)

        result = hiragana_pattern.sub(replace_hiragana, result)

    # Japanese Katakana
    if "katakana" in scripts:
        katakana_pattern = re.compile(r"[\u30A0-\u30FF\u31F0-\u31FF\s]+")

        def replace_katakana(match):
            katakana_text = match.group(0).strip()
            if katakana_text:
                return f"\\textjapanese{{{katakana_text}}}"
            return match.group(0)

        result = katakana_pattern.sub(replace_katakana, result)

    # Korean Hangul
    if "hangul" in scripts:
        hangul_pattern = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F\s]+")

        def replace_hangul(match):
            hangul_text = match.group(0).strip()
            if hangul_text:
                return f"\\textkorean{{{hangul_text}}}"
            return match.group(0)

        result = hangul_pattern.sub(replace_hangul, result)

    return result


def contains_non_latin_script(text):
    """Check if text contains any non-Latin scripts"""
    scripts = detect_script(text)
    return len(scripts) > 0


def unicode_to_latex(text):
    """Converts Unicode characters for LaTeX compatibility with multilingual support"""
    if pd.isna(text) or text == "":
        return ""

    result = str(text)

    # Remove only truly problematic Unicode characters
    # IMPORTANT: Preserve text shaping characters for various scripts
    invisible_chars = {
        "\u200b": "",  # Zero-width space (U+200B) - safe to remove
        # '\u200c': '',  # Zero-width non-joiner (U+200C) - KEEP for Arabic and other scripts
        # '\u200d': '',  # Zero-width joiner (U+200D) - KEEP for Arabic and other scripts
        "\u2060": "",  # Word joiner (U+2060)
        "\ufeff": "",  # Byte order mark (U+FEFF)
        "\u00ad": "",  # Soft hyphen (U+00AD)
    }

    for char, replacement in invisible_chars.items():
        result = result.replace(char, replacement)

    # Basic replacements for LaTeX BEFORE multilingual processing
    # IMPORTANT: Pay attention to order - backslash FIRST!
    replacements = {
        "\\": "\\textbackslash{}",  # Handle backslash FIRST
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",  # Simple # escaping for tables
        "^": "\\textasciicircum{}",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "<": "\\textless{}",
        ">": "\\textgreater{}",
    }

    for char, replacement in replacements.items():
        result = result.replace(char, replacement)

    # Handle multilingual text with proper XeLaTeX commands
    if contains_non_latin_script(result):
        result = wrap_multilingual_text(result)

    return result


def musical_key_to_camelot(key):
    """Convert musical key to Camelot notation for DJ use"""
    if pd.isna(key) or key == "":
        return ""

    # Convert to string and normalize
    key_str = str(key).strip().upper()

    # Remove problematic Unicode characters
    invisible_chars = {
        "\u200b": "",  # Zero-width space
        "\u2060": "",  # Word joiner
        "\ufeff": "",  # Byte order mark
        "\u00ad": "",  # Soft hyphen
    }

    for char, replacement in invisible_chars.items():
        key_str = key_str.replace(char, replacement)

    # Normalize musical notation
    key_str = (
        key_str.replace("♯", "#").replace("♭", "B").replace("#", "#").replace("b", "B")
    )

    # Camelot wheel mapping
    # Major keys (outer wheel) = A notation
    # Minor keys (inner wheel) = B notation
    camelot_major = {
        "C": "8A",
        "C#": "3A",
        "DB": "3A",
        "D": "10A",
        "D#": "5A",
        "EB": "5A",
        "E": "12A",
        "F": "7A",
        "F#": "2A",
        "GB": "2A",
        "G": "9A",
        "G#": "4A",
        "AB": "4A",
        "A": "11A",
        "A#": "6A",
        "BB": "6A",
        "B": "1A",
    }

    camelot_minor = {
        "C": "5B",
        "C#": "12B",
        "DB": "12B",
        "D": "7B",
        "D#": "2B",
        "EB": "2B",
        "E": "9B",
        "F": "4B",
        "F#": "11B",
        "GB": "11B",
        "G": "6B",
        "G#": "1B",
        "AB": "1B",
        "A": "8B",
        "A#": "3B",
        "BB": "3B",
        "B": "10B",
    }

    # Parse key format (handle various formats)
    import re

    # Pattern for key detection: root note + optional accidental + optional mode
    pattern = r"^([A-G])([#B]?)(?:M|MAJ|MAJOR|MIN|MINOR|m)?$"
    match = re.match(pattern, key_str)

    if not match:
        # If no match, return original key for LaTeX display
        return musical_key_to_latex_fallback(key)

    root = match.group(1)
    accidental = match.group(2) if match.group(2) else ""

    # Determine if minor based on original key string
    is_minor = (
        "m" in str(key).lower() and "maj" not in str(key).lower()
    ) or "minor" in str(key).lower()

    # Create lookup key
    lookup_key = root + accidental

    # Get Camelot notation
    if is_minor:
        camelot = camelot_minor.get(lookup_key, "")
    else:
        camelot = camelot_major.get(lookup_key, "")

    if camelot:
        return camelot
    else:
        # Fallback to original LaTeX formatting if no Camelot match
        return musical_key_to_latex_fallback(key)


def musical_key_to_latex_fallback(key):
    """Fallback function for non-Camelot musical key LaTeX formatting"""
    if pd.isna(key) or key == "":
        return ""

    result = str(key).strip()

    # Handle musical notation for LaTeX
    import re

    # Treat "b" as flat only when it follows a tone letter
    pattern = r"([A-Ga-g])b(?!m)"
    result = re.sub(pattern, r"\1$\\flat$", result)

    # Musical symbol replacements
    musical_replacements = {
        "♯": "$\\sharp$",
        "♭": "$\\flat$",
        "♮": "$\\natural$",
        "#": "$\\sharp$",
    }

    # Now the direct replacements
    for original, replacement in musical_replacements.items():
        result = result.replace(original, replacement)

    # Only the most necessary LaTeX escapes for keys (no backslash handling)
    final_replacements = {
        "&": "\\&",
        "%": "\\%",
        "^": "\\textasciicircum{}",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
    }

    for char, replacement in final_replacements.items():
        result = result.replace(char, replacement)

    return result


def inplace_change(filename, old_string, new_string):
    """Replaces text in a file"""
    with open(filename, "r", encoding="utf-8") as f:
        s = f.read()

    if old_string not in s:
        logger.warning(f'String "{old_string}" not found in {filename}')
        return

    with open(filename, "w", encoding="utf-8") as f:
        s = s.replace(old_string, new_string)
        f.write(s)


def create_latex_label_file(release_folder, metadata):
    """Creates a LaTeX label file for a release (original design)"""

    label_file = os.path.join(release_folder, "label.tex")

    # Always overwrite - no existence check
    # if os.path.exists(label_file):
    #     logger.info(f"LaTeX label already exists: {os.path.basename(label_file)}")
    #     return True

    return _create_label_original(release_folder, metadata, label_file)


def _create_label_original(release_folder, metadata, label_file):
    """
    New unified label design with:
    - Header: Cover image (left, 2 rows), Artist name, Album title (bold), QR code (top-right)
    - Table: 10 rows max with columns: Index, Track Name, BPM, Key, Waveform
    - Footer: Label, Catalog, Year, Genre, Release ID
    """

    try:
        logger.process(f"Creating label for release {metadata.get('id', 'unknown')}")

        # Get cover image path
        cover_path = os.path.join(release_folder, "cover.jpg")
        if not os.path.exists(cover_path):
            cover_path = os.path.join(release_folder, "cover.png")

        cover_latex = ""
        if os.path.exists(cover_path):
            cover_abs_path = os.path.abspath(cover_path).replace("\\", "/")
            # Cover image: 1.2cm width, positioned in header
            cover_latex = f"\\includegraphics[width=1.2cm]{{{cover_abs_path}}}"

        # Prepare artist and title
        artists = metadata.get("artist", [])
        if isinstance(artists, list):
            unique_artists = []
            for artist in artists:
                if artist not in unique_artists:
                    unique_artists.append(artist)
            artist_str = ", ".join(unique_artists)
        else:
            artist_str = str(artists)

        title = metadata.get("title", "")

        # Truncate artist and title to fit
        artist_truncated = (
            (artist_str[:45] + "...") if len(artist_str) > 45 else artist_str
        )
        title_truncated = (title[:45] + "...") if len(title) > 45 else title

        # Prepare footer metadata
        labels = metadata.get("label", [])
        if isinstance(labels, list):
            label_str = ", ".join(labels)
        else:
            label_str = str(labels)

        catalog_numbers = metadata.get("catalog_numbers", [])
        if isinstance(catalog_numbers, list):
            catalog_str = ", ".join(catalog_numbers)
        else:
            catalog_str = str(catalog_numbers) if catalog_numbers else ""

        genres = metadata.get("genres", [])
        if isinstance(genres, list):
            genre_str = ", ".join(genres[:2])  # Max 2 genres
        else:
            genre_str = str(genres) if genres else ""

        year = str(metadata.get("year", ""))
        release_id = str(metadata.get("id", ""))

        # Build footer with truncation
        footer_parts = []
        if label_str:
            footer_parts.append(unicode_to_latex(label_str[:30]))
        if catalog_str:
            footer_parts.append(unicode_to_latex(catalog_str[:20]))
        if year:
            footer_parts.append(year)
        if genre_str:
            footer_parts.append(unicode_to_latex(genre_str[:30]))
        footer_parts.append(f"ID: {release_id}")
        footer_text = ", ".join(footer_parts)

        # Process tracks - split into chunks of 10
        tracklist = metadata.get("tracklist", [])
        track_chunks = []

        for i in range(0, len(tracklist), 10):
            chunk = tracklist[i : i + 10]
            track_chunks.append(chunk)

        # If no tracks, create at least one label
        if not track_chunks:
            track_chunks = [[]]

        # Generate labels (one per chunk)
        labels_created = []

        for chunk_idx, track_chunk in enumerate(track_chunks):
            # Build track table
            tracks_data = []

            for track in track_chunk:
                track_pos = track.get("position", "")
                track_title = track.get("title", "")

                # Truncate track title to prevent overflow
                track_title_truncated = (
                    (track_title[:35] + "...") if len(track_title) > 35 else track_title
                )

                # Search for analysis data
                track_base = os.path.join(release_folder, track_pos)

                # Load BPM and Key
                bpm, key = "", ""
                json_file = f"{track_base}.json"
                if os.path.exists(json_file):
                    try:
                        with open(json_file, "r") as f:
                            analysis_data = json.load(f)

                        # BPM from rhythm section
                        bpm_value = analysis_data.get("rhythm", {}).get("bpm", 0)
                        if bpm_value and bpm_value > 0:
                            bpm = str(round(bpm_value))

                        # Key from tonal section
                        tonal_data = analysis_data.get("tonal", {})
                        key_temperley = tonal_data.get("key_temperley", {})

                        if key_temperley and isinstance(key_temperley, dict):
                            key_name = key_temperley.get("key", "")
                            key_scale = key_temperley.get("scale", "")
                            if key_name:
                                if "major" in key_scale.lower():
                                    key = key_name.upper()
                                elif "minor" in key_scale.lower():
                                    key = key_name.lower() + "m"
                                else:
                                    key = key_name
                        elif tonal_data.get("key_key"):
                            key = tonal_data.get("key_key")

                    except Exception as e:
                        logger.debug(
                            f"Error parsing analysis data for {track_pos}: {e}"
                        )

                # Waveform path
                waveform_path = f"{track_base}_waveform.png"
                waveform_latex = ""
                if os.path.exists(waveform_path):
                    waveform_abs = os.path.abspath(waveform_path).replace("\\", "/")
                    waveform_latex = (
                        f"\\includegraphics[width=1.8cm,height=0.3cm]{{{waveform_abs}}}"
                    )

                tracks_data.append(
                    {
                        "pos": unicode_to_latex(track_pos),
                        "title": unicode_to_latex(track_title_truncated),
                        "bpm": bpm,
                        "key": musical_key_to_camelot(key) if key else "",
                        "waveform": waveform_latex,
                    }
                )

            # Pad to exactly 10 rows
            while len(tracks_data) < 10:
                tracks_data.append(
                    {
                        "pos": "",
                        "title": "",
                        "bpm": "",
                        "key": "",
                        "waveform": "",
                    }
                )

            # Create DataFrame
            track_df = pd.DataFrame(tracks_data)

            # Column format: tight spacing for Avery L4744REV-65 (96mm width)
            # Index | Title (flexible) | BPM | Key | Waveform
            column_format = "@{}l@{\\hspace{2pt}}X@{\\hspace{2pt}}r@{\\hspace{2pt}}c@{\\hspace{2pt}}c@{}"

            latex_table = track_df.to_latex(
                index=False,
                header=False,
                escape=False,
                column_format=column_format,
            )

            # Remove horizontal lines
            for rule in ["\\toprule", "\\midrule", "\\bottomrule", "\\hline"]:
                latex_table = latex_table.replace(rule + "\n", "")
                latex_table = latex_table.replace(rule, "")

            # Build label content with header layout
            # Header: cover (left) + artist/title (middle) + QR placeholder (handled in combine)
            latex_content = f"""\\begin{{minipage}}[t][5.08cm][t]{{9.6cm}}
\\vspace{{0pt}}

% Header with cover image and text
\\noindent\\begin{{minipage}}[t]{{1.3cm}}
{cover_latex if cover_latex else ""}
\\end{{minipage}}%
\\hfill%
\\begin{{minipage}}[t]{{7.0cm}}
\\raggedright
\\small{{{unicode_to_latex(artist_truncated)}}}\\\\
\\textbf{{\\small{{{unicode_to_latex(title_truncated)}}}}}
\\end{{minipage}}

\\vspace{{0.3cm}}

% Track table (10 rows fixed)
{{\\scriptsize
{latex_table}
}}

\\vspace{{0.1cm}}

% Footer
\\noindent{{\\tiny{{{footer_text}}}}}

\\end{{minipage}}"""

            # Determine label filename
            if len(track_chunks) > 1:
                chunk_label_file = label_file.replace(
                    ".tex", f"_part{chunk_idx + 1}.tex"
                )
            else:
                chunk_label_file = label_file

            # Write LaTeX file
            with open(chunk_label_file, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Convert tabular to tabularx for flexible columns
            inplace_change(
                chunk_label_file, "\\begin{tabular}", "\\begin{tabularx}{9.2cm}"
            )
            inplace_change(chunk_label_file, "\\end{tabular}", "\\end{tabularx}")

            labels_created.append(os.path.basename(chunk_label_file))

        if len(labels_created) > 1:
            logger.success(
                f"Created {len(labels_created)} label files: {', '.join(labels_created)}"
            )
        else:
            logger.success(f"Label created: {labels_created[0]}")

        return True

    except Exception as e:
        logger.error(f"Error creating label: {e}")
        import traceback

        logger.debug(traceback.format_exc())
        return False


def combine_latex_labels(
    library_path, output_dir, max_labels=None, specific_release=None, since_date=None
):
    """
    Combines all labels into a printable LaTeX document
    Based on the original combineLatex function from Git history

    Args:
        library_path: Path to Discogs library directory
        output_dir: Output directory for final LaTeX document
        max_labels: Maximum number of labels (None = all)
        specific_release: Release ID for a specific label (None = all)
        since_date: Date from which labels should be created (YYYY-MM-DD or ISO format)
    """

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find release folders with labels
    if specific_release:
        # Process specific release - search for folder starting with the ID
        logger.info(f"Looking for release with ID: {specific_release}")

        # Find folder starting with the release ID
        matching_dirs = []
        for item in os.listdir(library_path):
            if item.startswith(f"{specific_release}_"):
                matching_dirs.append(item)

        if not matching_dirs:
            logger.error(f"No release directory found for ID: {specific_release}")
            return False

        if len(matching_dirs) > 1:
            logger.warning(
                f"Multiple directories found for ID {specific_release}: {matching_dirs}"
            )
            logger.info(f"Using first match: {matching_dirs[0]}")

        release_folder = matching_dirs[0]
        release_path = os.path.join(library_path, release_folder)
        label_file = os.path.join(release_path, "label.tex")

        # Find all label files (handle multi-part labels)
        label_files = []
        if os.path.exists(label_file):
            label_files.append("label.tex")

        # Check for multi-part labels (label_part1.tex, label_part2.tex, etc.)
        for item in os.listdir(release_path):
            if item.startswith("label_part") and item.endswith(".tex"):
                label_files.append(item)

        if not label_files:
            logger.warning(f"No LaTeX label found for release: {release_folder}")
            logger.info("Creating LaTeX label first...")
            # Load metadata for label creation
            metadata_file = os.path.join(release_path, "metadata.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    if not create_latex_label_file(release_path, metadata):
                        logger.error("Failed to create LaTeX label")
                        return False
                    # Re-check for created labels
                    label_files = []
                    if os.path.exists(label_file):
                        label_files.append("label.tex")
                    for item in os.listdir(release_path):
                        if item.startswith("label_part") and item.endswith(".tex"):
                            label_files.append(item)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.error(f"Error loading metadata for {release_folder}: {e}")
                    return False
            else:
                logger.error(f"No metadata.json found for {release_folder}")
                return False

        release_dirs = [(release_folder, label_file) for label_file in label_files]
    else:
        # Scan all releases
        logger.info("Scanning for releases with LaTeX labels...")
        all_items = os.listdir(library_path)
        release_dirs = []

        # Parse since_date if provided
        since_datetime = None
        if since_date:
            try:
                # Try different date formats
                if "T" in since_date or "+" in since_date or "Z" in since_date:
                    # ISO format
                    since_datetime = date_parser.parse(since_date)
                else:
                    # Simple YYYY-MM-DD format
                    since_datetime = datetime.strptime(since_date, "%Y-%m-%d")
                logger.info(f"Filtering releases added since: {since_datetime}")
            except ValueError as e:
                logger.error(
                    f"Invalid date format: {since_date}. Use YYYY-MM-DD or ISO format."
                )
                return False

        for item in tqdm(all_items, desc="Scanning releases", unit="folder"):
            item_path = os.path.join(library_path, item)
            if os.path.isdir(item_path):
                # Find all label files for this release
                label_files = []
                main_label = os.path.join(item_path, "label.tex")
                if os.path.exists(main_label):
                    label_files.append("label.tex")

                # Check for multi-part labels
                for label_item in os.listdir(item_path):
                    if label_item.startswith("label_part") and label_item.endswith(
                        ".tex"
                    ):
                        label_files.append(label_item)

                if label_files:
                    # Timestamp filtering if since_date provided
                    if since_datetime:
                        metadata_file = os.path.join(item_path, "metadata.json")
                        if os.path.exists(metadata_file):
                            try:
                                with open(metadata_file, "r", encoding="utf-8") as f:
                                    metadata = json.load(f)
                                    if "timestamp" in metadata:
                                        release_datetime = date_parser.parse(
                                            metadata["timestamp"]
                                        )
                                        # Remove timezone info for comparison if necessary
                                        if (
                                            release_datetime.tzinfo is not None
                                            and since_datetime.tzinfo is None
                                        ):
                                            release_datetime = release_datetime.replace(
                                                tzinfo=None
                                            )
                                        elif (
                                            release_datetime.tzinfo is None
                                            and since_datetime.tzinfo is not None
                                        ):
                                            since_datetime = since_datetime.replace(
                                                tzinfo=None
                                            )
                                        if release_datetime >= since_datetime:
                                            for lf in label_files:
                                                release_dirs.append((item, lf))
                                    else:
                                        # If no timestamp, use directory modification time
                                        dir_mtime = datetime.fromtimestamp(
                                            os.path.getmtime(item_path)
                                        )
                                        if dir_mtime >= since_datetime:
                                            for lf in label_files:
                                                release_dirs.append((item, lf))
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.debug(f"Error reading timestamp for {item}: {e}")
                                # On errors, if no timestamp available, use directory time
                                dir_mtime = datetime.fromtimestamp(
                                    os.path.getmtime(item_path)
                                )
                                if dir_mtime >= since_datetime:
                                    for lf in label_files:
                                        release_dirs.append((item, lf))
                        else:
                            # If no metadata.json, use directory time
                            dir_mtime = datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            )
                            if dir_mtime >= since_datetime:
                                for lf in label_files:
                                    release_dirs.append((item, lf))
                    else:
                        # No time filtering
                        for lf in label_files:
                            release_dirs.append((item, lf))

    if not release_dirs:
        logger.warning("No releases with LaTeX labels found")
        return False

    # Sort alphabetically for consistent order
    release_dirs.sort()

    # Limit number if desired
    if max_labels:
        release_dirs = release_dirs[:max_labels]
        logger.info(f"Limited to first {max_labels} releases")

    logger.process(f"Combining {len(release_dirs)} LaTeX labels for printing...")

    # Configuration for Avery Zweckform L4744REV-65 labels
    # 96mm x 50.8mm on A4 paper
    labels_per_page = 10  # 2 columns x 5 rows
    pages_needed = (len(release_dirs) + labels_per_page - 1) // labels_per_page

    # Improved filenames
    if specific_release:
        base_name = f"vinyl_label_{release_dirs[0][0]}"
    elif since_date:
        # Format date for filename
        date_str = since_date.replace("-", "").replace(":", "").replace("T", "_")[:8]
        base_name = f"vinyl_labels_since_{date_str}_{len(release_dirs)}_releases"
    else:
        base_name = f"vinyl_labels_{len(release_dirs)}_releases"
    output_file = os.path.join(output_dir, f"{base_name}.tex")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Read LaTeX template preamble
            template_path = os.path.join(
                os.path.dirname(__file__), "templates", "xelatexTemplate.tex"
            )
            with open(template_path, "r", encoding="utf-8") as template:
                f.write(template.read())

            release_idx = 0

            # Create pages (optimized original algorithm) with progress bar
            with tqdm(
                total=len(release_dirs), desc="Creating labels", unit="label"
            ) as pbar:
                for page in range(pages_needed):
                    if release_idx >= len(release_dirs):
                        break

                    f.write("\\begin{tikzpicture}[thick,font=\\Large]\n")

                    # 5 rows x 2 columns = 10 labels per page (Avery L4744REV-65)
                    for row in range(5):
                        if release_idx >= len(release_dirs):
                            break
                        for col in [0, 1]:
                            release_num = (col + 1) + (row * 2) + (page * 10)
                            if release_num > len(release_dirs):
                                break

                            release_dir, label_filename = release_dirs[release_idx]

                            # Calculate position for Avery L4744REV-65
                            # Label: 96mm (3.78") width, gap: ~4mm (0.157")
                            x_pos = 3.937 * col  # 3.78" label + 0.157" gap
                            y_pos = row * -2  # 50.8mm = 2" per row

                            # Label frame with rounded corners for Avery L4744REV-65
                            f.write(
                                f"\t\\draw[rounded corners=0.5cm] ({x_pos} in, {y_pos} in) rectangle +(3.78in,2in);\n"
                            )

                            # QR code position (prioritize fancy QR, fallback to plain QR)
                            qr_fancy_file = os.path.join(
                                library_path, release_dir, "qrcode_fancy.png"
                            )
                            qr_plain_file = os.path.join(
                                library_path, release_dir, "qrcode.png"
                            )

                            qr_file = None
                            if os.path.exists(qr_fancy_file):
                                qr_file = qr_fancy_file
                            elif os.path.exists(qr_plain_file):
                                qr_file = qr_plain_file

                            if qr_file:
                                # Position QR code in top-right corner
                                qr_x = x_pos + 3.15
                                qr_y = y_pos - 0.25 + 1.975
                                # Absolute path to QR code file
                                qr_path = os.path.abspath(qr_file).replace("\\", "/")
                                f.write(
                                    f"\\node[above right,inner sep=0] at ({qr_x} in, {qr_y} in){{"
                                )
                                f.write(
                                    f"\\includegraphics[width=1.2cm]{{{qr_path}}}}};\n"
                                )

                            # Include label content with adjusted positioning for Avery L4744REV-65
                            content_x = x_pos + 0.105
                            content_y = y_pos + 0.975
                            # Absolute path to label file
                            label_path = os.path.abspath(
                                os.path.join(library_path, release_dir, label_filename)
                            ).replace("\\", "/")
                            f.write(
                                f"\t\\node[right,align=left] at ({content_x} in, {content_y} in){{\n"
                            )
                            f.write(f"\t\t\\input{{{label_path}}}\n")
                            f.write("\t};\n")

                            release_idx += 1
                            pbar.update(
                                1
                            )  # Progress bar update for each processed label

                    f.write("\\end{tikzpicture}\n")

                    # New page (original style)
                    if page < pages_needed - 1:
                        f.write("\\clearpage\n")

            f.write("\\end{document}\n")

        logger.success(f"Master LaTeX document created: {output_file}")
        logger.info(
            f"📄 {pages_needed} pages with {len(release_dirs)} labels ready for printing"
        )

        # Compile PDF if pdflatex available
        if _compile_pdf(output_file, output_dir):
            logger.success("PDF successfully compiled!")

        return True

    except Exception as e:
        logger.error(f"Error combining LaTeX labels: {e}")
        return False


def _compile_pdf(tex_file, output_dir):
    """Compiles LaTeX to PDF using XeLaTeX for Unicode support"""
    import subprocess
    import shutil

    xelatex_path = shutil.which("xelatex")
    if not xelatex_path:
        logger.info("xelatex not found - LaTeX file created but not compiled")
        return False

    try:
        logger.process("Compiling LaTeX to PDF with XeLaTeX...")
        logger.info("This may take several minutes for large collections...")

        # Change to output directory for relative paths
        original_cwd = os.getcwd()
        os.chdir(output_dir)

        # Extract base filename
        tex_basename = os.path.splitext(os.path.basename(tex_file))[0]

        # Compile PDF (2x for references)
        for run in range(2):
            logger.info(f"XeLaTeX compilation pass {run + 1}/2...")
            result = subprocess.run(
                [
                    "xelatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    f"{tex_basename}.tex",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"xelatex error: {result.stderr}")
                return False
            logger.info(f"Pass {run + 1}/2 completed")

        # Cleanup: delete .aux, .log files
        for ext in [".aux", ".log"]:
            cleanup_file = f"{tex_basename}{ext}"
            if os.path.exists(cleanup_file):
                os.remove(cleanup_file)

        os.chdir(original_cwd)
        return True

    except Exception as e:
        logger.error(f"PDF compilation failed: {e}")
        if "original_cwd" in locals():
            os.chdir(original_cwd)
        return False
