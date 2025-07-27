#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX Label Master Document Generator

Generiert druckfertige PDF-Labels aus Discogs Release-Daten
Basierend auf der originalen combineLatex Funktion

Usage:
    python generate_labels.py                    # Alle Labels
    python generate_labels.py --max 15           # Erste 15 Labels  
    python generate_labels.py --output /tmp      # Custom Output-Pfad

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

def main():
    parser = argparse.ArgumentParser(
        description='Generate printable LaTeX labels from Discogs releases',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--max', 
        type=int, 
        default=None,
        help='Maximum number of labels to generate (default: all)'
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
            # Default: Eine Ebene über der Discogs Library mit Zeitstempel
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = library_path.parent / "vinyl_labels" / f"export_{timestamp}"
        
        logger.separator("LaTeX Label Generation")
        logger.info(f"Library path: {library_path}")
        logger.info(f"Output directory: {output_dir}")
        
        if args.max:
            logger.info(f"Maximum labels: {args.max}")
        
        # Generiere Master-Dokument
        success = combine_latex_labels(
            library_path=str(library_path),
            output_dir=str(output_dir),
            max_labels=args.max
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