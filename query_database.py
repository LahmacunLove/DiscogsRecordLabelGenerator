#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database query examples and testing script

Demonstrates how to query the SQLite database for collection insights.

Usage:
    python3 query_database.py

Created on 2025-01-22
@author: ffx
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import load_config
from database import DiscogsDatabase
from logger import logger


def show_statistics(db):
    """Display collection statistics"""
    logger.info("\n=== Collection Statistics ===")
    stats = db.get_statistics()

    logger.info(f"Total releases: {stats['total_releases']}")
    logger.info(f"Total tracks: {stats['total_tracks']}")
    logger.info(f"Total artists: {stats['total_artists']}")
    logger.info(f"Total labels: {stats['total_labels']}")

    if stats['by_decade']:
        logger.info("\nReleases by decade:")
        for decade, count in sorted(stats['by_decade'].items(), reverse=True):
            bar = '█' * (count // 2)
            logger.info(f"  {decade}: {bar} {count}")


def search_artist(db, artist_name):
    """Search for releases by artist"""
    logger.info(f"\n=== Searching for artist: '{artist_name}' ===")
    releases = db.search_releases_by_artist(artist_name)

    if not releases:
        logger.warning("No releases found")
        return

    logger.info(f"Found {len(releases)} release(s):")
    for release in releases:
        logger.info(f"  [{release['year']}] {release['title']} (ID: {release['release_id']})")


def search_label(db, label_name):
    """Search for releases by label"""
    logger.info(f"\n=== Searching for label: '{label_name}' ===")
    releases = db.search_releases_by_label(label_name)

    if not releases:
        logger.warning("No releases found")
        return

    logger.info(f"Found {len(releases)} release(s):")
    for release in releases:
        logger.info(f"  [{release['year']}] {release['title']} (ID: {release['release_id']})")


def search_year(db, year):
    """Get all releases from a specific year"""
    logger.info(f"\n=== Releases from {year} ===")
    releases = db.search_releases_by_year(year)

    if not releases:
        logger.warning("No releases found")
        return

    logger.info(f"Found {len(releases)} release(s):")
    for release in releases:
        logger.info(f"  {release['title']} (ID: {release['release_id']})")


def show_release_details(db, release_id):
    """Show complete details for a release"""
    logger.info(f"\n=== Release Details: {release_id} ===")
    release = db.get_release(release_id)

    if not release:
        logger.warning("Release not found")
        return

    logger.info(f"Title: {release['title']}")
    logger.info(f"Artist(s): {', '.join(release['artist'])}")
    logger.info(f"Label(s): {', '.join(release['label'])}")
    if release['catalog_numbers']:
        logger.info(f"Catalog: {', '.join(release['catalog_numbers'])}")
    logger.info(f"Year: {release['year']}")
    logger.info(f"Genres: {', '.join(release['genres'])}")
    logger.info(f"Folder: {release['release_folder']}")

    logger.info(f"\nTracks ({len(release['tracklist'])}):")
    for track in release['tracklist']:
        duration = f" [{track['duration']}]" if track['duration'] else ""
        logger.info(f"  {track['position']}. {track['title']}{duration}")


def interactive_mode(db):
    """Interactive query mode"""
    logger.info("\n=== Interactive Database Query Mode ===")
    logger.info("Commands:")
    logger.info("  stats - Show collection statistics")
    logger.info("  artist <name> - Search by artist")
    logger.info("  label <name> - Search by label")
    logger.info("  year <year> - Search by year")
    logger.info("  release <id> - Show release details")
    logger.info("  quit - Exit")

    while True:
        try:
            command = input("\n> ").strip().lower()

            if not command:
                continue

            if command == "quit":
                break
            elif command == "stats":
                show_statistics(db)
            elif command.startswith("artist "):
                artist_name = command[7:].strip()
                search_artist(db, artist_name)
            elif command.startswith("label "):
                label_name = command[6:].strip()
                search_label(db, label_name)
            elif command.startswith("year "):
                try:
                    year = int(command[5:].strip())
                    search_year(db, year)
                except ValueError:
                    logger.error("Invalid year")
            elif command.startswith("release "):
                try:
                    release_id = int(command[8:].strip())
                    show_release_details(db, release_id)
                except ValueError:
                    logger.error("Invalid release ID")
            else:
                logger.warning("Unknown command")

        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            break


def main():
    """Main entry point"""
    config = load_config()
    library_path = Path(config["LIBRARY_PATH"]).expanduser()
    db_path = library_path / "discogs_collection.db"

    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Run 'python3 migrate_to_database.py' first to create the database")
        return

    db = DiscogsDatabase(db_path)

    # Show statistics by default
    show_statistics(db)

    # Enter interactive mode
    interactive_mode(db)

    db.close()
    logger.info("\nGoodbye!")


if __name__ == "__main__":
    main()
