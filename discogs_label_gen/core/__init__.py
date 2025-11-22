#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core data models and domain entities

This module contains the fundamental data structures used throughout
the application. All models are independent of database implementation.

Created on 2025-01-22
@author: ffx
"""

from .models import (
    Release,
    Track,
    Artist,
    Label,
    Genre,
    YouTubeMatch,
    AudioAnalysis,
    DownloadStatus
)

__all__ = [
    'Release',
    'Track',
    'Artist',
    'Label',
    'Genre',
    'YouTubeMatch',
    'AudioAnalysis',
    'DownloadStatus',
]
