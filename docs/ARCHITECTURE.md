# Architecture Documentation

## Overview

The project has been refactored into a clean, modular architecture that separates concerns and prepares for migration from SQLite to SQL server databases (PostgreSQL/MySQL).

## Directory Structure

```
DiscogsRecordLabelGenerator/
├── discogs_label_gen/          # Main package (new architecture)
│   ├── __init__.py
│   ├── core/                   # Domain models
│   │   ├── __init__.py
│   │   └── models.py           # Release, Track, Artist, etc.
│   ├── database/               # Data persistence layer
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract database interface
│   │   ├── sqlite_backend.py   # SQLite implementation
│   │   └── compat_wrapper.py   # Backward compatibility
│   ├── services/               # Business logic (future)
│   ├── cli/                    # Command-line interface (future)
│   └── utils/                  # Helper functions (future)
├── src/                        # Legacy code (being migrated)
│   ├── database.py             # Now imports from discogs_label_gen
│   ├── mirror.py
│   └── ...
├── tests/                      # Test suite
│   └── test_database_backend.py
├── docs/                       # Documentation
│   └── ARCHITECTURE.md
└── scripts/                    # Utility scripts (future)
```

## Core Concepts

### 1. Domain Models (`discogs_label_gen/core/models.py`)

Data models are **independent of database implementation**. They use Python dataclasses and represent domain entities:

- `Release` - Music release with metadata
- `Track` - Individual track on a release
- `Artist` - Artist information
- `Label` - Record label
- `Genre` - Music genre
- `YouTubeMatch` - YouTube video match for a track
- `AudioAnalysis` - Audio analysis data (BPM, key, etc.)
- `DownloadStatus` - Enum for download states

**Key features:**
- Type-safe with dataclasses
- Includes `to_dict()` and `from_dict()` for serialization
- No database dependencies

**Example usage:**
```python
from discogs_label_gen import Release, Artist, Track

release = Release(
    release_id=123456,
    title="Kid A",
    year=2000
)
release.artists.append(Artist(name="Radiohead"))
release.tracks.append(Track(
    release_id=123456,
    position="1",
    title="Everything In Its Right Place"
))
```

### 2. Database Abstraction Layer (`discogs_label_gen/database/`)

The database layer uses the **Strategy Pattern** to allow swapping database backends.

#### `base.py` - Abstract Interface

Defines the contract that all database backends must implement:

```python
class DatabaseBackend(ABC):
    @abstractmethod
    def save_release(self, release: Release) -> bool:
        pass

    @abstractmethod
    def get_release(self, release_id: int) -> Optional[Release]:
        pass

    # ... more methods
```

#### `sqlite_backend.py` - SQLite Implementation

Concrete implementation using SQLite:

```python
from discogs_label_gen import SQLiteBackend

backend = SQLiteBackend(Path("collection.db"))
backend.connect()
backend.initialize_schema()

# Work with Release objects
backend.save_release(release)
release = backend.get_release(123456)
```

#### `compat_wrapper.py` - Backward Compatibility

Provides old dictionary-based API for gradual migration:

```python
from discogs_label_gen.database.compat_wrapper import DiscogsDatabase

db = DiscogsDatabase(db_path)

# Old style - works with dictionaries
metadata = {
    'release_id': 123456,
    'title': 'Kid A',
    'artist': ['Radiohead']
}
db.save_release(metadata)
```

### 3. Legacy Compatibility

The old `src/database.py` now simply re-exports the compatibility wrapper:

```python
# src/database.py
from discogs_label_gen.database.compat_wrapper import DiscogsDatabase
```

This means **all existing code continues to work** without modifications:
- `main.py`
- `download_assets.py`
- `query_database.py`
- `migrate_to_database.py`

## Migration Strategy

### Phase 1: Foundation (COMPLETED ✅)

- ✅ Create new package structure
- ✅ Define domain models
- ✅ Create database abstraction layer
- ✅ Implement SQLite backend
- ✅ Create compatibility wrapper
- ✅ Add tests
- ✅ Verify existing code still works

### Phase 2: Gradual Migration (IN PROGRESS)

