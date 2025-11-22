#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite database module for Discogs Record Label Generator

COMPATIBILITY LAYER: This module now uses the new refactored backend.
The new architecture is in discogs_label_gen/ package.

For new code, prefer importing from discogs_label_gen directly:
    from discogs_label_gen import SQLiteBackend, Release

This file maintains backward compatibility during gradual migration.

Created on 2025-01-22
@author: ffx
"""

import sys
from pathlib import Path

# Add parent directory to path to import from discogs_label_gen
sys.path.insert(0, str(Path(__file__).parent.parent))

# Re-export the compatibility wrapper as DiscogsDatabase
from discogs_label_gen.database.compat_wrapper import DiscogsDatabase

__all__ = ['DiscogsDatabase']
