#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database abstraction layer

Provides a pluggable database backend system that supports multiple
database engines (SQLite, PostgreSQL, MySQL) through a common interface.

Created on 2025-01-22
@author: ffx
"""

from .base import DatabaseBackend
from .sqlite_backend import SQLiteBackend

__all__ = [
    'DatabaseBackend',
    'SQLiteBackend',
]
