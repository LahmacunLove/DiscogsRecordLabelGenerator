# Two-Phase Workflow

## Overview

The Discogs sync process is now split into two independent phases for better data integrity and workflow control:

1. **Phase 1: Metadata Sync** - Sync pure Discogs metadata to database
2. **Phase 2: Asset Download** - Download covers, match YouTube, download audio

## Why Two Phases?

### Data Integrity
- **Pure Discogs metadata** is never modified after initial sync
- **Enrichment data** (YouTube, Bandcamp) stored separately
- Clear separation between source of truth (Discogs) and enhancements

### Flexibility
- Sync metadata quickly without waiting for downloads
- Retry failed downloads independently
- Download assets for specific releases only
- Track progress for each phase separately

### Efficiency
- Metadata sync is fast (API calls only, no downloads)
- Asset downloads can be interrupted and resumed
- Parallel processing possible in each phase

## Phase 1: Metadata Sync

Syncs release metadata from Discogs API to local database.

```bash
# Sync entire collection (metadata only)
python3 main.py --discogs-only

# Sync first 10 releases for testing
python3 main.py --max=10 --discogs-only

# Sync specific release
python3 main.py --release-id=12345 --discogs-only
```

### What Gets Synced:
- Release title, year, artists
- Labels and catalog numbers
- Genres and formats
- Tracklist (position, title, duration)
- Collection timestamp

### Database Storage:
- `releases` table - Core release data
- `artists`, `labels`, `genres` tables - Normalized data
- `tracks` table - Track information
- `discogs_synced_at` timestamp - Last sync time

### What Doesn't Happen:
- ❌ No cover images downloaded
- ❌ No YouTube matching
- ❌ No audio downloads
- ❌ No analysis

## Phase 2: Asset Download

Downloads assets for releases that have been synced.

```bash
# Download all missing assets (covers + YouTube + audio)
python3 download_assets.py

# Download only covers
python3 download_assets.py --covers-only

# Match YouTube videos only
python3 download_assets.py --youtube-only

# Download audio only (requires YouTube matches)
python3 download_assets.py --audio-only

# Process first 5 releases
python3 download_assets.py --max=5
```

### Download Order:

1. **Covers** (`--covers-only`)
   - Primary cover image
   - Additional release images (cover_2.jpg, etc.)
   - Marks `covers_downloaded = 1` in database

2. **YouTube Matching** (`--youtube-only`)
   - Search YouTube for each track
   - Fuzzy matching against track titles
   - Save matches to `yt_matches.json`
   - Store in `youtube_matches` table
   - Marks `youtube_matched = 1` in database

3. **Audio Download** (`--audio-only`)
   - Download audio from YouTube matches
   - Requires YouTube matching first
   - Saves as `.opus` files
   - Marks `audio_downloaded = 1` in database

### Progress Tracking:

Each release tracks its download status:
- `covers_downloaded` - Boolean flag
- `youtube_matched` - Boolean flag
- `audio_downloaded` - Boolean flag

View progress:
```bash
python3 query_database.py
# Shows: Covers: 10/100 (10%), YouTube: 5/100 (5%), Audio: 3/100 (3%)
```

## Complete Workflow Example

### 1. Initial Sync (Full Collection)

```bash
# Phase 1: Sync all metadata from Discogs
python3 main.py --discogs-only

# Result: 618 releases in database (metadata only)
```

### 2. Download Assets Incrementally

```bash
# Start with covers for first 10
python3 download_assets.py --covers-only --max=10

# Then match YouTube for those same 10
python3 download_assets.py --youtube-only --max=10

# Then download audio
python3 download_assets.py --audio-only --max=10

# Check progress
python3 query_database.py
```

### 3. Process Remaining Releases

```bash
# Download everything for remaining releases
python3 download_assets.py

# Or do it in batches
python3 download_assets.py --max=50
python3 download_assets.py --max=50
# etc...
```

## Database Schema

### Releases Table (Discogs Metadata)
```sql
releases (
    release_id INTEGER PRIMARY KEY,
    title TEXT,
    year INTEGER,
    formats JSON,
    discogs_synced_at TEXT,      -- When Discogs data was synced
    covers_downloaded BOOLEAN,    -- Cover images downloaded?
    youtube_matched BOOLEAN,      -- YouTube videos matched?
    audio_downloaded BOOLEAN,     -- Audio files downloaded?
    ...
)
```

### Enrichment Tables
```sql
youtube_matches (
    match_id INTEGER PRIMARY KEY,
    track_id INTEGER,
    video_url TEXT,
    video_duration INTEGER,
    ...
)

audio_analysis (
    analysis_id INTEGER PRIMARY KEY,
    track_id INTEGER,
    bpm REAL,
    key TEXT,
    ...
)
```

## Querying Your Collection

```bash
# Interactive query mode
python3 query_database.py

# Example queries:
> stats                    # Show collection statistics
> artist radiohead         # Find all Radiohead releases
> label warp              # Find all Warp Records releases
> year 1997               # Show 1997 releases
> release 12345           # Show release details
```

## Data Separation

### Discogs Data (Never Modified)
- Release metadata
- Track information
- Artists, labels, genres
- Only updated when re-syncing from Discogs

### Enrichment Data (Separate)
- YouTube matches (`youtube_matches` table)
- Audio analysis (`audio_analysis` table)
- Cover images (filesystem)
- Audio files (filesystem)

### Benefits:
- Can re-sync Discogs without losing enrichments
- Can re-download assets without re-syncing metadata
- Clear audit trail of data sources
- No conflicts between Discogs and YouTube data

## Migration from Old Workflow

If you have existing releases:

```bash
# Migrate existing JSON files to database
python3 migrate_to_database.py

# Database will import:
# - metadata.json → releases table
# - yt_matches.json → youtube_matches table
# - Analysis files → audio_analysis table
```

## Troubleshooting

### "No releases needing covers"
All releases already have covers downloaded according to database.
To re-download: Manually update database or delete cover files.

### "YouTube matched but no audio"
YouTube matching completed but audio download failed or pending.
Run: `python3 download_assets.py --audio-only`

### Check specific release status
```bash
python3 query_database.py
> release 12345
# Shows complete release info and download status
```

## Advanced Usage

### Selective Re-downloads

```sql
-- Reset cover download status for specific release
UPDATE releases SET covers_downloaded = 0 WHERE release_id = 12345;

-- Reset all YouTube matches
UPDATE releases SET youtube_matched = 0;
```

Then run `python3 download_assets.py` to re-download.

### Custom Queries

```python
from database import DiscogsDatabase
from pathlib import Path

db = DiscogsDatabase(Path("discogs_collection.db"))

# Get all releases from 1990s without YouTube matches
releases = db.conn.execute("""
    SELECT release_id, title, year
    FROM releases
    WHERE year >= 1990 AND year < 2000
    AND youtube_matched = 0
    ORDER BY year
""").fetchall()

for r in releases:
    print(f"{r[1]} ({r[2]})")
```

## Future Enhancements

Possible additions to Phase 2:
- Bandcamp audio matching/download
- Automatic audio analysis (BPM, key detection)
- Waveform generation
- Label generation
- Playlist creation
