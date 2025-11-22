#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite database backend implementation

Implements the DatabaseBackend interface using SQLite for storage.
Provides persistence for Discogs releases, tracks, and enrichment data.

Created on 2025-01-22
@author: ffx
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.models import Release, Track, Artist, Label, Genre, YouTubeMatch, AudioAnalysis
from .base import DatabaseBackend


class SQLiteBackend(DatabaseBackend):
    """SQLite implementation of database backend"""

    def __init__(self, db_path: Path):
        """
        Initialize SQLite database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            return False

    def disconnect(self) -> bool:
        """Close database connection"""
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
            return True
        except Exception as e:
            print(f"Failed to close database: {e}")
            return False

    def initialize_schema(self) -> bool:
        """Create all necessary tables and indexes"""
        try:
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
                    discogs_synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    covers_downloaded BOOLEAN DEFAULT 0,
                    youtube_matched BOOLEAN DEFAULT 0,
                    audio_downloaded BOOLEAN DEFAULT 0,
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

            # Audio analysis table
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
            return True

        except Exception as e:
            print(f"Failed to create schema: {e}")
            return False

    # ==================== Helper Methods ====================

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

    # ==================== Release Operations ====================

    def save_release(self, release: Release) -> bool:
        """Save or update a release"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()

            # Insert or replace release
            cursor.execute("""
                INSERT OR REPLACE INTO releases (
                    release_id, title, year, timestamp, formats,
                    release_folder, videos, discogs_synced_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                release.release_id,
                release.title,
                release.year,
                release.timestamp,
                json.dumps(release.formats),
                release.release_folder,
                json.dumps(release.videos),
                now,
                now
            ))

            # Handle artists
            for artist in release.artists:
                artist_id = self._get_or_create_artist(artist.name)
                cursor.execute("""
                    INSERT OR IGNORE INTO release_artists (release_id, artist_id)
                    VALUES (?, ?)
                """, (release.release_id, artist_id))

            # Handle labels
            for label in release.labels:
                label_id = self._get_or_create_label(label.name)
                cursor.execute("""
                    INSERT OR REPLACE INTO release_labels (release_id, label_id, catalog_number)
                    VALUES (?, ?, ?)
                """, (release.release_id, label_id, label.catalog_number))

            # Handle genres
            for genre in release.genres:
                genre_id = self._get_or_create_genre(genre.name)
                cursor.execute("""
                    INSERT OR IGNORE INTO release_genres (release_id, genre_id)
                    VALUES (?, ?)
                """, (release.release_id, genre_id))

            # Handle tracks
            for track in release.tracks:
                cursor.execute("""
                    INSERT OR REPLACE INTO tracks (
                        release_id, position, title, duration, artist
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    release.release_id,
                    track.position,
                    track.title,
                    track.duration,
                    track.artist
                ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Failed to save release: {e}")
            self.conn.rollback()
            return False

    def get_release(self, release_id: int) -> Optional[Release]:
        """Get a release by ID"""
        cursor = self.conn.cursor()

        # Get main release data
        cursor.execute("SELECT * FROM releases WHERE release_id = ?", (release_id,))
        release_row = cursor.fetchone()

        if not release_row:
            return None

        # Create Release object
        release = Release(
            release_id=release_row['release_id'],
            title=release_row['title'],
            year=release_row['year'],
            timestamp=release_row['timestamp'],
            release_folder=release_row['release_folder'],
            formats=json.loads(release_row['formats']) if release_row['formats'] else {},
            videos=json.loads(release_row['videos']) if release_row['videos'] else [],
            covers_downloaded=bool(release_row['covers_downloaded']),
            youtube_matched=bool(release_row['youtube_matched']),
            audio_downloaded=bool(release_row['audio_downloaded'])
        )

        # Get artists
        cursor.execute("""
            SELECT a.artist_id, a.name FROM artists a
            JOIN release_artists ra ON a.artist_id = ra.artist_id
            WHERE ra.release_id = ?
        """, (release_id,))
        release.artists = [Artist(artist_id=row[0], name=row[1]) for row in cursor.fetchall()]

        # Get labels
        cursor.execute("""
            SELECT l.label_id, l.name, rl.catalog_number FROM labels l
            JOIN release_labels rl ON l.label_id = rl.label_id
            WHERE rl.release_id = ?
        """, (release_id,))
        release.labels = [
            Label(label_id=row[0], name=row[1], catalog_number=row[2])
            for row in cursor.fetchall()
        ]

        # Get genres
        cursor.execute("""
            SELECT g.genre_id, g.name FROM genres g
            JOIN release_genres rg ON g.genre_id = rg.genre_id
            WHERE rg.release_id = ?
        """, (release_id,))
        release.genres = [Genre(genre_id=row[0], name=row[1]) for row in cursor.fetchall()]

        # Get tracks
        cursor.execute("""
            SELECT track_id, position, title, duration, artist
            FROM tracks WHERE release_id = ?
            ORDER BY position
        """, (release_id,))
        release.tracks = [
            Track(
                track_id=row[0],
                release_id=release_id,
                position=row[1],
                title=row[2],
                duration=row[3],
                artist=row[4]
            )
            for row in cursor.fetchall()
        ]

        return release

    def delete_release(self, release_id: int) -> bool:
        """Delete a release and all related data"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM releases WHERE release_id = ?", (release_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to delete release: {e}")
            return False

    def release_exists(self, release_id: int) -> bool:
        """Check if a release exists in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM releases WHERE release_id = ? LIMIT 1", (release_id,))
        return cursor.fetchone() is not None

    def get_all_release_ids(self) -> List[int]:
        """Get list of all release IDs"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT release_id FROM releases ORDER BY release_id")
        return [row[0] for row in cursor.fetchall()]

    # ==================== Search Operations ====================

    def search_releases_by_artist(self, artist_name: str) -> List[Release]:
        """Search releases by artist name (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.release_id FROM releases r
            JOIN release_artists ra ON r.release_id = ra.release_id
            JOIN artists a ON ra.artist_id = a.artist_id
            WHERE a.name LIKE ?
            ORDER BY r.year DESC
        """, (f"%{artist_name}%",))

        release_ids = [row[0] for row in cursor.fetchall()]
        return [self.get_release(rid) for rid in release_ids if self.get_release(rid)]

    def search_releases_by_label(self, label_name: str) -> List[Release]:
        """Search releases by label name (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.release_id FROM releases r
            JOIN release_labels rl ON r.release_id = rl.release_id
            JOIN labels l ON rl.label_id = l.label_id
            WHERE l.name LIKE ?
            ORDER BY r.year DESC
        """, (f"%{label_name}%",))

        release_ids = [row[0] for row in cursor.fetchall()]
        return [self.get_release(rid) for rid in release_ids if self.get_release(rid)]

    def search_releases_by_year(self, year: int) -> List[Release]:
        """Get all releases from a specific year"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT release_id FROM releases
            WHERE year = ?
            ORDER BY title
        """, (year,))

        release_ids = [row[0] for row in cursor.fetchall()]
        return [self.get_release(rid) for rid in release_ids if self.get_release(rid)]

    def search_releases_by_genre(self, genre_name: str) -> List[Release]:
        """Search releases by genre (case-insensitive)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT r.release_id FROM releases r
            JOIN release_genres rg ON r.release_id = rg.release_id
            JOIN genres g ON rg.genre_id = g.genre_id
            WHERE g.name LIKE ?
            ORDER BY r.year DESC
        """, (f"%{genre_name}%",))

        release_ids = [row[0] for row in cursor.fetchall()]
        return [self.get_release(rid) for rid in release_ids if self.get_release(rid)]

    # ==================== Download Status Operations ====================

    def get_releases_needing_covers(self) -> List[int]:
        """Get release IDs that need cover downloads"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT release_id FROM releases
            WHERE covers_downloaded = 0
            ORDER BY release_id
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_releases_needing_youtube(self) -> List[int]:
        """Get release IDs that need YouTube matching"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT release_id FROM releases
            WHERE youtube_matched = 0
            ORDER BY release_id
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_releases_needing_audio(self) -> List[int]:
        """Get release IDs that need audio downloads"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT release_id FROM releases
            WHERE audio_downloaded = 0 AND youtube_matched = 1
            ORDER BY release_id
        """)
        return [row[0] for row in cursor.fetchall()]

    def mark_covers_downloaded(self, release_id: int) -> bool:
        """Mark that cover images have been downloaded"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE releases
                SET covers_downloaded = 1, updated_at = ?
                WHERE release_id = ?
            """, (datetime.now().isoformat(), release_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to mark covers downloaded: {e}")
            return False

    def mark_youtube_matched(self, release_id: int) -> bool:
        """Mark that YouTube videos have been matched"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE releases
                SET youtube_matched = 1, updated_at = ?
                WHERE release_id = ?
            """, (datetime.now().isoformat(), release_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to mark YouTube matched: {e}")
            return False

    def mark_audio_downloaded(self, release_id: int) -> bool:
        """Mark that audio files have been downloaded"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE releases
                SET audio_downloaded = 1, updated_at = ?
                WHERE release_id = ?
            """, (datetime.now().isoformat(), release_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to mark audio downloaded: {e}")
            return False

    # ==================== YouTube Match Operations ====================

    def save_youtube_match(self, match: YouTubeMatch) -> bool:
        """Save a YouTube match for a track"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO youtube_matches (
                    track_id, video_url, video_title, video_duration, confidence_score
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                match.track_id,
                match.video_url,
                match.video_title,
                match.video_duration,
                match.confidence_score
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save YouTube match: {e}")
            return False

    def get_youtube_matches_for_release(self, release_id: int) -> List[YouTubeMatch]:
        """Get all YouTube matches for a release"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ym.match_id, ym.track_id, ym.video_url, ym.video_title,
                   ym.video_duration, ym.confidence_score
            FROM youtube_matches ym
            JOIN tracks t ON ym.track_id = t.track_id
            WHERE t.release_id = ?
            ORDER BY t.position
        """, (release_id,))

        return [
            YouTubeMatch(
                match_id=row[0],
                track_id=row[1],
                video_url=row[2],
                video_title=row[3],
                video_duration=row[4],
                confidence_score=row[5]
            )
            for row in cursor.fetchall()
        ]

    # ==================== Audio Analysis Operations ====================

    def save_audio_analysis(self, analysis: AudioAnalysis) -> bool:
        """Save audio analysis data for a track"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO audio_analysis (
                    track_id, bpm, key, has_waveform, has_spectrogram,
                    has_chromagram, analysis_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.track_id,
                analysis.bpm,
                analysis.key,
                analysis.has_waveform,
                analysis.has_spectrogram,
                analysis.has_chromagram,
                analysis.analysis_file
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save audio analysis: {e}")
            return False

    def get_audio_analysis(self, track_id: int) -> Optional[AudioAnalysis]:
        """Get audio analysis for a track"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT analysis_id, track_id, bpm, key, has_waveform,
                   has_spectrogram, has_chromagram, analysis_file, created_at
            FROM audio_analysis
            WHERE track_id = ?
        """, (track_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return AudioAnalysis(
            analysis_id=row[0],
            track_id=row[1],
            bpm=row[2],
            key=row[3],
            has_waveform=bool(row[4]),
            has_spectrogram=bool(row[5]),
            has_chromagram=bool(row[6]),
            analysis_file=row[7],
            created_at=datetime.fromisoformat(row[8]) if row[8] else None
        )

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
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

        # Download progress
        cursor.execute("SELECT COUNT(*) FROM releases WHERE covers_downloaded = 1")
        stats['covers_downloaded'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM releases WHERE youtube_matched = 1")
        stats['youtube_matched'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM releases WHERE audio_downloaded = 1")
        stats['audio_downloaded'] = cursor.fetchone()[0]

        return stats
