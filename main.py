#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: ffx
"""

import time
import sys
import os

# Füge src/ zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mirror import DiscogsLibraryMirror
from logger import logger

def main():
    # Startzeit speichern
    start_time = time.time()
    
    # library spiegeln / änderungen abgleichen:
    library_mirror = DiscogsLibraryMirror()
    logger.separator("Starting Discogs Library Sync")
    
    
    # library_mirror.sync_releases()
    # library_mirror.sync_single_release(65923)
    
    logger.separator()
    library_mirror.sync_single_release(96648)
    
    # Ende des Prozesses - berechne die Dauer
    end_time = time.time()
    duration = end_time - start_time
      
    # Ausgabe der Dauer
    logger.separator("Process Completed")
    logger.success(f"Script completed in {duration:.2f} seconds")


if __name__ == "__main__":
    main()
