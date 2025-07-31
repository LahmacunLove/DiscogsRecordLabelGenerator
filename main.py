#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: ffx
"""

import time
import sys
import os
import argparse

# Füge src/ zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mirror import DiscogsLibraryMirror
from logger import logger

def main():
    parser = argparse.ArgumentParser(
        description='Sync Discogs collection and generate labels',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
    
    args = parser.parse_args()
    
    # Startzeit speichern
    start_time = time.time()
    
    # library spiegeln / änderungen abgleichen:
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
    else:
        # Normal sync operation
        # Bestimme Limit für Development Mode
        limit = None
        if args.max:
            limit = args.max
            logger.separator(f"Starting Discogs Library Sync (Limited to {limit} releases)")
        elif args.dev:
            limit = 10
            logger.separator("Starting Discogs Library Sync (Development Mode - 10 releases)")
        else:
            logger.separator("Starting Discogs Library Sync (Full Collection)")
        
        library_mirror.sync_releases(max_releases=limit)
    
    logger.separator()
    
    # Ende des Prozesses - berechne die Dauer
    end_time = time.time()
    duration = end_time - start_time
      
    # Ausgabe der Dauer
    logger.separator("Process Completed")
    logger.success(f"Script completed in {duration:.2f} seconds")


if __name__ == "__main__":
    main()
