# Migration Guide

## Overview

This guide explains the refactoring changes and how to work with the new architecture.

## What Changed?

### Before (Old)
```
src/database.py - 666 lines of SQLite code mixed with business logic
```

### After (New)
```
discogs_label_gen/
  core/models.py          - Domain models (Release, Track, etc.)
  database/base.py        - Abstract database interface
  database/sqlite_backend.py  - SQLite implementation
  database/compat_wrapper.py  - Backward compatibility layer
src/database.py           - Simple re-export (compatibility)
```

## Do Existing Scripts Still Work?

**YES!** All existing code continues to work without any changes:

- ✅ `main.py` - Syncs Discogs collection
- ✅ `download_assets.py` - Downloads covers/YouTube/audio
- ✅ `query_database.py` - Interactive database queries
- ✅ `migrate_to_database.py` - Imports JSON files

## How Does It Work?

The old `src/database.py` now imports from the new package:

```python
# src/database.py
from discogs_label_gen.database.compat_wrapper import DiscogsDatabase
```

The compatibility wrapper converts between:
- **Old format**: Dictionaries (`{'release_id': 123, 'title': 'Album'}`)
- **New format**: Model objects (`Release(release_id=123, title='Album')`)

## Writing New Code

### Option 1: Use New Models (Recommended)

```python
from discogs_label_gen import SQLiteBackend, Release, Artist

backend = SQLiteBackend(Path("db.sqlite"))
backend.connect()
backend.initialize_schema()

# Create a release
release = Release(
    release_id=123456,
    title="OK Computer",
    year=1997
)
release.artists.append(Artist(name="Radiohead"))

# Save it
backend.save_release(release)

# Get it back
release = backend.get_release(123456)
print(f"{release.title} by {release.artists[0].name}")

backend.disconnect()
```

**Benefits:**
- Type safety (IDE autocomplete)
- Clear data structure
- Easy to test
- Cleaner code

### Option 2: Use Old API (Compatible)

```python
from database import DiscogsDatabase

db = DiscogsDatabase(Path("db.sqlite"))

# Old dictionary format still works
metadata = {
    'release_id': 123456,
    'title': 'OK Computer',
    'year': 1997,
    'artist': ['Radiohead']
}

db.save_release(metadata)
retrieved = db.get_release(123456)

db.close()
```

## Migrating Existing Code

### Example: Migrating a Function

**Before:**
```python
def process_release(db, metadata):
    release_id = metadata['release_id']
    title = metadata['title']
    artists = metadata.get('artist', [])

    print(f"Processing {title}")
    db.save_release(metadata)
```

**After:**
```python
def process_release(backend, release):
    print(f"Processing {release.title}")
    backend.save_release(release)
```

### Example: Migrating Data Access

**Before:**
```python
metadata = db.get_release(123)
if metadata:
    for track in metadata['tracklist']:
        print(f"{track['position']}. {track['title']}")
```

**After:**
```python
release = backend.get_release(123)
if release:
    for track in release.tracks:
        print(f"{track.position}. {track.title}")
```

## Testing Your Changes

After migrating code, run tests:

```bash
# Test new backend
python3 tests/test_database_backend.py

# Test with actual data
python3 query_database.py
```

## Future: PostgreSQL Migration

The new architecture makes switching to PostgreSQL easy:

```python
# Just change the backend class
backend = PostgreSQLBackend(
    host="localhost",
    database="discogs",
    user="discogs_user",
    password="secret"
)

# Everything else stays the same!
backend.save_release(release)
release = backend.get_release(123)
```

## Common Patterns

### Pattern 1: Creating Releases

**Old:**
```python
metadata = {
    'release_id': 123,
    'title': 'Album',
    'year': 2020,
    'artist': ['Artist Name'],
    'tracklist': [
        {'position': '1', 'title': 'Track 1'}
    ]
}
db.save_release(metadata)
```

**New:**
```python
release = Release(release_id=123, title='Album', year=2020)
release.artists.append(Artist(name='Artist Name'))
release.tracks.append(Track(
    release_id=123,
    position='1',
    title='Track 1'
))
backend.save_release(release)
```

### Pattern 2: Searching

**Old:**
```python
releases = db.search_releases_by_artist("Radiohead")
for release in releases:
    print(release['title'])  # Dictionary
```

**New:**
```python
releases = backend.search_releases_by_artist("Radiohead")
for release in releases:
    print(release.title)  # Object attribute
```

### Pattern 3: Statistics

Both old and new return the same dictionary:

```python
stats = backend.get_statistics()
# OR
stats = db.get_statistics()

print(f"Total: {stats['total_releases']}")
```

## Backward Compatibility Layer

The compatibility wrapper provides these methods:

| Method | Old Format | New Format |
|--------|-----------|------------|
| `save_release(dict)` | ✅ Dict in | Uses Release internally |
| `get_release(id)` | ✅ Dict out | Converts Release to dict |
| `search_*` | ✅ List of dicts | Converts Release list to dicts |
| `get_statistics()` | ✅ Same format | Same format |

## When to Migrate?

### Migrate Now If:
- Writing new features
- Refactoring existing code
- Adding tests

### Keep Old API If:
- Quick fixes
- Scripts that work fine
- Not touching the code

## Getting Help

- Read `docs/ARCHITECTURE.md` for detailed architecture info
- Check `tests/test_database_backend.py` for examples
- Look at `discogs_label_gen/core/models.py` for model definitions

## Summary

1. **Existing code works** - No immediate changes needed
2. **New code should use models** - Better type safety and clarity
3. **Migration is gradual** - Migrate one module at a time
4. **Future-proof** - Easy to switch to PostgreSQL later
