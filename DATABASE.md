# SQLite Database Integration

## Overview

The Discogs Record Label Generator now uses a **SQLite database** to store and query your music collection metadata. This replaces the previous JSON-only approach while still keeping audio files and analysis on disk.

## Benefits

- **Fast Queries**: Search your entire collection instantly
- **Powerful Filters**: Find releases by artist, label, year, genre, etc.
- **No Server Required**: SQLite is file-based and built into Python
- **Expandable**: Easily add new tables and columns as needed
- **Statistics**: Get insights into your collection
- **Backwards Compatible**: JSON files are still created alongside database

## Database Location

The database file is stored in your library folder:
```
$LIBRARY_PATH/discogs_collection.db
```

## Database Schema

### Core Tables

**releases** - Main release information
- release_id (PRIMARY KEY)
- title, year, timestamp
- formats (JSON), videos (JSON)
- release_folder (path to files)

**tracks** - Individual tracks
- track_id, release_id, position
- title, duration, artist

**artists** - Unique artist names
- artist_id, name

**labels** - Record labels
- label_id, name

**genres** - Music genres
- genre_id, name

### Relationship Tables

**release_artists** - Links releases to artists (many-to-many)

**release_labels** - Links releases to labels with catalog numbers (many-to-many)

**release_genres** - Links releases to genres (many-to-many)

### Additional Tables

**youtube_matches** - YouTube video matches for tracks
- video_url, video_title, video_duration
- confidence_score

**audio_analysis** - Audio analysis results
- bpm, key
- has_waveform, has_spectrogram, has_chromagram
- analysis_file (path to JSON)

## Usage

### 1. Migrate Existing Data

If you already have releases in JSON format, migrate them:

```bash
python3 migrate_to_database.py
```

This will:
- Scan all `metadata.json` files
- Import releases, tracks, artists, labels, genres
- Import YouTube matches (`yt_matches.json`)
- Import audio analysis (`.json` analysis files)

### 2. Query Your Collection

Use the interactive query tool:

```bash
python3 query_database.py
```

Commands:
```
stats                  - Show collection statistics
artist <name>          - Search by artist (e.g., "artist radiohead")
label <name>           - Search by label (e.g., "label warp")
year <year>            - Show releases from year (e.g., "year 1997")
release <id>           - Show release details (e.g., "release 12345")
quit                   - Exit
```

### 3. Programmatic Access

Use the database in your Python code:

```python
from database import DiscogsDatabase
from pathlib import Path

# Initialize
db = DiscogsDatabase(Path("~/music/discogs_collection.db"))

# Get statistics
stats = db.get_statistics()
print(f"Total releases: {stats['total_releases']}")

# Search by artist
releases = db.search_releases_by_artist("Pink Floyd")
for release in releases:
    print(f"{release['year']} - {release['title']}")

# Get full release details
release = db.get_release(12345)
print(f"Title: {release['title']}")
for track in release['tracklist']:
    print(f"  {track['position']}. {track['title']}")

# Close connection
db.close()
```

## New Releases

When you run `main.py` with the new code:
- Metadata is saved to both JSON **and** database
- YouTube matches are saved to database automatically
- Audio analysis can be saved to database (optional)

## Expanding the Database

### Add New Columns

```python
# Add a column to the releases table
cursor.execute("ALTER TABLE releases ADD COLUMN rating INTEGER")
```

### Add New Tables

```python
# Create a new table for playlists
cursor.execute("""
    CREATE TABLE playlists (
        playlist_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
```

### Add Indexes for Performance

```python
# Speed up searches by title
cursor.execute("CREATE INDEX idx_releases_title ON releases(title)")
```

## Example Queries

### Find all vinyl releases from the 1970s
```python
cursor.execute("""
    SELECT * FROM releases
    WHERE year >= 1970 AND year < 1980
    AND formats LIKE '%Vinyl%'
    ORDER BY year
""")
```

### Find all tracks with BPM > 140
```python
cursor.execute("""
    SELECT t.title, r.title as release, a.bpm
    FROM tracks t
    JOIN releases r ON t.release_id = r.release_id
    JOIN audio_analysis a ON t.track_id = a.track_id
    WHERE a.bpm > 140
    ORDER BY a.bpm DESC
""")
```

### Find most prolific artists
```python
cursor.execute("""
    SELECT a.name, COUNT(*) as release_count
    FROM artists a
    JOIN release_artists ra ON a.artist_id = ra.artist_id
    GROUP BY a.artist_id
    ORDER BY release_count DESC
    LIMIT 10
""")
```

## Technical Details

- **Database Engine**: SQLite 3
- **Python Module**: `sqlite3` (built-in)
- **File Format**: Single `.db` file
- **Concurrency**: Multiple readers, single writer
- **Size**: Minimal overhead (~100KB for 1000 releases)
- **Backup**: Simply copy the `.db` file

## Troubleshooting

### Database doesn't exist
Run the migration script first: `python3 migrate_to_database.py`

### Database is locked
Close other programs accessing the database file

### Corrupted database
SQLite is very robust, but if needed:
```bash
sqlite3 discogs_collection.db ".recover" > recovered.sql
sqlite3 new_discogs_collection.db < recovered.sql
```

## Future Enhancements

Possible additions:
- Playlist management
- Listening history tracking
- Custom tags and ratings
- Advanced similarity search using audio features
- Integration with music streaming services
- Export to different formats (CSV, Excel, etc.)
