#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX Label Generator for Discogs Releases

Erstellt LaTeX-basierte Etiketten für Vinyl-Releases mit:
- Track-Tabelle mit Waveforms, BPM, Key
- Release-Informationen
- Optimierte Größenanpassung mit fitbox

@author: ffx
"""

import os
import json
import pandas as pd
from datetime import datetime
from dateutil import parser as date_parser
from logger import logger
from tqdm import tqdm

def unicode_to_latex(text):
    """Konvertiert Unicode-Zeichen für LaTeX-Kompatibilität"""
    if pd.isna(text) or text == '':
        return ''
    
    result = str(text)
    
    # Entferne problematische Unicode-Zeichen ZUERST
    invisible_chars = {
        '\u200b': '',  # Zero-width space (U+200B)
        '\u200c': '',  # Zero-width non-joiner (U+200C) 
        '\u200d': '',  # Zero-width joiner (U+200D)
        '\u2060': '',  # Word joiner (U+2060)
        '\ufeff': '',  # Byte order mark (U+FEFF)
        '\u00ad': '',  # Soft hyphen (U+00AD)
    }
    
    for char, replacement in invisible_chars.items():
        result = result.replace(char, replacement)
    
    # Basis-Ersetzungen für LaTeX
    # WICHTIG: Reihenfolge beachten - backslash ZUERST!
    replacements = {
        '\\': '\\textbackslash{}',  # Backslash ZUERST behandeln
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',  # Einfaches # escaping für Tabellen
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '<': '\\textless{}',
        '>': '\\textgreater{}',
    }
    
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    
    return result

def musical_key_to_latex(key):
    """Spezialisierte Funktion für musikalische Tonarten in LaTeX"""
    if pd.isna(key) or key == '':
        return ''
    
    # Konvertiere zu String
    result = str(key).strip()
    
    # Entferne problematische Unicode-Zeichen ZUERST
    invisible_chars = {
        '\u200b': '',  # Zero-width space (U+200B)
        '\u200c': '',  # Zero-width non-joiner (U+200C) 
        '\u200d': '',  # Zero-width joiner (U+200D)
        '\u2060': '',  # Word joiner (U+2060)
        '\ufeff': '',  # Byte order mark (U+FEFF)
        '\u00ad': '',  # Soft hyphen (U+00AD)
    }
    
    for char, replacement in invisible_chars.items():
        result = result.replace(char, replacement)
    
    # Musikalische Notation behandeln (ohne andere LaTeX-Escaping)
    import re
    
    # Behandle "b" als flat nur wenn es nach einem Ton-Buchstaben steht
    # aber nicht bei "bm" (b-moll) oder "Bm" (B-moll)
    # Pattern: Tonbuchstabe + b (aber nicht bm)
    pattern = r'([A-Ga-g])b(?!m)'
    result = re.sub(pattern, r'\1$\\flat$', result)
    
    # Direkte musikalische Ersetzungen
    musical_replacements = {
        # Unicode musikalische Symbole
        '♯': '$\\sharp$',      # Unicode sharp
        '♭': '$\\flat$',       # Unicode flat  
        '♮': '$\\natural$',    # Unicode natural
        
        # ASCII sharp (# → ♯)
        '#': '$\\sharp$',
    }
    
    # Jetzt die direkten Ersetzungen
    for original, replacement in musical_replacements.items():
        result = result.replace(original, replacement)
    
    # Nur die notwendigsten LaTeX-Escapes für Tonarten (keine backslash-Behandlung)
    final_replacements = {
        '&': '\\&',
        '%': '\\%',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
    }
    
    for char, replacement in final_replacements.items():
        result = result.replace(char, replacement)
    
    return result

def inplace_change(filename, old_string, new_string):
    """Ersetzt Text in einer Datei"""
    with open(filename, 'r', encoding='utf-8') as f:
        s = f.read()
    
    if old_string not in s:
        logger.warning(f'String "{old_string}" not found in {filename}')
        return
    
    with open(filename, 'w', encoding='utf-8') as f:
        s = s.replace(old_string, new_string)
        f.write(s)

def create_latex_label_file(release_folder, metadata):
    """Erstellt eine LaTeX-Label-Datei für ein Release (Original-Design)"""
    
    label_file = os.path.join(release_folder, 'label.tex')
    
    # Überschreibe immer - keine Existenz-Prüfung
    # if os.path.exists(label_file):
    #     logger.info(f"LaTeX label already exists: {os.path.basename(label_file)}")
    #     return True
    
    return _create_label_original(release_folder, metadata, label_file)


def _create_label_original(release_folder, metadata, label_file):
    """Original Label-Design - basierend auf der ursprünglichen createLatexLabelFile Methode"""
    
    try:
        logger.process(f"Creating original LaTeX label for release {metadata.get('id', 'unknown')}")
        
        # Erstelle DataFrame für Tracks (wie im Original)
        tracks_data = []
        for track in metadata.get('tracklist', []):
            track_pos = track.get('position', '')
            track_title = track.get('title', '')
            track_artist = track.get('artist', '')
            track_duration = track.get('duration', '')
            
            # Suche nach Analyse-Daten
            track_base = os.path.join(release_folder, track_pos)
            
            # BPM und Key aus JSON laden (falls vorhanden)
            bpm, key = '', ''
            json_file = f"{track_base}.json"
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        analysis_data = json.load(f)
                    
                    # BPM aus rhythm-Sektion
                    bpm_value = analysis_data.get('rhythm', {}).get('bpm', 0)
                    if bpm_value and bpm_value > 0:
                        bpm = str(round(bpm_value))
                    
                    # Key aus tonal-Sektion (verschiedene Möglichkeiten prüfen)
                    tonal_data = analysis_data.get('tonal', {})
                    key_key = tonal_data.get('key_key', '')
                    key_scale = tonal_data.get('key_scale', '')
                    key_temperley = tonal_data.get('key_temperley', {})
                    
                    # Prüfe verschiedene Key-Quellen
                    if key_temperley and isinstance(key_temperley, dict):
                        key_name = key_temperley.get('key', '')
                        key_scale = key_temperley.get('scale', '')
                        if key_name:
                            # Kombiniere Key + Scale (z.B. "C major" → "C")
                            if 'major' in key_scale.lower():
                                key = key_name.upper()
                            elif 'minor' in key_scale.lower():
                                key = key_name.lower() + 'm'
                            else:
                                key = key_name
                    elif key_key:
                        key = key_key
                        
                except Exception as e:
                    logger.debug(f"Error parsing analysis data for {track_pos}: {e}")
                    pass
            
            # Waveform-Pfad (absoluter Pfad wie im Original)
            waveform_path = f"{track_base}_waveform.png"
            waveform_latex = ''
            if os.path.exists(waveform_path):
                # Absoluter Pfad für LaTeX wie im Original
                waveform_latex = f'\\includegraphics[width=2cm]{{{os.path.abspath(waveform_path)}}}'
            
            tracks_data.append({
                'pos': track_pos,
                'title': track_title,
                'artist': track_artist,
                'duration': track_duration,
                'bpm': bpm,
                'key': key,
                'waveform': waveform_latex
            })
        
        # DataFrame erstellen (pandas-basiert wie im Original)
        track_df = pd.DataFrame(tracks_data)
        
        # NaN-Werte durch leere Strings ersetzen (Original-Verhalten)
        track_df = track_df.fillna('')
        
        # Unicode-Konvertierung für LaTeX (applymap wie im Original)
        for col in ['pos', 'title', 'artist', 'duration', 'bpm']:
            if col in track_df.columns:
                track_df[col] = track_df[col].apply(unicode_to_latex)
        
        # Spezielle Behandlung für Key-Spalte mit musikalischer Notation
        if 'key' in track_df.columns:
            track_df['key'] = track_df['key'].apply(musical_key_to_latex)
        
        # Original Various Artists Behandlung
        unique_artists = track_df['artist'].unique()
        if len(unique_artists) == 1:
            # Nur ein Artist - verstecke Artist-Spalte (Original-Logik)
            columns_to_show = ['pos', 'title', 'duration', 'bpm', 'key', 'waveform']
        else:
            # Mehrere Artists - kombiniere title und artist (Original-Verhalten)
            track_df['title'] = track_df['title'] + ' / ' + track_df['artist']
            columns_to_show = ['pos', 'title', 'duration', 'bpm', 'key', 'waveform']
        
        # Filtere DataFrame
        track_df_display = track_df[columns_to_show]
        
        # LaTeX-Tabelle mit optimierten Spaltenabständen (sauberer Look)
        latex_table = track_df_display.to_latex(
            index=False,
            header=False,  # Entferne Tabellen-Header
            escape=False,  # Wichtig: Lass LaTeX-Befehle durch
            column_format="@{}l@{\\hspace{3pt}}X@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{3pt}}l@{\\hspace{2pt}}c@{}"  # Flexiblere Abstände für bessere Lesbarkeit
        )
        
        # Entferne alle horizontalen Linien manuell
        latex_table = latex_table.replace('\\toprule\n', '')
        latex_table = latex_table.replace('\\midrule\n', '')
        latex_table = latex_table.replace('\\bottomrule\n', '')
        latex_table = latex_table.replace('\\hline\n', '')
        latex_table = latex_table.replace('\\toprule', '')
        latex_table = latex_table.replace('\\midrule', '')
        latex_table = latex_table.replace('\\bottomrule', '')
        latex_table = latex_table.replace('\\hline', '')
        
        # Release-Informationen vorbereiten
        artists = metadata.get('artist', [])
        if isinstance(artists, list):
            artist_str = ', '.join(artists)
        else:
            artist_str = str(artists)
        
        title = metadata.get('title', '')
        labels = metadata.get('label', [])
        if isinstance(labels, list):
            label_str = ', '.join(labels)
        else:
            label_str = str(labels)
        
        # Jahr und Release ID
        year = str(metadata.get('year', ''))
        release_id = str(metadata.get('id', ''))
        
        # IMPROVED: Separated title/artist with resizebox, table, and footer - with fixed height
        latex_content = f"""\\begin{{minipage}}[t]{{3.5in}}{{2in}}
