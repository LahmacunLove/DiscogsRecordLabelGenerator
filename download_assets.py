#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download assets for Discogs releases (Phase 2)

After syncing Discogs metadata (Phase 1), this script downloads:
- Cover images
- YouTube video matches
- Audio files

Usage:
    python3 download_assets.py                  # Download all missing assets
    python3 download_assets.py --covers-only    # Only download covers
    python3 download_assets.py --youtube-only   # Only match/download YouTube
    python3 download_assets.py --max=10         # Process first 10 releases

Created on 2025-01-22
@author: ffx
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import load_config
from database import DiscogsDatabase
from mirror import DiscogsLibraryMirror
from logger import logger
from tqdm import tqdm


def download_covers(library_mirror, max_releases=None):
    """Download cover images for releases that don't have them"""
    logger.separator("Downloading Cover Images")

    with library_mirror._get_db_connection() as db:
        releases_needing_covers = db.get_releases_needing_covers()

    if not releases_needing_covers:
        logger.info("All releases already have covers downloaded")
        return

    if max_releases:
        releases_needing_covers = releases_needing_covers[:max_releases]

    logger.info(f"Found {len(releases_needing_covers)} releases needing covers")

    with tqdm(total=len(releases_needing_covers), desc="Downloading covers", unit="release") as pbar:
        for release_id in releases_needing_covers:
            try:
                # Get metadata from database
                metadata = library_mirror.get_release_metadata(release_id)
                if not metadata:
                    logger.warning(f"No metadata found for release {release_id}")
                    pbar.update(1)
                    continue

                # Download covers
                library_mirror.save_cover_art(release_id, metadata)

                # Mark as downloaded in database
                with library_mirror._get_db_connection() as db:
                    db.mark_covers_downloaded(release_id)

                pbar.update(1)

            except Exception as e:
                logger.error(f"Failed to download covers for {release_id}: {e}")
                pbar.update(1)

    logger.success(f"Cover download complete!")


def match_youtube(library_mirror, max_releases=None):
    """Match YouTube videos for releases"""
    logger.separator("Matching YouTube Videos")

    with library_mirror._get_db_connection() as db:
        releases_needing_youtube = db.get_releases_needing_youtube()

    if not releases_needing_youtube:
        logger.info("All releases already have YouTube matches")
        return

    if max_releases:
        releases_needing_youtube = releases_needing_youtube[:max_releases]

    logger.info(f"Found {len(releases_needing_youtube)} releases needing YouTube matching")

    with tqdm(total=len(releases_needing_youtube), desc="Matching YouTube", unit="release") as pbar:
        for release_id in releases_needing_youtube:
            try:
                # Get metadata from database
                metadata = library_mirror.get_release_metadata(release_id)
                if not metadata:
                    logger.warning(f"No metadata found for release {release_id}")
                    pbar.update(1)
                    continue

                # Set release folder
                title = metadata.get('title', release_id)
                from utils import sanitize_filename
                release_folder = library_mirror.library_path / f"{release_id}_{sanitize_filename(title)}"
                library_mirror.release_folder = release_folder

                # Match YouTube videos (will save yt_matches.json)
                from youtube_handler import YouTubeMatcher
                yt_matcher = YouTubeMatcher(str(release_folder))
                yt_matcher.match_discogs_release_youtube(metadata)

                # Save matches to database and mark as matched
                if (release_folder / "yt_matches.json").exists():
                    import json
                    with open(release_folder / "yt_matches.json", 'r') as f:
                        matches = json.load(f)

                    with library_mirror._get_db_connection() as db:
                        db.save_youtube_matches(release_id, matches)
                        db.mark_youtube_matched(release_id)

                pbar.update(1)

            except Exception as e:
                logger.error(f"Failed to match YouTube for {release_id}: {e}")
                pbar.update(1)

    logger.success(f"YouTube matching complete!")


def download_audio(library_mirror, max_releases=None):
    """Download audio files for releases with YouTube matches"""
    logger.separator("Downloading Audio Files")

    with library_mirror._get_db_connection() as db:
        releases_needing_audio = db.get_releases_needing_audio()

    if not releases_needing_audio:
        logger.info("All releases with YouTube matches already have audio downloaded")
        return

    if max_releases:
        releases_needing_audio = releases_needing_audio[:max_releases]

    logger.info(f"Found {len(releases_needing_audio)} releases needing audio downloads")

    with tqdm(total=len(releases_needing_audio), desc="Downloading audio", unit="release") as pbar:
        for release_id in releases_needing_audio:
            try:
                # Get metadata from database
                metadata = library_mirror.get_release_metadata(release_id)
                if not metadata:
                    logger.warning(f"No metadata found for release {release_id}")
                    pbar.update(1)
                    continue

                # Set release folder
                title = metadata.get('title', release_id)
                from utils import sanitize_filename
                release_folder = library_mirror.library_path / f"{release_id}_{sanitize_filename(title)}"
                library_mirror.release_folder = release_folder

                # Download audio via YouTube
                from youtube_handler import YouTubeMatcher
                yt_matcher = YouTubeMatcher(str(release_folder))

                # Load existing matches
                yt_matches_file = release_folder / "yt_matches.json"
                if yt_matches_file.exists():
                    import json
                    with open(yt_matches_file, 'r') as f:
                        yt_matcher.matches = json.load(f)

                    # Download audio for each match
                    yt_matcher.audioDWNLDAnalyse()

                    # Mark as downloaded
                    with library_mirror._get_db_connection() as db:
                        db.mark_audio_downloaded(release_id)

                pbar.update(1)

            except Exception as e:
                logger.error(f"Failed to download audio for {release_id}: {e}")
                pbar.update(1)

    logger.success(f"Audio download complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Download assets for Discogs releases (Phase 2)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--covers-only',
        action='store_true',
        help='Only download cover images'
    )

    parser.add_argument(
        '--youtube-only',
        action='store_true',
        help='Only match YouTube videos'
    )

    parser.add_argument(
        '--audio-only',
        action='store_true',
        help='Only download audio files'
    )

    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Process maximum N releases'
    )

    args = parser.parse_args()

    # Initialize mirror
    library_mirror = DiscogsLibraryMirror()

    # Show current status
    with library_mirror._get_db_connection() as db:
        stats = db.get_statistics()

    logger.info(f"Collection status:")
    logger.info(f"  Total releases: {stats['total_releases']}")
    logger.info(f"  Covers downloaded: {stats['covers_downloaded']}/{stats['total_releases']}")
    logger.info(f"  YouTube matched: {stats['youtube_matched']}/{stats['total_releases']}")
    logger.info(f"  Audio downloaded: {stats['audio_downloaded']}/{stats['total_releases']}")
    print()

    # Execute requested operations
    if args.covers_only:
        download_covers(library_mirror, args.max)
    elif args.youtube_only:
        match_youtube(library_mirror, args.max)
    elif args.audio_only:
        download_audio(library_mirror, args.max)
    else:
        # Download everything
        download_covers(library_mirror, args.max)
        match_youtube(library_mirror, args.max)
        download_audio(library_mirror, args.max)

    # Show final status
    print()
    with library_mirror._get_db_connection() as db:
        stats = db.get_statistics()

    logger.success("Final status:")
    logger.info(f"  Covers downloaded: {stats['covers_downloaded']}/{stats['total_releases']}")
    logger.info(f"  YouTube matched: {stats['youtube_matched']}/{stats['total_releases']}")
    logger.info(f"  Audio downloaded: {stats['audio_downloaded']}/{stats['total_releases']}")


if __name__ == "__main__":
    main()
