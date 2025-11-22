#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compatibility wrapper for old DiscogsDatabase interface

This wrapper provides backward compatibility by exposing the old dictionary-based
API while using the new model-based backend internally. This allows gradual
migration of existing code.

Created on 2025-01-22
@author: ffx
"""

from pathlib import Path
from typing import List, Dict, Optional
from .sqlite_backend import SQLiteBackend
from ..core.models import Release


class DiscogsDatabase:
    """
    Backward-compatible database wrapper

    Maintains the old dictionary-based API while using the new backend.
    This allows existing code to continue working during migration.
    """

    def __init__(self, db_path: Path):
        """Initialize database with backward-compatible interface"""
        self.db_path = Path(db_path)
        self.backend = SQLiteBackend(db_path)
        self.backend.connect()
        self.backend.initialize_schema()

        # For compatibility with context manager usage
        self.conn = self.backend.conn

    def save_release(self, metadata: Dict) -> bool:
        """
        Save release from dictionary (old format)

        Args:
            metadata: Release metadata dictionary

        Returns:
            True if successful
        """
        # Convert dict to Release model
        release = Release.from_dict(metadata)
        return self.backend.save_release(release)

    def get_release(self, release_id: int) -> Optional[Dict]:
        """
        Get release as dictionary (old format)

        Args:
            release_id: Discogs release ID

        Returns:
            Dictionary with release metadata or None
        """
        release = self.backend.get_release(release_id)
        if not release:
            return None

        # Convert Release model to dict
        return release.to_dict()

    def get_all_release_ids(self) -> List[int]:
        """Get list of all release IDs"""
        return self.backend.get_all_release_ids()

    def release_exists(self, release_id: int) -> bool:
        """Check if release exists in database"""
        return self.backend.release_exists(release_id)

    def delete_release(self, release_id: int) -> bool:
        """Delete release and all related data"""
        return self.backend.delete_release(release_id)

    def search_releases_by_artist(self, artist_name: str) -> List[Dict]:
        """Search releases by artist name (returns dicts)"""
        releases = self.backend.search_releases_by_artist(artist_name)
        return [r.to_dict() for r in releases if r]

    def search_releases_by_label(self, label_name: str) -> List[Dict]:
        """Search releases by label name (returns dicts)"""
        releases = self.backend.search_releases_by_label(label_name)
        return [r.to_dict() for r in releases if r]

    def search_releases_by_year(self, year: int) -> List[Dict]:
        """Get all releases from a specific year (returns dicts)"""
        releases = self.backend.search_releases_by_year(year)
        return [r.to_dict() for r in releases if r]

    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        return self.backend.get_statistics()

    def save_youtube_matches(self, release_id: int, matches: List[Dict]) -> bool:
        """
        Save YouTube matches for a release (from old format)

        Args:
            release_id: Discogs release ID
            matches: List of match dictionaries from yt_matches.json

        Returns:
            True if successful
        """
        try:
            cursor = self.backend.conn.cursor()

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

            self.backend.conn.commit()
            return True

        except Exception as e:
            print(f"Failed to save YouTube matches: {e}")
            self.backend.conn.rollback()
            return False

    def save_audio_analysis(self, release_id: int, track_position: str,
                           analysis_data: Dict) -> bool:
        """Save audio analysis data for a track"""
        try:
            cursor = self.backend.conn.cursor()

            # Get track_id
            cursor.execute("""
                SELECT track_id FROM tracks
                WHERE release_id = ? AND position = ?
            """, (release_id, track_position))

            track_row = cursor.fetchone()
            if not track_row:
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

            self.backend.conn.commit()
            return True

        except Exception as e:
            print(f"Failed to save audio analysis: {e}")
            self.backend.conn.rollback()
            return False

    def mark_covers_downloaded(self, release_id: int) -> bool:
        """Mark that cover images have been downloaded"""
        return self.backend.mark_covers_downloaded(release_id)

    def mark_youtube_matched(self, release_id: int) -> bool:
        """Mark that YouTube videos have been matched"""
        return self.backend.mark_youtube_matched(release_id)

    def mark_audio_downloaded(self, release_id: int) -> bool:
        """Mark that audio files have been downloaded"""
        return self.backend.mark_audio_downloaded(release_id)

    def get_releases_needing_covers(self) -> List[int]:
        """Get release IDs that need cover downloads"""
        return self.backend.get_releases_needing_covers()

    def get_releases_needing_youtube(self) -> List[int]:
        """Get release IDs that need YouTube matching"""
        return self.backend.get_releases_needing_youtube()

    def get_releases_needing_audio(self) -> List[int]:
        """Get release IDs that need audio downloads"""
        return self.backend.get_releases_needing_audio()

    def close(self):
        """Close database connection"""
        self.backend.disconnect()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
