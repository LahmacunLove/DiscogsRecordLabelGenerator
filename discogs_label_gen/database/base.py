"""
Abstract database interface

This defines the contract that all database backends must implement.
Allows switching between SQLite, PostgreSQL, MySQL, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..core.models import Release, Track, Artist, Label, Genre, YouTubeMatch, AudioAnalysis


class DatabaseBackend(ABC):
    """Abstract base class for database backends"""

    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close database connection"""
        pass

    @abstractmethod
    def initialize_schema(self) -> bool:
        """Create all necessary tables and indexes"""
        pass

    # ==================== Release Operations ====================

    @abstractmethod
    def save_release(self, release: Release) -> bool:
        """
        Save or update a release

        Args:
            release: Release object to save

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_release(self, release_id: int) -> Optional[Release]:
        """
        Get a release by ID

        Args:
            release_id: Discogs release ID

        Returns:
            Release object or None if not found
        """
        pass

    @abstractmethod
    def delete_release(self, release_id: int) -> bool:
        """Delete a release and all related data"""
        pass

    @abstractmethod
    def release_exists(self, release_id: int) -> bool:
        """Check if a release exists in database"""
        pass

    @abstractmethod
    def get_all_release_ids(self) -> List[int]:
        """Get list of all release IDs"""
        pass

    # ==================== Search Operations ====================

    @abstractmethod
    def search_releases_by_artist(self, artist_name: str) -> List[Release]:
        """Search releases by artist name (case-insensitive)"""
        pass

    @abstractmethod
    def search_releases_by_label(self, label_name: str) -> List[Release]:
        """Search releases by label name (case-insensitive)"""
        pass

    @abstractmethod
    def search_releases_by_year(self, year: int) -> List[Release]:
        """Get all releases from a specific year"""
        pass

    @abstractmethod
    def search_releases_by_genre(self, genre_name: str) -> List[Release]:
        """Search releases by genre (case-insensitive)"""
        pass

    # ==================== Download Status Operations ====================

    @abstractmethod
    def get_releases_needing_covers(self) -> List[int]:
        """Get release IDs that need cover downloads"""
        pass

    @abstractmethod
    def get_releases_needing_youtube(self) -> List[int]:
        """Get release IDs that need YouTube matching"""
        pass

    @abstractmethod
    def get_releases_needing_audio(self) -> List[int]:
        """Get release IDs that need audio downloads"""
        pass

    @abstractmethod
    def mark_covers_downloaded(self, release_id: int) -> bool:
        """Mark that cover images have been downloaded"""
        pass

    @abstractmethod
    def mark_youtube_matched(self, release_id: int) -> bool:
        """Mark that YouTube videos have been matched"""
        pass

    @abstractmethod
    def mark_audio_downloaded(self, release_id: int) -> bool:
        """Mark that audio files have been downloaded"""
        pass

    # ==================== YouTube Match Operations ====================

    @abstractmethod
    def save_youtube_match(self, match: YouTubeMatch) -> bool:
        """Save a YouTube match for a track"""
        pass

    @abstractmethod
    def get_youtube_matches_for_release(self, release_id: int) -> List[YouTubeMatch]:
        """Get all YouTube matches for a release"""
        pass

    # ==================== Audio Analysis Operations ====================

    @abstractmethod
    def save_audio_analysis(self, analysis: AudioAnalysis) -> bool:
        """Save audio analysis data for a track"""
        pass

    @abstractmethod
    def get_audio_analysis(self, track_id: int) -> Optional[AudioAnalysis]:
        """Get audio analysis for a track"""
        pass

    # ==================== Statistics ====================

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Dictionary with stats like total_releases, total_tracks, etc.
        """
        pass

    # ==================== Context Manager ====================

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
