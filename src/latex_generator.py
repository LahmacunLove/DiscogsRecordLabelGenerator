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
from logger import logger

def unicode_to_latex(text):
    """Konvertiert Unicode-Zeichen für LaTeX-Kompatibilität"""
    if pd.isna(text) or text == '':
        return ''
    
    # Basis-Ersetzungen für LaTeX
    replacements = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '\\': '\\textbackslash{}',
        '<': '\\textless{}',
        '>': '\\textgreater{}',
    }
    
    result = str(text)
    for char, replacement in replacements.items():
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
    """Erstellt eine LaTeX-Label-Datei für ein Release"""
    
    label_file = os.path.join(release_folder, 'label.tex')
    
    # Prüfe ob Label bereits existiert
    if os.path.exists(label_file):
        logger.info(f"LaTeX label already exists: {os.path.basename(label_file)}")
        return True
    
    try:
        logger.process(f"Creating LaTeX label for release {metadata.get('id', 'unknown')}")
        
        # Erstelle DataFrame für Tracks
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
                    bpm = str(round(analysis_data.get('rhythm', {}).get('bpm', 0)))
                    key = analysis_data.get('tonal', {}).get('key_key', '')
                except:
                    pass
            
            # Waveform-Pfad
            waveform_path = f"{track_base}_waveform.png"
            waveform_latex = ''
            if os.path.exists(waveform_path):
                waveform_latex = f'\\includegraphics[width=2cm]{{{waveform_path}}}'
            
            tracks_data.append({
                'pos': track_pos,
                'title': track_title,
                'artist': track_artist,
                'duration': track_duration,
                'bpm': bpm,
                'key': key,
                'waveform': waveform_latex
            })
        
        # DataFrame erstellen
        track_df = pd.DataFrame(tracks_data)
        
        # NaN-Werte durch leere Strings ersetzen
        track_df = track_df.fillna('')
        
        # Unicode-Konvertierung für LaTeX
        for col in ['pos', 'title', 'artist', 'duration', 'bpm', 'key']:
            if col in track_df.columns:
                track_df[col] = track_df[col].apply(unicode_to_latex)
        
        # Behandle Various Artists Problem
        unique_artists = track_df['artist'].unique()
        if len(unique_artists) <= 1 or all(artist == '' for artist in unique_artists):
            # Nur ein Artist oder alle leer - verstecke Artist-Spalte
            columns_to_show = ['pos', 'title', 'duration', 'bpm', 'key', 'waveform']
        else:
            # Mehrere Artists - kombiniere title und artist
            track_df['title'] = track_df['title'] + ' / ' + track_df['artist']
            columns_to_show = ['pos', 'title', 'duration', 'bpm', 'key', 'waveform']
        
        # Filtere DataFrame
        track_df_display = track_df[columns_to_show]
        
        # Erstelle LaTeX-Tabelle
        latex_table = track_df_display.to_latex(
            index=False,
            escape=False,  # Wichtig: Lass LaTeX-Befehle durch
            column_format="@{}lXlllc@{}"
        )
        
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
        
        # Jahr extrahieren
        year = str(metadata.get('year', ''))
        release_id = str(metadata.get('id', ''))
        
        # LaTeX-Inhalt erstellen
        latex_content = f'''\\begin{{fitbox}}{{8cm}}{{4.5cm}}
\\textbf{{{unicode_to_latex(artist_str)}}} \\\\
{unicode_to_latex(title)}
\\vfill
\\scriptsize
{latex_table}
\\vfill
\\raggedright \\tinyb{{{unicode_to_latex(label_str)}, {year}, releaseID: {release_id}}}
\\end{{fitbox}}'''
        
        # Schreibe LaTeX-Datei
        with open(label_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Ersetze tabular durch tabularx für bessere Spaltenbreiten
        inplace_change(label_file, "\\begin{tabular}", "\\begin{tabularx}{8.5cm}")
        inplace_change(label_file, "\\end{tabular}", "\\end{tabularx}")
        
        logger.success(f"LaTeX label created: {os.path.basename(label_file)}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating LaTeX label: {e}")
        return False

def combine_latex_labels(library_path, output_dir, max_labels=None):
    """
    Kombiniert alle Labels zu einem druckbaren LaTeX-Dokument
    Basierend auf der originalen combineLatex Funktion aus der Git-History
    
    Args:
        library_path: Pfad zum Discogs Library Verzeichnis
        output_dir: Ausgabe-Verzeichnis für das finale LaTeX-Dokument
        max_labels: Maximale Anzahl Labels (None = alle)
    """
    
    # Erstelle Output-Verzeichnis falls nicht vorhanden
    os.makedirs(output_dir, exist_ok=True)
    
    # Finde alle Release-Ordner mit label.tex
    release_dirs = []
    for item in os.listdir(library_path):
        item_path = os.path.join(library_path, item)
        if os.path.isdir(item_path):
            label_file = os.path.join(item_path, 'label.tex')
            if os.path.exists(label_file):
                release_dirs.append(item)
    
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
    base_name = f"vinyl_labels_{len(release_dirs)}_releases"
    output_file = os.path.join(output_dir, f'{base_name}.tex')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # LaTeX-Template Preamble einlesen
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'latexTemplate.tex')
            with open(template_path, 'r', encoding='utf-8') as template:
                f.write(template.read())
            
            release_idx = 0
            
            # Seiten erstellen (Original-Algorithmus optimiert)
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
                        
                        current_release = release_dirs[release_idx]
                        
                        # Position berechnen (Original-Koordinaten)
                        x_pos = 4.1 * col  # Original: 4.1 inches Spaltenabstand
                        y_pos = row * -2   # Original: -2 inches pro Zeile
                        
                        # Label-Rahmen (Original-Design)
                        f.write(f"\t\\draw[rounded corners=0.5cm] ({x_pos} in, {y_pos} in) rectangle +(4in,2in);\n")
                        
                        # QR-Code Position (falls vorhanden)
                        qr_file = os.path.join(library_path, current_release, 'qrcode.png')
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
                        label_path = os.path.abspath(os.path.join(library_path, current_release, 'label.tex')).replace('\\', '/')
                        f.write(f"\t\\node[right,align=left] at ({content_x} in, {content_y} in){{\n")
                        f.write(f"\t\t\\input{{{label_path}}}\n")
                        f.write("\t};\n")
                        
                        release_idx += 1
                
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