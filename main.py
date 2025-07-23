#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    
    
    library_mirror.sync_releases()
    # library_mirror.sync_single_release(65923)
    
    print("\n--------------------------------\n")
    # library_mirror.sync_single_release(96648)
    
    # Ende des Prozesses - berechne die Dauer
    end_time = time.time()
    duration = end_time - start_time
      
    # Ausgabe der Dauer
    print("\n--------------------------------")
    print(f"Das Script hat {duration:.2f} Sekunden benötigt.")


if __name__ == "__main__":
    main()
