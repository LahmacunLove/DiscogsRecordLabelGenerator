#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite database module for Discogs Record Label Generator

Provides structured storage for releases, tracks, artists, labels, and analysis data.
Replaces JSON file-based storage with queryable database while keeping audio files on disk.

Created on 2025-01-22
@author: ffx
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from logger import logger


class DiscogsDatabase:
    """SQLite database manager for Discogs collection"""

    def __init__(self, db_path: Path):
        """
        Initialize database connection and create schema if needed

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._create_schema()
        logger.info(f"Database initialized at {self.db_path}")

    def _create_schema(self):
        """Create all database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Releases table - main release information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                release_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                year INTEGER,
                timestamp TEXT,
                formats TEXT,
                release_folder TEXT,
                videos TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Artists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artists (
                artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Labels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                label_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Genres table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Tracks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                release_id INTEGER NOT NULL,
                position TEXT NOT NULL,
                title TEXT NOT NULL,
                duration TEXT,
                artist TEXT,
                FOREIGN KEY (release_id) REFERENCES releases(release_id) ON DELETE CASCADE,
                UNIQUE(release_id, position)
            )
        """)

        # YouTube matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS youtube_matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                video_url TEXT,
                video_title TEXT,
                video_duration INTEGER,
                confidence_score REAL,
                FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
            )
        """)

        # Audio analysis table (for BPM, key, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_analysis (
                analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                bpm REAL,
                key TEXT,
                has_waveform BOOLEAN DEFAULT 0,
                has_spectrogram BOOLEAN DEFAULT 0,
                has_chromagram BOOLEAN DEFAULT 0,
                analysis_file TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
                UNIQUE(track_id)
            )
        """)

        # Many-to-many: Release Artists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_artists (
                release_id INTEGER NOT NULL,
                artist_id INTEGER NOT NULL,
                PRIMARY KEY (release_id, artist_id),
                FOREIGN KEY (release_id) REFERENCES releases(release_id) ON DELETE CASCADE,
                FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
            )
        """)

        # Many-to-many: Release Labels
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_labels (
                release_id INTEGER NOT NULL,
                label_id INTEGER NOT NULL,
                catalog_number TEXT,
                PRIMARY KEY (release_id, label_id),
                FOREIGN KEY (release_id) REFERENCES releases(release_id) ON DELETE CASCADE,
                FOREIGN KEY (label_id) REFERENCES labels(label_id) ON DELETE CASCADE
            )
        """)

        # Many-to-many: Release Genres
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_genres (
                release_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,
                PRIMARY KEY (release_id, genre_id),
                FOREIGN KEY (release_id) REFERENCES releases(release_id) ON DELETE CASCADE,
                FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
            )
        """)

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_releases_year ON releases(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracks_release ON tracks(release_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_youtube_track ON youtube_matches(track_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_track ON audio_analysis(track_id)")

        self.conn.commit()
        logger.debug("Database schema created/verified")

    def _get_or_create_artist(self, artist_name: str) -> int:
        """Get artist ID or create new artist if doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT artist_id FROM artists WHERE name = ?", (artist_name,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute("INSERT INTO artists (name) VALUES (?)", (artist_name,))
        self.conn.commit()
        return cursor.lastrowid

    def _get_or_create_label(self, label_name: str) -> int:
        """Get label ID or create new label if doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT label_id FROM labels WHERE name = ?", (label_name,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute("INSERT INTO labels (name) VALUES (?)", (label_name,))
        self.conn.commit()
        return cursor.lastrowid

    def _get_or_create_genre(self, genre_name: str) -> int:
        """Get genre ID or create new genre if doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT genre_id FROM genres WHERE name = ?", (genre_name,))
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute("INSERT INTO genres (name) VALUES (?)", (genre_name,))
        self.conn.commit()
        return cursor.lastrowid

    def save_release(self, metadata: Dict) -> bool:
        """
        Save or update a release with all related data

        Args:
            metadata: Release metadata dictionary (same format as current JSON)

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            release_id = metadata.get('release_id') or metadata.get('id')

            if not release_id:
                logger.error("No release_id found in metadata")
                return False

            # Insert or replace release
            cursor.execute("""
                INSERT OR REPLACE INTO releases (
                    release_id, title, year, timestamp, formats,
                    release_folder, videos, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                release_id,
                metadata.get('title', ''),
                metadata.get('year'),
                metadata.get('timestamp', ''),
                json.dumps(metadata.get('formats', {})),
                metadata.get('release_folder', ''),
                json.dumps(metadata.get('videos', [])),
                datetime.now().isoformat()
            ))

            # Handle artists
            for artist_name in metadata.get('artist', []):
                artist_id = self._get_or_create_artist(artist_name)
                cursor.execute("""
                    INSERT OR IGNORE INTO release_artists (release_id, artist_id)
                    VALUES (?, ?)
                """, (release_id, artist_id))

            # Handle labels with catalog numbers
            labels = metadata.get('label', [])
            catalog_numbers = metadata.get('catalog_numbers', [])
            for i, label_name in enumerate(labels):
                label_id = self._get_or_create_label(label_name)
                catno = catalog_numbers[i] if i < len(catalog_numbers) else None
                cursor.execute("""
                    INSERT OR REPLACE INTO release_labels (release_id, label_id, catalog_number)
                    VALUES (?, ?, ?)
                """, (release_id, label_id, catno))

            # Handle genres
            for genre_name in metadata.get('genres', []):
                genre_id = self._get_or_create_genre(genre_name)
                cursor.execute("""
                    INSERT OR IGNORE INTO release_genres (release_id, genre_id)
                    VALUES (?, ?)
                """, (release_id, genre_id))

            # Handle tracks
            for track in metadata.get('tracklist', []):
                cursor.execute("""
                    INSERT OR REPLACE INTO tracks (
                        release_id, position, title, duration, artist
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    release_id,
                    track.get('position', ''),
                    track.get('title', ''),
                    track.get('duration', ''),
                    track.get('artist', '')
                ))

            self.conn.commit()
            logger.success(f"Release {release_id} saved to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save release to database: {e}")
            self.conn.rollback()
            return False

    def get_release(self, release_id: int) -> Optional[Dict]:
        """
        Retrieve complete release metadata from database

        Args:
            release_id: Discogs release ID

        Returns:
            Dictionary with release metadata or None if not found
        """
        cursor = self.conn.cursor()

        # Get main release data
        cursor.execute("SELECT * FROM releases WHERE release_id = ?", (release_id,))
        release_row = cursor.fetchone()

        if not release_row:
            return None

        # Convert to dict
        release = dict(release_row)
        release['formats'] = json.loads(release['formats']) if release['formats'] else {}
        release['videos'] = json.loads(release['videos']) if release['videos'] else []

        # Get artists
        cursor.execute("""
            SELECT a.name FROM artists a
            JOIN release_artists ra ON a.artist_id = ra.artist_id
            WHERE ra.release_id = ?
        """, (release_id,))
        release['artist'] = [row[0] for row in cursor.fetchall()]

        # Get labels and catalog numbers
        cursor.execute("""
            SELECT l.name, rl.catalog_number FROM labels l
            JOIN release_labels rl ON l.label_id = rl.label_id
            WHERE rl.release_id = ?
        """, (release_id,))
        labels_data = cursor.fetchall()
        release['label'] = [row[0] for row in labels_data]
        release['catalog_numbers'] = [row[1] for row in labels_data if row[1]]

        # Get genres
        cursor.execute("""
            SELECT g.name FROM genres g
            JOIN release_genres rg ON g.genre_id = rg.genre_id
            WHERE rg.release_id = ?
        """, (release_id,))
        release['genres'] = [row[0] for row in cursor.fetchall()]

        # Get tracks
        cursor.execute("""
            SELECT position, title, duration, artist
            FROM tracks WHERE release_id = ?
            ORDER BY position
        """, (release_id,))
        release['tracklist'] = [
            {
                'position': row[0],
                'title': row[1],
                'duration': row[2],
                'artist': row[3]
            }
            for row in cursor.fetchall()
        ]

        return release

    def get_all_release_ids(self) -> List[int]:
        """Get list of all release IDs in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT release_id FROM releases ORDER BY release_id")
        return [row[0] for row in cursor.fetchall()]

    def release_exists(self, release_id: int) -> bool:
        """Check if release exists in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM releases WHERE release_id = ? LIMIT 1", (release_id,))
        return cursor.fetchone() is not None

    def delete_release(self, release_id: int) -> bool:
        """Delete release and all related data (cascades automatically)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM releases WHERE release_id = ?", (release_id,))
            self.conn.commit()
            logger.info(f"Release {release_id} deleted from database")
            return True
        except Exception as e:
            logger.error(f"Failed to delete release {release_id}: {e}")
            return False

    def search_releases_by_artist(self, artist_name: str) -> List[Dict]:
        """Search releases by artist name (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.* FROM releases r
            JOIN release_artists ra ON r.release_id = ra.release_id
            JOIN artists a ON ra.artist_id = a.artist_id
            WHERE a.name LIKE ?
            ORDER BY r.year DESC
        """, (f"%{artist_name}%",))

        return [dict(row) for row in cursor.fetchall()]

    def search_releases_by_label(self, label_name: str) -> List[Dict]:
        """Search releases by label name (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.* FROM releases r
            JOIN release_labels rl ON r.release_id = rl.release_id
            JOIN labels l ON rl.label_id = l.label_id
            WHERE l.name LIKE ?
            ORDER BY r.year DESC
        """, (f"%{label_name}%",))

        return [dict(row) for row in cursor.fetchall()]

    def search_releases_by_year(self, year: int) -> List[Dict]:
        """Get all releases from a specific year"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM releases
            WHERE year = ?
            ORDER BY title
        """, (year,))

        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total releases
        cursor.execute("SELECT COUNT(*) FROM releases")
        stats['total_releases'] = cursor.fetchone()[0]

        # Total tracks
        cursor.execute("SELECT COUNT(*) FROM tracks")
        stats['total_tracks'] = cursor.fetchone()[0]

        # Total artists
        cursor.execute("SELECT COUNT(*) FROM artists")
        stats['total_artists'] = cursor.fetchone()[0]

        # Total labels
        cursor.execute("SELECT COUNT(*) FROM labels")
        stats['total_labels'] = cursor.fetchone()[0]

        # Releases by decade
        cursor.execute("""
            SELECT (year / 10) * 10 as decade, COUNT(*) as count
            FROM releases
            WHERE year IS NOT NULL
            GROUP BY decade
            ORDER BY decade DESC
        """)
        stats['by_decade'] = {f"{row[0]}s": row[1] for row in cursor.fetchall()}

        return stats

    def save_youtube_matches(self, release_id: int, matches: List[Dict]) -> bool:
        """
        Save YouTube matches for a release

        Args:
            release_id: Discogs release ID
            matches: List of YouTube match dictionaries

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()

            for match in matches:
                track_position = match.get('track_position', '')
                youtube_match = match.get('youtube_match', {})

                if not track_position or not youtube_match:
                    continue

                # Get track_id
                cursor.execute("""
                    SELECT track_id FROM tracks
                    WHERE release_id = ? AND position = ?
                """, (release_id, track_position))

                track_row = cursor.fetchone()
                if not track_row:
                    logger.warning(f"Track not found for position {track_position}")
                    continue

                track_id = track_row[0]

                # Insert YouTube match
                cursor.execute("""
                    INSERT OR REPLACE INTO youtube_matches (
                        track_id, video_url, video_title, video_duration, confidence_score
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    track_id,
                    youtube_match.get('url', ''),
                    youtube_match.get('title', ''),
                    youtube_match.get('duration'),
                    match.get('confidence_score', 0.0)
                ))

            self.conn.commit()
            logger.debug(f"YouTube matches saved for release {release_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save YouTube matches: {e}")
            self.conn.rollback()
            return False

    def save_audio_analysis(self, release_id: int, track_position: str,
                           analysis_data: Dict) -> bool:
        """
        Save audio analysis data for a track

        Args:
            release_id: Discogs release ID
            track_position: Track position (e.g., "A1", "1")
            analysis_data: Dictionary with BPM, key, file paths, etc.

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()

            # Get track_id
            cursor.execute("""
                SELECT track_id FROM tracks
                WHERE release_id = ? AND position = ?
            """, (release_id, track_position))

            track_row = cursor.fetchone()
            if not track_row:
                logger.warning(f"Track not found: {release_id} - {track_position}")
                return False

            track_id = track_row[0]

            # Insert or update analysis
            cursor.execute("""
                INSERT OR REPLACE INTO audio_analysis (
                    track_id, bpm, key, has_waveform, has_spectrogram,
                    has_chromagram, analysis_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                track_id,
                analysis_data.get('bpm'),
                analysis_data.get('key'),
                analysis_data.get('has_waveform', False),
                analysis_data.get('has_spectrogram', False),
                analysis_data.get('has_chromagram', False),
                analysis_data.get('analysis_file', '')
            ))

            self.conn.commit()
            logger.debug(f"Audio analysis saved for track {track_position}")
            return True

        except Exception as e:
            logger.error(f"Failed to save audio analysis: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-close connection"""
        self.close()
