#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: ffx
"""

import time
import sys
import os
import argparse

# Add src/ to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mirror import DiscogsLibraryMirror
from logger import logger
from latex_generator import combine_latex_labels
from pathlib import Path

def gui_progress(current, total, phase="Processing"):
    """Output GUI-friendly progress information"""
    percentage = (current / total) * 100 if total > 0 else 0
    print(f"GUI_PROGRESS: {percentage:.1f}% ({current}/{total}) - {phase}", flush=True)

def generate_final_labels(library_mirror):
    """Generate combined LaTeX labels after successful sync"""
    try:
        logger.separator("Generating Final Labels")
        logger.info("Combining all LaTeX labels into master document...")
        
        # Use library path from the mirror
        library_path = str(library_mirror.library_path)
        output_dir = str(library_mirror.library_path.parent / "vinyl_labels")
        
        # Generate master document with all labels
        success = combine_latex_labels(
            library_path=library_path,
            output_dir=output_dir,
            max_labels=None,  # Generate all labels
            specific_release=None,
            since_date=None
        )
        
        if success:
            logger.success("📋 Master label document generated successfully!")
            logger.info(f"📁 Output directory: {output_dir}")
            
            # Check for generated files
            output_path = Path(output_dir)
            tex_files = list(output_path.glob('*.tex'))
            pdf_files = list(output_path.glob('*.pdf'))
            
            if pdf_files:
                logger.success("🖨️  PDF ready for printing!")
            elif tex_files:
                logger.info("💡 Install pdflatex to auto-generate PDF")
        else:
            logger.warning("⚠️  Label generation failed, but main process completed successfully")
            
    except Exception as e:
        logger.error(f"Error generating labels: {e}")
        logger.info("Main process completed successfully despite label generation error")

def main():
    parser = argparse.ArgumentParser(
        description='Sync Discogs collection and generate labels',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add GUI mode for progress reporting
    parser.add_argument(
        '--gui-mode',
        action='store_true',
        help='Enable GUI-friendly progress output (internal use)'
    )
    
    parser.add_argument(
        '--dev', '--development',
        action='store_true',
        help='Development mode: process first 10 releases from collection (repeatable)'
    )
    
    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Process first N releases from collection (repeatable, overrides --dev)'
    )
    
    parser.add_argument(
        '--regenerate-labels',
        action='store_true',
        help='Regenerate all LaTeX label files without downloading new releases'
    )
    
    parser.add_argument(
        '--regenerate-waveforms',
        action='store_true',
        help='Regenerate all waveform PNG files without downloading new releases'
    )
    
    parser.add_argument(
        '--dryrun',
        action='store_true',
        help='Dry run mode: process existing releases offline without Discogs/YouTube sync (analyze, generate QR codes, labels)'
    )
    
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Download-only mode: sync releases and download covers/audio without analysis or label generation'
    )
    
    args = parser.parse_args()
    
    # Store start time
    start_time = time.time()
    
    # Mirror library / sync changes:
    library_mirror = DiscogsLibraryMirror()
    
    # Handle special modes
    if args.regenerate_labels or args.regenerate_waveforms:
        if args.regenerate_labels and args.regenerate_waveforms:
            logger.separator("Regenerating all LaTeX labels and waveforms")
        elif args.regenerate_labels:
            logger.separator("Regenerating all LaTeX labels")
        elif args.regenerate_waveforms:
            logger.separator("Regenerating all waveforms")
        
        library_mirror.regenerate_existing_files(
            regenerate_labels=args.regenerate_labels,
            regenerate_waveforms=args.regenerate_waveforms
        )
    elif args.dryrun:
        logger.separator("Dry Run Mode - Processing existing releases offline")
        library_mirror.process_existing_releases_offline()
        
        # Generate labels after dry run processing
        generate_final_labels(library_mirror)
    elif args.download_only:
        # Determine limit for Download-Only Mode
        limit = None
        if args.max:
            limit = args.max
            logger.separator(f"Download-Only Mode - Syncing {limit} releases (no analysis)")
        elif args.dev:
            limit = 10
            logger.separator("Download-Only Mode - Development (10 releases, no analysis)")
        else:
            logger.separator("Download-Only Mode - Full Collection (no analysis)")
        
        progress_cb = gui_progress if args.gui_mode else None
        library_mirror.sync_releases(max_releases=limit, download_only=True, progress_callback=progress_cb)
    else:
        # Normal sync operation
        # Determine limit for Development Mode
        limit = None
        if args.max:
            limit = args.max
            logger.separator(f"Starting Discogs Library Sync (Limited to {limit} releases)")
        elif args.dev:
            limit = 10
            logger.separator("Starting Discogs Library Sync (Development Mode - 10 releases)")
        else:
            logger.separator("Starting Discogs Library Sync (Full Collection)")
        
        progress_cb = gui_progress if args.gui_mode else None
        library_mirror.sync_releases(max_releases=limit, progress_callback=progress_cb)
        
        # Generate labels after normal sync operation (with analysis)
        generate_final_labels(library_mirror)
    
    logger.separator()
    
    # End of process - calculate duration
    end_time = time.time()
    duration = end_time - start_time
      
    # Output duration
    logger.separator("Process Completed")
    logger.success(f"Script completed in {duration:.2f} seconds")


if __name__ == "__main__":
    main()