% Title/Artist section with resizebox for dynamic sizing
\\resizebox{{3.4in}}{{!}}{{%
\\begin{{minipage}}{{3.4in}}
\\textbf{{{unicode_to_latex(artist_str)}}}\\\\[0.1em]
{unicode_to_latex(title)}
\\end{{minipage}}%
}}

\\vspace{{0.4em}}

% Track table section
\\scriptsize
{latex_table}

\\vfill

% Footer section (forced to bottom)
\\raggedright
\\tiny{{\\textbf{{{unicode_to_latex(label_str)}}}, {year}, Release ID: {release_id}}}
\\end{{minipage}}"""
        
        # latex_content = f"""\\begin{{fitbox}}{{9.5cm}}{{4.5cm}}
        # \\textbf{{{unicode_to_latex(artist_str)}}}\\\\[0.3em]
        # {unicode_to_latex(title)}
        # \\hfill
        # \\scriptsize
        # {latex_table}
        # \\hfill
        # \\raggedright
        # \\tiny{{\\textbf{{{unicode_to_latex(label_str)}}}, {year}, Release ID: \\href{{https://www.discogs.com/release/{release_id}}}{{{release_id}}}}}
        # \\end{{fitbox}}"""
        
        # NEW: LaTeX-Content without fitbox - using minipage for fixed size