Migrate modules one at a time:

1. **Services Layer** - Extract business logic from mirror.py
2. **CLI Layer** - Separate command-line interface
3. **Utils** - Move helper functions

### Phase 3: Database Migration (FUTURE)

Prepare for SQL server migration:

1. Create PostgreSQL backend (`postgres_backend.py`)
2. Create MySQL backend (`mysql_backend.py`)
3. Add database configuration system
4. Test with both SQLite and PostgreSQL
5. Production deployment with PostgreSQL

## Usage Examples

### New Code (Recommended)

```python
from discogs_label_gen import SQLiteBackend, Release, Artist

# Create backend
backend = SQLiteBackend(Path("collection.db"))
backend.connect()
backend.initialize_schema()

# Create release
release = Release(release_id=123, title="Test")
release.artists.append(Artist(name="Artist"))

# Save
backend.save_release(release)

# Retrieve
release = backend.get_release(123)
print(f"Title: {release.title}")
print(f"Artist: {release.artists[0].name}")

backend.disconnect()
```

### Old Code (Still Works)

```python
from database import DiscogsDatabase

db = DiscogsDatabase(Path("collection.db"))

# Old dictionary format
metadata = {
    'release_id': 123,
    'title': 'Test',
    'artist': ['Artist']
}
db.save_release(metadata)

retrieved = db.get_release(123)
print(retrieved['title'])  # Dictionary access

db.close()
```

## Benefits of New Architecture

### 1. Database Flexibility

Switch between SQLite and PostgreSQL with minimal code changes:

```python
# Development - SQLite
backend = SQLiteBackend(Path("dev.db"))

# Production - PostgreSQL (future)
backend = PostgreSQLBackend(
    host="localhost",
    database="discogs",
    user="user",
    password="pass"
)

# Same API for both!
backend.save_release(release)
```

### 2. Type Safety

Models provide IDE autocomplete and type checking:

```python
release = backend.get_release(123)
release.title          # ✓ IDE knows this is a string
release.year           # ✓ IDE knows this is Optional[int]
release.unknownfield   # ✗ IDE catches typo
```

### 3. Testability

Easy to mock database for unit tests:

```python
class MockBackend(DatabaseBackend):
    def save_release(self, release):
        return True
    # ... implement other methods
```

### 4. Separation of Concerns

- **Models** - What the data looks like
- **Database** - How to store/retrieve data
- **Services** - What to do with the data
- **CLI** - How users interact

### 5. Maintainability

- Clear module boundaries
- Single responsibility per class
- Easy to understand and modify

## Testing

Run the test suite:

```bash
python3 tests/test_database_backend.py
```

This tests:
- All CRUD operations
- Search functionality
- Statistics
- Backward compatibility

## Future Database Backends

### PostgreSQL Backend (Planned)

```python
# discogs_label_gen/database/postgres_backend.py
class PostgreSQLBackend(DatabaseBackend):
    def __init__(self, host, database, user, password):
        self.connection_params = {...}
        # Use psycopg2 or asyncpg

    def save_release(self, release: Release) -> bool:
        # PostgreSQL-specific implementation
        pass
```

### Configuration

```python
# Future: config.py
DATABASE_CONFIG = {
    'backend': 'postgresql',  # or 'sqlite', 'mysql'
    'host': 'localhost',
    'database': 'discogs',
    'user': 'user',
    'password': 'pass'
}

# Factory pattern
def get_database():
    if DATABASE_CONFIG['backend'] == 'sqlite':
        return SQLiteBackend(...)
    elif DATABASE_CONFIG['backend'] == 'postgresql':
        return PostgreSQLBackend(...)
```

## Migration Checklist

When migrating existing code:

- [ ] Replace dictionary access with model attributes
- [ ] Use `Release` instead of `metadata` dict
- [ ] Use `backend.save_release()` instead of `db.save_release()`
- [ ] Use type hints for better IDE support
- [ ] Add unit tests for new code

## Questions?

See also:
- `WORKFLOW.md` - Two-phase sync workflow
- `DATABASE.md` - SQLite schema details
- `CLAUDE.md` - Project overview
