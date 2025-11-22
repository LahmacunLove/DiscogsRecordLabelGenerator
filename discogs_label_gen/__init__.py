#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discogs Record Label Generator - Core Package

A comprehensive library for managing Discogs music collections with support for
YouTube matching, audio analysis, and label generation.

Created on 2025-01-22
@author: ffx
"""

__version__ = "0.2.0"
__author__ = "ffx"

# Re-export core models for convenience
from .core.models import (
    Release,
    Track,
    Artist,
    Label,
    Genre,
    YouTubeMatch,
    AudioAnalysis,
    DownloadStatus
)

# Re-export database interface
from .database.base import DatabaseBackend
from .database.sqlite_backend import SQLiteBackend

__all__ = [
    'Release',
    'Track',
    'Artist',
    'Label',
    'Genre',
    'YouTubeMatch',
    'AudioAnalysis',
    'DownloadStatus',
    'DatabaseBackend',
    'SQLiteBackend',
]