#         latex_content = f"""\\begin{{minipage}}{{3.5in}}{{2in}}
# \\textbf{{{unicode_to_latex(artist_str)}}}\\ bla \\[0.2em]
# {unicode_to_latex(title)}

# \\vspace{{0.3em}}
# \\scriptsize
# {latex_table}

# \\vfill
# \\raggedright
# \\tiny{{\\textbf{{{unicode_to_latex(label_str)}}}, {year}, Release ID: {release_id}}}
# \\end{{minipage}}"""
        
        # Schreibe LaTeX-Datei
        with open(label_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Angepasste tabularx-Konvertierung für minipage (3.5in = ca. 8.9cm)
        inplace_change(label_file, "\\begin{tabular}", "\\begin{tabularx}{3.4in}")
        inplace_change(label_file, "\\end{tabular}", "\\end{tabularx}")
        
        logger.success(f"Original LaTeX label created: {os.path.basename(label_file)}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating original LaTeX label: {e}")
        return False


def combine_latex_labels(library_path, output_dir, max_labels=None, specific_release=None, since_date=None):
    """
    Kombiniert alle Labels zu einem druckbaren LaTeX-Dokument
    Basierend auf der originalen combineLatex Funktion aus der Git-History
    
    Args:
        library_path: Pfad zum Discogs Library Verzeichnis
        output_dir: Ausgabe-Verzeichnis für das finale LaTeX-Dokument
        max_labels: Maximale Anzahl Labels (None = alle)
        specific_release: Release-ID für ein spezifisches Label (None = alle)
        since_date: Datum ab dem Labels erstellt werden sollen (YYYY-MM-DD oder ISO format)
    """
    
    # Erstelle Output-Verzeichnis falls nicht vorhanden
    os.makedirs(output_dir, exist_ok=True)
    
    # Finde Release-Ordner mit Labels
    if specific_release:
        # Spezifisches Release verarbeiten - suche nach Ordner der mit der ID beginnt
        logger.info(f"Looking for release with ID: {specific_release}")
        
        # Finde Ordner der mit der Release-ID beginnt
        matching_dirs = []
        for item in os.listdir(library_path):
            if item.startswith(f"{specific_release}_"):
                matching_dirs.append(item)
        
        if not matching_dirs:
            logger.error(f"No release directory found for ID: {specific_release}")
            return False
        
        if len(matching_dirs) > 1:
            logger.warning(f"Multiple directories found for ID {specific_release}: {matching_dirs}")
            logger.info(f"Using first match: {matching_dirs[0]}")
        
        release_folder = matching_dirs[0]
        release_path = os.path.join(library_path, release_folder)
        label_file = os.path.join(release_path, 'label.tex')
        
        if not os.path.exists(label_file):
            logger.warning(f"No LaTeX label found for release: {release_folder}")
            logger.info("Creating LaTeX label first...")
            # Lade metadata für Label-Erstellung
            metadata_file = os.path.join(release_path, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
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
        # Alle Releases scannen
        logger.info("Scanning for releases with LaTeX labels...")
        all_items = os.listdir(library_path)
        release_dirs = []
        
        # Parse since_date falls angegeben
        since_datetime = None
        if since_date:
            try:
                # Versuche verschiedene Datumsformate
                if 'T' in since_date or '+' in since_date or 'Z' in since_date:
                    # ISO Format
                    since_datetime = date_parser.parse(since_date)
                else:
                    # Einfaches YYYY-MM-DD Format
                    since_datetime = datetime.strptime(since_date, '%Y-%m-%d')
                logger.info(f"Filtering releases added since: {since_datetime}")
            except ValueError as e:
                logger.error(f"Invalid date format: {since_date}. Use YYYY-MM-DD or ISO format.")
                return False
        
        for item in tqdm(all_items, desc="Scanning releases", unit="folder"):
            item_path = os.path.join(library_path, item)
            if os.path.isdir(item_path):
                label_file = os.path.join(item_path, 'label.tex')
                if os.path.exists(label_file):
                    # Timestamp-Filterung falls since_date angegeben
                    if since_datetime:
                        metadata_file = os.path.join(item_path, 'metadata.json')
                        if os.path.exists(metadata_file):
                            try:
                                with open(metadata_file, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    if 'timestamp' in metadata:
                                        release_datetime = date_parser.parse(metadata['timestamp'])
                                        # Entferne Timezone-Info für Vergleich falls nötig
                                        if release_datetime.tzinfo is not None and since_datetime.tzinfo is None:
                                            release_datetime = release_datetime.replace(tzinfo=None)
                                        elif release_datetime.tzinfo is None and since_datetime.tzinfo is not None:
                                            since_datetime = since_datetime.replace(tzinfo=None)
                                        if release_datetime >= since_datetime:
                                            release_dirs.append((item, "label.tex"))
                                    else:
                                        # Falls kein timestamp, nutze Verzeichnis-Modifikationszeit
                                        dir_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                                        if dir_mtime >= since_datetime:
                                            release_dirs.append((item, "label.tex"))
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.debug(f"Error reading timestamp for {item}: {e}")
                                # Bei Fehlern, falls kein timestamp verfügbar, verwende Verzeichnis-Zeit
                                dir_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                                if dir_mtime >= since_datetime:
                                    release_dirs.append((item, "label.tex"))
                        else:
                            # Falls keine metadata.json, nutze Verzeichnis-Zeit
                            dir_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                            if dir_mtime >= since_datetime:
                                release_dirs.append((item, "label.tex"))
                    else:
                        # Keine Zeitfilterung
                        release_dirs.append((item, "label.tex"))
    
    if not release_dirs:
        logger.warning("No releases with LaTeX labels found")
        return False
    
    # Sortiere alphabetisch für konsistente Reihenfolge
    release_dirs.sort()
    
    # Begrenze Anzahl falls gewünscht
    if max_labels:
        release_dirs = release_dirs[:max_labels]
        logger.info(f"Limited to first {max_labels} releases")
    
    logger.process(f"Combining {len(release_dirs)} LaTeX labels for printing...")
    
    # Konfiguration für 8163 shipping labels (Original-Layout)
    labels_per_page = 10  # 2 Spalten x 5 Zeilen
    pages_needed = (len(release_dirs) + labels_per_page - 1) // labels_per_page
    
    # Verbesserte Dateinamen
    if specific_release:
        base_name = f"vinyl_label_{release_dirs[0][0]}"
    elif since_date:
        # Formatiere Datum für Dateinamen
        date_str = since_date.replace('-', '').replace(':', '').replace('T', '_')[:8]
        base_name = f"vinyl_labels_since_{date_str}_{len(release_dirs)}_releases"
    else:
        base_name = f"vinyl_labels_{len(release_dirs)}_releases"
    output_file = os.path.join(output_dir, f'{base_name}.tex')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # LaTeX-Template Preamble einlesen
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latexTemplate.tex')
            with open(template_path, 'r', encoding='utf-8') as template:
                f.write(template.read())
            
            release_idx = 0
            
            # Seiten erstellen (Original-Algorithmus optimiert) mit Progress Bar
            with tqdm(total=len(release_dirs), desc="Creating labels", unit="label") as pbar:
                for page in range(pages_needed):
                    if release_idx >= len(release_dirs):
                        break
                        
                    f.write("\\begin{tikzpicture}[thick,font=\\Large]\n")
                    
                    # 5 Zeilen x 2 Spalten = 10 Labels pro Seite (Original-Layout)
                    for row in range(5):
                        if release_idx >= len(release_dirs):
                            break
                        for col in [0, 1]:  # Original verwendete [0,1]
                            release_num = (col + 1) + (row * 2) + (page * 10)
                            if release_num > len(release_dirs):
                                break
                            
                            release_dir, label_filename = release_dirs[release_idx]
                            
                            # Position berechnen (Original-Koordinaten)
                            x_pos = 4.1 * col  # Original: 4.1 inches Spaltenabstand
                            y_pos = row * -2   # Original: -2 inches pro Zeile
                            
                            # Label-Rahmen (Original-Design)
                            f.write(f"\t\\draw[rounded corners=0.5cm] ({x_pos} in, {y_pos} in) rectangle +(4in,2in);\n")
                            
                            # QR-Code Position (falls vorhanden)
                            qr_file = os.path.join(library_path, release_dir, 'qrcode.png')
                            if os.path.exists(qr_file):
                                qr_x = x_pos + 3.3
                                qr_y = y_pos - 0.36 + 2
                                # Absoluter Pfad zur QR-Code Datei
                                qr_path = os.path.abspath(qr_file).replace('\\', '/')
                                f.write(f"\\node[right,align=left] at ({qr_x} in, {qr_y} in){{")
                                f.write(f"\\includegraphics[width=1.5cm]{{{qr_path}}}}};\n")
                            
                            # Label-Inhalt einbinden
                            content_x = x_pos
                            content_y = y_pos + 1
                            # Absoluter Pfad zur Label-Datei
                            label_path = os.path.abspath(os.path.join(library_path, release_dir, label_filename)).replace('\\', '/')
                            f.write(f"\t\\node[right,align=left] at ({content_x} in, {content_y} in){{\n")
                            f.write(f"\t\t\\input{{{label_path}}}\n")
                            f.write("\t};\n")
                            
                            release_idx += 1
                            pbar.update(1)  # Progress Bar Update für jedes verarbeitete Label
                    
                    f.write("\\end{tikzpicture}\n")
                    
                    # Neue Seite (Original-Style)
                    if page < pages_needed - 1:
                        f.write("\\clearpage\n")
            
            f.write("\\end{document}\n")
        
        logger.success(f"Master LaTeX document created: {output_file}")
        logger.info(f"📄 {pages_needed} pages with {len(release_dirs)} labels ready for printing")
        
        # PDF kompilieren falls pdflatex verfügbar
        if _compile_pdf(output_file, output_dir):
            logger.success("PDF successfully compiled!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error combining LaTeX labels: {e}")
        return False

def _compile_pdf(tex_file, output_dir):
    """Kompiliert LaTeX zu PDF falls pdflatex verfügbar ist"""
    import subprocess
    import shutil
    
    pdflatex_path = shutil.which("pdflatex")
    if not pdflatex_path:
        logger.info("pdflatex not found - LaTeX file created but not compiled")
        return False
    
    try:
        logger.process("Compiling LaTeX to PDF...")
        
        # Wechsle in Output-Verzeichnis für relative Pfade
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        # Extrahiere Basis-Dateiname
        tex_basename = os.path.splitext(os.path.basename(tex_file))[0]
        
        # Kompiliere PDF (2x für Referenzen)
        for run in range(2):
            result = subprocess.run([
                'pdflatex', 
                '-interaction=nonstopmode',
                '-halt-on-error',
                f'{tex_basename}.tex'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"pdflatex error: {result.stderr}")
                return False
        
        # Aufräumen: .aux, .log Dateien löschen
        for ext in ['.aux', '.log']:
            cleanup_file = f"{tex_basename}{ext}"
            if os.path.exists(cleanup_file):
                os.remove(cleanup_file)
        
        os.chdir(original_cwd)
        return True
        
    except Exception as e:
        logger.error(f"PDF compilation failed: {e}")
        if 'original_cwd' in locals():
            os.chdir(original_cwd)
        return False