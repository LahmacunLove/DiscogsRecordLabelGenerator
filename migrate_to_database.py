#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to import existing JSON metadata into SQLite database

Scans the library folder for all metadata.json files and imports them into
the new SQLite database. Also imports YouTube matches and audio analysis data.

Usage:
    python3 migrate_to_database.py

Created on 2025-01-22
@author: ffx
"""

import json
import sys
from pathlib import Path
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import load_config
from database import DiscogsDatabase
from logger import logger


def migrate_metadata_files():
    """Migrate all metadata.json files to database"""
    config = load_config()
    library_path = Path(config["LIBRARY_PATH"]).expanduser()

    # Initialize database
    db_path = library_path / "discogs_collection.db"
    db = DiscogsDatabase(db_path)

    logger.info(f"Scanning library: {library_path}")

    # Find all metadata.json files
    metadata_files = list(library_path.glob("*/metadata.json"))
    logger.info(f"Found {len(metadata_files)} releases to migrate")

    if not metadata_files:
        logger.warning("No metadata.json files found - nothing to migrate")
        return

    # Process each release
    success_count = 0
    error_count = 0

    with tqdm(total=len(metadata_files), desc="Migrating releases", unit="release") as pbar:
        for metadata_file in metadata_files:
            release_folder = metadata_file.parent

            try:
                # Load metadata
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Add release folder path
                metadata['release_folder'] = str(release_folder)

                # Save to database
                if db.save_release(metadata):
                    success_count += 1

                    # Import YouTube matches if they exist
                    yt_matches_file = release_folder / "yt_matches.json"
                    if yt_matches_file.exists():
                        try:
                            with open(yt_matches_file, 'r', encoding='utf-8') as f:
                                yt_matches = json.load(f)
                            release_id = metadata.get('release_id') or metadata.get('id')
                            db.save_youtube_matches(release_id, yt_matches)
                        except Exception as e:
                            logger.debug(f"Could not import YouTube matches: {e}")

                    # Import audio analysis files if they exist
                    release_id = metadata.get('release_id') or metadata.get('id')
                    for track in metadata.get('tracklist', []):
                        track_pos = track.get('position', '')
                        if not track_pos:
                            continue

                        # Check for analysis file
                        analysis_file = release_folder / f"{track_pos}.json"
                        if analysis_file.exists():
                            try:
                                with open(analysis_file, 'r', encoding='utf-8') as f:
                                    analysis_data = json.load(f)

                                # Extract relevant data
                                analysis_info = {
                                    'bpm': analysis_data.get('rhythm', {}).get('bpm'),
                                    'key': analysis_data.get('tonal', {}).get('key_key'),
                                    'has_waveform': (release_folder / f"{track_pos}_waveform.png").exists(),
                                    'has_spectrogram': (release_folder / f"{track_pos}_Mel-spectogram.png").exists(),
                                    'has_chromagram': (release_folder / f"{track_pos}_HPCP_chromatogram.png").exists(),
                                    'analysis_file': str(analysis_file)
                                }

                                db.save_audio_analysis(release_id, track_pos, analysis_info)
                            except Exception as e:
                                logger.debug(f"Could not import analysis for {track_pos}: {e}")

                else:
                    error_count += 1

            except Exception as e:
                logger.error(f"Error migrating {release_folder.name}: {e}")
                error_count += 1

            pbar.update(1)

    # Print statistics
    logger.success(f"\nMigration complete!")
    logger.info(f"Successfully migrated: {success_count} releases")
    if error_count > 0:
        logger.warning(f"Errors: {error_count} releases")

    # Show database statistics
    stats = db.get_statistics()
    logger.info("\nDatabase Statistics:")
    logger.info(f"  Total releases: {stats['total_releases']}")
    logger.info(f"  Total tracks: {stats['total_tracks']}")
    logger.info(f"  Total artists: {stats['total_artists']}")
    logger.info(f"  Total labels: {stats['total_labels']}")

    if stats['by_decade']:
        logger.info("\n  Releases by decade:")
        for decade, count in sorted(stats['by_decade'].items()):
            logger.info(f"    {decade}: {count} releases")

    db.close()


if __name__ == "__main__":
    logger.info("Starting migration to SQLite database...")
    migrate_metadata_files()
