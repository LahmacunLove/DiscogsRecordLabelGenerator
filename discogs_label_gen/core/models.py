"""
Data models for Discogs Record Label Generator

These models represent the core entities in our domain.
They are independent of database implementation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DownloadStatus(Enum):
    """Download status for release assets"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Artist:
    """Represents a music artist"""
    artist_id: Optional[int] = None
    name: str = ""


@dataclass
class Label:
    """Represents a record label"""
    label_id: Optional[int] = None
    name: str = ""
    catalog_number: Optional[str] = None


@dataclass
class Genre:
    """Represents a music genre"""
    genre_id: Optional[int] = None
    name: str = ""


@dataclass
class Track:
    """Represents a track on a release"""
    track_id: Optional[int] = None
    release_id: int = 0
    position: str = ""
    title: str = ""
    duration: Optional[str] = None
    artist: Optional[str] = None  # Track-specific artist (if different from release)

    # Enrichment data
    youtube_video_url: Optional[str] = None
    youtube_video_title: Optional[str] = None
    youtube_duration: Optional[int] = None
    audio_file_path: Optional[str] = None

    # Analysis data
    bpm: Optional[float] = None
    key: Optional[str] = None
    has_waveform: bool = False
    has_spectrogram: bool = False
    analysis_file_path: Optional[str] = None


@dataclass
class Release:
    """Represents a music release from Discogs"""
    # Discogs metadata (source of truth)
    release_id: int = 0
    title: str = ""
    year: Optional[int] = None
    artists: List[Artist] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    genres: List[Genre] = field(default_factory=list)
    formats: Dict[str, Any] = field(default_factory=dict)
    videos: List[str] = field(default_factory=list)
    tracks: List[Track] = field(default_factory=list)

    # Collection metadata
    timestamp: Optional[str] = None  # When added to Discogs collection
    release_folder: Optional[str] = None

    # Sync/Download status
    discogs_synced_at: Optional[datetime] = None
    covers_downloaded: bool = False
    youtube_matched: bool = False
    audio_downloaded: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert release to dictionary (for JSON serialization)"""
        return {
            'release_id': self.release_id,
            'title': self.title,
            'year': self.year,
            'artist': [a.name for a in self.artists],
            'label': [l.name for l in self.labels],
            'catalog_numbers': [l.catalog_number for l in self.labels if l.catalog_number],
            'genres': [g.name for g in self.genres],
            'formats': self.formats,
            'videos': self.videos,
            'timestamp': self.timestamp,
            'release_folder': self.release_folder,
            'tracklist': [
                {
                    'position': t.position,
                    'title': t.title,
                    'duration': t.duration,
                    'artist': t.artist
                }
                for t in self.tracks
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Release':
        """Create Release from dictionary (from JSON or database)"""
        release = cls(
            release_id=data.get('release_id', 0),
            title=data.get('title', ''),
            year=data.get('year'),
            timestamp=data.get('timestamp'),
            release_folder=data.get('release_folder'),
            formats=data.get('formats', {}),
            videos=data.get('videos', []),
        )

        # Parse artists
        for artist_name in data.get('artist', []):
            release.artists.append(Artist(name=artist_name))

        # Parse labels
        label_names = data.get('label', [])
        catalog_numbers = data.get('catalog_numbers', [])
        for i, label_name in enumerate(label_names):
            catno = catalog_numbers[i] if i < len(catalog_numbers) else None
            release.labels.append(Label(name=label_name, catalog_number=catno))

        # Parse genres
        for genre_name in data.get('genres', []):
            release.genres.append(Genre(name=genre_name))

        # Parse tracks
        for track_data in data.get('tracklist', []):
            release.tracks.append(Track(
                release_id=release.release_id,
                position=track_data.get('position', ''),
                title=track_data.get('title', ''),
                duration=track_data.get('duration'),
                artist=track_data.get('artist')
            ))

        return release


@dataclass
class YouTubeMatch:
    """Represents a YouTube video match for a track"""
    match_id: Optional[int] = None
    track_id: int = 0
    video_url: str = ""
    video_title: str = ""
    video_duration: Optional[int] = None
    confidence_score: float = 0.0


@dataclass
class AudioAnalysis:
    """Represents audio analysis data for a track"""
    analysis_id: Optional[int] = None
    track_id: int = 0
    bpm: Optional[float] = None
    key: Optional[str] = None
    has_waveform: bool = False
    has_spectrogram: bool = False
    has_chromagram: bool = False
    analysis_file: Optional[str] = None
    created_at: Optional[datetime] = None
