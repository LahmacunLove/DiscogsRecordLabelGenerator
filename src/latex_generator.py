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
    """Original label design - based on the original createLatexLabelFile method"""

    try:
        logger.process(
            f"Creating original LaTeX label for release {metadata.get('id', 'unknown')}"
        )

        # Load YouTube matches for duration fallback
        yt_matches_file = os.path.join(release_folder, "yt_matches.json")
        youtube_durations = {}
        if os.path.exists(yt_matches_file):
            try:
                with open(yt_matches_file, "r", encoding="utf-8") as f:
                    yt_matches = json.load(f)
                # Create mapping from track position to YouTube duration
                for match in yt_matches:
                    track_pos = match.get("track_position")
                    youtube_match = match.get("youtube_match")
                    if track_pos and youtube_match and youtube_match.get("length"):
                        # Convert seconds to MM:SS format
                        duration_seconds = youtube_match["length"]
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        youtube_durations[track_pos] = f"{minutes}:{seconds:02d}"
            except Exception as e:
                logger.debug(
                    f"Error loading YouTube matches for duration fallback: {e}"
                )

        # Create DataFrame for tracks (as in original)
        tracks_data = []
        for track in metadata.get("tracklist", []):
            track_pos = track.get("position", "")
            track_title = track.get("title", "")
            track_artist = track.get("artist", "")
            track_duration = track.get("duration", "")

            # Use YouTube duration as fallback if Discogs duration is missing
            if not track_duration or track_duration.strip() == "":
                if track_pos in youtube_durations:
                    track_duration = youtube_durations[track_pos]

            # Search for analysis data
            track_base = os.path.join(release_folder, track_pos)

            # Load BPM and Key from JSON (if available)
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

                    # Key from tonal section (check various possibilities)
                    tonal_data = analysis_data.get("tonal", {})
                    key_key = tonal_data.get("key_key", "")
                    key_scale = tonal_data.get("key_scale", "")
                    key_temperley = tonal_data.get("key_temperley", {})

                    # Check different key sources
                    if key_temperley and isinstance(key_temperley, dict):
                        key_name = key_temperley.get("key", "")
                        key_scale = key_temperley.get("scale", "")
                        if key_name:
                            # Combine Key + Scale (e.g. "C major" → "C")
                            if "major" in key_scale.lower():
                                key = key_name.upper()
                            elif "minor" in key_scale.lower():
                                key = key_name.lower() + "m"
                            else:
                                key = key_name
                    elif key_key:
                        key = key_key

                except Exception as e:
                    logger.debug(f"Error parsing analysis data for {track_pos}: {e}")
                    pass

            # Waveform path (absolute path as in original)
            waveform_path = f"{track_base}_waveform.png"
            waveform_latex = ""
            if os.path.exists(waveform_path):
                # Absolute path for LaTeX as in original
                waveform_latex = (
                    f"\\includegraphics[width=2cm]{{{os.path.abspath(waveform_path)}}}"
                )

            tracks_data.append(
                {
                    "pos": track_pos,
                    "title": track_title,
                    "artist": track_artist,
                    "duration": track_duration,
                    "bpm": bpm,
                    "key": key,
                    "waveform": waveform_latex,
                }
            )

        # Create DataFrame (pandas-based as in original)
        track_df = pd.DataFrame(tracks_data)

        # Replace NaN values with empty strings (original behavior)
        track_df = track_df.fillna("")

        # Unicode conversion for LaTeX (applymap as in original)
        for col in ["pos", "title", "artist", "duration", "bpm"]:
            if col in track_df.columns:
                track_df[col] = track_df[col].apply(unicode_to_latex)

        # Special handling for Key column - convert to Camelot notation
        if "key" in track_df.columns:
            track_df["key"] = track_df["key"].apply(musical_key_to_camelot)

        # Check if any tracks have durations (excluding empty strings)
        has_durations = track_df["duration"].notna() & (track_df["duration"] != "")
        has_any_duration = has_durations.any()

        # Original Various Artists handling
        unique_artists = track_df["artist"].unique()
        if len(unique_artists) == 1:
            # Only one artist - hide artist column (original logic)
            if has_any_duration:
                # Include duration column at the end
                columns_to_show = ["pos", "title", "bpm", "key", "waveform", "duration"]
                column_format = "@{}l@{\\hspace{3pt}}X@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{2pt}}c@{\\hspace{3pt}}l@{}"
            else:
                # Exclude duration column
                columns_to_show = ["pos", "title", "bpm", "key", "waveform"]
                column_format = "@{}l@{\\hspace{3pt}}X@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{2pt}}c@{}"
        else:
            # Multiple artists - combine title and artist (original behavior)
            track_df["title"] = track_df["title"] + " / " + track_df["artist"]
            if has_any_duration:
                # Include duration column at the end
                columns_to_show = ["pos", "title", "bpm", "key", "waveform", "duration"]
                column_format = "@{}l@{\\hspace{3pt}}X@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{2pt}}c@{\\hspace{3pt}}l@{}"
            else:
                # Exclude duration column
                columns_to_show = ["pos", "title", "bpm", "key", "waveform"]
                column_format = "@{}l@{\\hspace{3pt}}X@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{2pt}}c@{}"

        # Filter DataFrame
        track_df_display = track_df[columns_to_show]

        # LaTeX table with dynamic column format
        latex_table = track_df_display.to_latex(
            index=False,
            header=False,  # Remove table header
            escape=False,  # Important: Let LaTeX commands through
            column_format=column_format,
        )

        # Remove all horizontal lines manually
        latex_table = latex_table.replace("\\toprule\n", "")
        latex_table = latex_table.replace("\\midrule\n", "")
        latex_table = latex_table.replace("\\bottomrule\n", "")
        latex_table = latex_table.replace("\\hline\n", "")
        latex_table = latex_table.replace("\\toprule", "")
        latex_table = latex_table.replace("\\midrule", "")
        latex_table = latex_table.replace("\\bottomrule", "")
        latex_table = latex_table.replace("\\hline", "")

        # Prepare release information
        artists = metadata.get("artist", [])
        if isinstance(artists, list):
            # Remove duplicates while preserving order
            unique_artists = []
            for artist in artists:
                if artist not in unique_artists:
                    unique_artists.append(artist)
            artist_str = ", ".join(unique_artists)
        else:
            artist_str = str(artists)

        title = metadata.get("title", "")
        labels = metadata.get("label", [])
        if isinstance(labels, list):
            label_str = ", ".join(labels)
        else:
            label_str = str(labels)

        # Catalog numbers
        catalog_numbers = metadata.get("catalog_numbers", [])
        if isinstance(catalog_numbers, list):
            catalog_str = ", ".join(catalog_numbers)
        else:
            catalog_str = str(catalog_numbers) if catalog_numbers else ""

        # Genres
        genres = metadata.get("genres", [])
        if isinstance(genres, list):
            # Limit to first 2-3 genres to avoid overly long footline
            genre_str = ", ".join(genres[:3])
        else:
            genre_str = str(genres) if genres else ""

        # Year and release ID
        year = str(metadata.get("year", ""))
        release_id = str(metadata.get("id", ""))

        # Minipage method with proper adjustbox structure
        # Adjusted for Avery L4744REV-65: 96mm x 50.8mm (3.78" x 2" = 9.6cm x 5.08cm)
        latex_content = f"""\\begin{{minipage}}[t][5.08cm][t]{{9.6cm}}

\\begin{{adjustbox}}{{max width=9cm}}
  \\textbf{{{unicode_to_latex(artist_str)}}}
\\end{{adjustbox}} \\\\

\\begin{{adjustbox}}{{max width=9cm}}
  {unicode_to_latex(title)}
\\end{{adjustbox}}

\\vspace{{.4cm}}

\\vfill
\\begin{{adjustbox}}{{max height=1.4cm}}
\\scriptsize
{latex_table}
\\end{{adjustbox}}
\\vfill

\\raggedright
\\tiny{{\\textbf{{{unicode_to_latex(label_str)}}}{", " + unicode_to_latex(catalog_str) if catalog_str else ""}, {year}{", " + unicode_to_latex(genre_str) if genre_str else ""}, Release ID: {release_id}}}
\\end{{minipage}}"""

        # \adjustbox{width=5cm, height=3cm}{\includegraphics{bild.png}}

        # Write LaTeX file
        with open(label_file, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # Adapted tabularx conversion for minipage (3.78in = 96mm for Avery L4744REV-65)
        inplace_change(label_file, "\\begin{tabular}", "\\begin{tabularx}{3.78in}")
        inplace_change(label_file, "\\end{tabular}", "\\end{tabularx}")

        logger.success(f"Original LaTeX label created: {os.path.basename(label_file)}")
        return True

    except Exception as e:
        logger.error(f"Error creating original LaTeX label: {e}")
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

        if not os.path.exists(label_file):
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
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.error(f"Error loading metadata for {release_folder}: {e}")
                    return False
            else:
                logger.error(f"No metadata.json found for {release_folder}")
                return False

        release_dirs = [(release_folder, "label.tex")]
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
                label_file = os.path.join(item_path, "label.tex")
                if os.path.exists(label_file):
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
                                            release_dirs.append((item, "label.tex"))
                                    else:
                                        # If no timestamp, use directory modification time
                                        dir_mtime = datetime.fromtimestamp(
                                            os.path.getmtime(item_path)
                                        )
                                        if dir_mtime >= since_datetime:
                                            release_dirs.append((item, "label.tex"))
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.debug(f"Error reading timestamp for {item}: {e}")
                                # On errors, if no timestamp available, use directory time
                                dir_mtime = datetime.fromtimestamp(
                                    os.path.getmtime(item_path)
                                )
                                if dir_mtime >= since_datetime:
                                    release_dirs.append((item, "label.tex"))
                        else:
                            # If no metadata.json, use directory time
                            dir_mtime = datetime.fromtimestamp(
                                os.path.getmtime(item_path)
                            )
                            if dir_mtime >= since_datetime:
                                release_dirs.append((item, "label.tex"))
                    else:
                        # No time filtering
                        release_dirs.append((item, "label.tex"))

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
                                qr_x = x_pos + 3.25
                                qr_y = y_pos - 0.36 + 1.975
                                # Absolute path to QR code file
                                qr_path = os.path.abspath(qr_file).replace("\\", "/")
                                f.write(
                                    f"\\node[right,align=left] at ({qr_x} in, {qr_y} in){{"
                                )
                                f.write(
                                    f"\\includegraphics[width=1.5cm]{{{qr_path}}}}};\n"
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
