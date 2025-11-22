#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic tests for database backend

Verifies that the new database backend works correctly.

Created on 2025-01-22
@author: ffx
"""

import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discogs_label_gen import SQLiteBackend, Release, Artist, Label, Genre, Track


def test_basic_operations():
    """Test basic CRUD operations"""
    print("Testing basic database operations...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Initialize backend
        backend = SQLiteBackend(db_path)
        backend.connect()
        backend.initialize_schema()

        # Create a test release
        release = Release(
            release_id=123456,
            title="Test Album",
            year=2020
        )
        release.artists.append(Artist(name="Test Artist"))
        release.labels.append(Label(name="Test Label", catalog_number="TEST-001"))
        release.genres.append(Genre(name="Electronic"))
        release.tracks.append(Track(
            release_id=123456,
            position="A1",
            title="Test Track",
            duration="3:45"
        ))

        # Test save
        assert backend.save_release(release), "Failed to save release"
        print("✓ Save release")

        # Test exists
        assert backend.release_exists(123456), "Release should exist"
        print("✓ Release exists")

        # Test get
        retrieved = backend.get_release(123456)
        assert retrieved is not None, "Failed to retrieve release"
        assert retrieved.title == "Test Album"
        assert len(retrieved.artists) == 1
        assert retrieved.artists[0].name == "Test Artist"
        assert len(retrieved.tracks) == 1
        print("✓ Get release")

        # Test get_all_release_ids
        all_ids = backend.get_all_release_ids()
        assert 123456 in all_ids, "Release ID should be in list"
        print("✓ Get all release IDs")

        # Test search
        by_artist = backend.search_releases_by_artist("Test Artist")
        assert len(by_artist) == 1
        assert by_artist[0].release_id == 123456
        print("✓ Search by artist")

        by_label = backend.search_releases_by_label("Test Label")
        assert len(by_label) == 1
        print("✓ Search by label")

        by_year = backend.search_releases_by_year(2020)
        assert len(by_year) == 1
        print("✓ Search by year")

        # Test statistics
        stats = backend.get_statistics()
        assert stats['total_releases'] == 1
        assert stats['total_tracks'] == 1
        assert stats['total_artists'] == 1
        print("✓ Get statistics")

        # Test delete
        assert backend.delete_release(123456), "Failed to delete release"
        assert not backend.release_exists(123456), "Release should not exist"
        print("✓ Delete release")

        backend.disconnect()
        print("\n✅ All database backend tests passed!")
        return True

    finally:
        # Cleanup
        if db_path.exists():
            db_path.unlink()


def test_compatibility_wrapper():
    """Test that the compatibility wrapper works with old code"""
    print("\nTesting compatibility wrapper...")

    # Import old way
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    from database import DiscogsDatabase

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Use old-style dictionary API
        db = DiscogsDatabase(db_path)

        metadata = {
            'release_id': 789012,
            'title': 'Compatibility Test',
            'year': 2021,
            'artist': ['Old Style Artist'],
            'label': ['Old Label'],
            'catalog_numbers': ['OLD-001'],
            'genres': ['Rock'],
            'tracklist': [
                {'position': '1', 'title': 'Track One', 'duration': '4:20'}
            ]
        }

        # Test save (dict format)
        assert db.save_release(metadata), "Failed to save via compatibility layer"
        print("✓ Save release (dict format)")

        # Test get (returns dict)
        retrieved = db.get_release(789012)
        assert retrieved is not None
        assert retrieved['title'] == 'Compatibility Test'
        assert 'Old Style Artist' in retrieved['artist']
        print("✓ Get release (dict format)")

        # Test other operations
        assert db.release_exists(789012)
        print("✓ Release exists")

        stats = db.get_statistics()
        assert stats['total_releases'] == 1
        print("✓ Get statistics")

        db.close()
        print("\n✅ All compatibility wrapper tests passed!")
        return True

    finally:
        if db_path.exists():
            db_path.unlink()


if __name__ == '__main__':
    print("=" * 60)
    print("Database Backend Tests")
    print("=" * 60)

    try:
        test_basic_operations()
        test_compatibility_wrapper()
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
