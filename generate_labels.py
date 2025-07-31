#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX Label Master Document Generator

Generiert druckfertige PDF-Labels aus Discogs Release-Daten
Basierend auf der originalen combineLatex Funktion

Usage:
    python generate_labels.py                       # Alle Labels
    python generate_labels.py --dev                 # Erste 10 Labels (Development)
    python generate_labels.py --max 15              # Erste 15 Labels  
    python generate_labels.py --output /tmp         # Custom Output-Pfad
    python generate_labels.py --release-id 12345    # Einzelnes Label
    python generate_labels.py --since 2024-12-01    # Labels seit Datum

@author: ffx
"""

import os
import argparse
import sys
from pathlib import Path

# Füge src/ zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from latex_generator import combine_latex_labels
from logger import logger
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(
        description='Generate printable LaTeX labels from Discogs releases',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--dev', '--development',
        action='store_true',
        help='Development mode: generate first 10 labels (repeatable)'
    )
    
    parser.add_argument(
        '--max', 
        type=int, 
        default=None,
        help='Maximum number of labels to generate (default: all, overrides --dev)'
    )
    
    parser.add_argument(
        '--release-id',
        type=str,
        default=None,
        help='Generate label for specific release ID (e.g., "12345")'
    )
    
    parser.add_argument(
        '--since',
        type=str,
        default=None,
        help='Generate labels for releases added since date (YYYY-MM-DD or ISO format)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='Output directory for LaTeX and PDF files (default: parent dir of library)'
    )
    
    parser.add_argument(
        '--library-path',
        type=str,
        default=None,
        help='Path to Discogs library (default: from config)'
    )
    
    parser.add_argument(
        '--compile-pdf',
        action='store_true',
        help='Force PDF compilation even if pdflatex not found'
    )
    
    args = parser.parse_args()
    
    # Validierung: --release-id und andere Parameter schließen sich aus
    if args.release_id and (args.max or args.since or args.dev):
        parser.error("--release-id cannot be combined with --max, --since, or --dev")
    
    try:
        # Lade Konfiguration
        config = load_config()
        
        # Bestimme Library-Pfad
        if args.library_path:
            library_path = Path(args.library_path).expanduser()
        else:
            library_path = Path(config["LIBRARY_PATH"]).expanduser()
        
        if not library_path.exists():
            logger.error(f"Library path does not exist: {library_path}")
            sys.exit(1)
        
        # Bestimme Output-Pfad
        if args.output:
            output_dir = Path(args.output).resolve()
        else:
            # Default: Eine Ebene über der Discogs Library ohne Zeitstempel (für Development)
            # TODO: Für finale Version wieder Zeitstempel aktivieren
            output_dir = library_path.parent / "vinyl_labels"
        
        logger.separator("LaTeX Label Generation")
        logger.info(f"Library path: {library_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Bestimme Limit für Development Mode
        limit = None
        if args.max:
            limit = args.max
            logger.info(f"Maximum labels: {limit}")
        elif args.dev:
            limit = 10
            logger.info("Development mode: generating first 10 labels")
        
        if args.release_id:
            logger.info(f"Generating label for release: {args.release_id}")
        
        if args.since:
            logger.info(f"Generating labels for releases added since: {args.since}")
        
        # Generiere Master-Dokument
        success = combine_latex_labels(
            library_path=str(library_path),
            output_dir=str(output_dir),
            max_labels=limit,
            specific_release=args.release_id,
            since_date=args.since
        )
        
        if success:
            logger.separator("Generation Complete")
            
            # Zeige generierte Dateien
            tex_files = list(output_dir.glob('*.tex'))
            pdf_files = list(output_dir.glob('*.pdf'))
            
            for tex_file in tex_files:
                logger.success(f"📄 LaTeX: {tex_file}")
            
            if pdf_files:
                for pdf_file in pdf_files:
                    logger.success(f"📋 PDF: {pdf_file}")
                logger.info("🖨️  Ready for printing!")
            else:
                logger.info("💡 Install pdflatex to auto-generate PDF")
                if tex_files:
                    tex_name = tex_files[0].stem
                    logger.info(f"Manual compilation: cd {output_dir} && pdflatex {tex_name}.tex")
            
        else:
            logger.error("Label generation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()