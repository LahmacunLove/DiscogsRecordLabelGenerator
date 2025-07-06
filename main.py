#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 19:02:55 2025

@author: ffx
"""

import time
from mirror import DiscogsLibraryMirror

def main():
    # Startzeit speichern
    start_time = time.time()
    
    # library spiegeln / änderungen abgleichen:
    library_mirror = DiscogsLibraryMirror()
    print("\n--------------------------------\n")
    
    
    # library_mirror.sync_releases()
    # library_mirror.sync_single_release(15589261)
    
    print("\n--------------------------------\n")
    library_mirror.sync_single_release(30685762)
    
    # Ende des Prozesses - berechne die Dauer
    end_time = time.time()
    duration = end_time - start_time
      
    # Ausgabe der Dauer
    print("\n--------------------------------")
    print(f"Das Script hat {duration:.2f} Sekunden benötigt.")


if __name__ == "__main__":
    main()
