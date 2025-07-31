#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for DiscogsRecordLabelGenerator

@author: ffx
"""

import re


def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing problematic characters.
    
    Args:
        filename (str): The original filename/foldername
        
    Returns:
        str: Sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed"
    
    # Replace problematic characters with underscores
    # This includes: \ / : * ? " < > | ' and other filesystem-unsafe chars
    # Added apostrophe (') because it causes issues with gnuplot
    sanitized = re.sub(r'[\\/:*?"<>|\'"]', '_', str(filename))
    
    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing whitespace and dots (Windows compatibility)
    sanitized = sanitized.strip(' .')
    
    # Ensure we don't have an empty string
    if not sanitized:
        return "unnamed"
        
    return sanitized