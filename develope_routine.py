#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 19:02:55 2025

@author: ffx
"""

import time
import argparse
from mirror import DiscogsLibraryMirror
from pathlib import Path

# Hardcoded Argumente für Entwicklung (Release 123456 mit Overwrite)
DEBUG_ARGS = ['--release', '30685762', '--overwrite']

def main():
    # CLI-Argumente parsen
    parser = argparse.ArgumentParser(
        description="Spiegelt Deine Discogs-Library oder verarbeitet gezielt ein Release."
    )
    parser.add_argument(
        "-r", "--release", 
        type=int, 
        help="Nur dieses Release (ID) verarbeiten"
    )
    parser.add_argument(
        "-o", "--overwrite", 
        action="store_true", 
        help="Bereits existierende Metadaten überschreiben"
    )

    # DEBUG: Immer hardcodierte Argumente verwenden
    args = parser.parse_args(DEBUG_ARGS)
    print(f"[DEBUG] Nutze Argumente: {DEBUG_ARGS}")

    start_time = time.time()
    library_mirror = DiscogsLibraryMirror() # connect zur lib
    library_mirror.library_path = Path(library_mirror.config["LIBRARY_PATH"]).expanduser()

    if args.release:
        release_id = args.release
        existing = any(
            entry.is_dir() and entry.name.startswith(f"{release_id}_")
            for entry in library_mirror.library_path.iterdir()
        ) if library_mirror.library_path.exists() else False

        if existing and not args.overwrite:
            print(f"Release {release_id} existiert bereits. Verwende --overwrite, um es neu zu laden.")
        else:
            if existing and args.overwrite:
                print(f"Lösche vorhandenes Release {release_id} zur Überschreibung...")
                library_mirror.delete_release_folder(release_id)
            print(f"Lade Metadaten für Release {release_id}...")
            metadata = library_mirror.discogs.release(release_id).data
            library_mirror.save_release_metadata(release_id, metadata)
    else:
        library_mirror.sync_releases()

    duration = time.time() - start_time
    print(f"Das Script hat {duration:.2f} Sekunden benötigt.")

if __name__ == "__main__":
    main()
