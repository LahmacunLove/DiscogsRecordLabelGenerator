#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup duplicate releases caused by sanitization changes

This script identifies releases with the same ID but different folder names
due to changes in the sanitization procedure, and removes the folders that
don't match the current sanitization rules.

@author: ffx
"""

import os
import sys
import json
import shutil
from pathlib import Path
from collections import defaultdict

# Add src/ to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import load_config
from utils import sanitize_filename
from logger import logger

def find_duplicate_releases(library_path):
    """Find releases with same ID but different folder names"""
    release_folders = defaultdict(list)
    
    for item in library_path.iterdir():
        if not item.is_dir():
            continue
            
        folder_name = item.name
        if "_" not in folder_name:
            continue
            
        try:
            # Extract release ID from folder name
            release_id = int(folder_name.split("_")[0])
            release_folders[release_id].append(item)
        except (ValueError, IndexError):
            continue
    
    # Filter to only releases with multiple folders
    duplicates = {k: v for k, v in release_folders.items() if len(v) > 1}
    return duplicates

def get_correct_folder_name(release_id, metadata):
    """Generate the correct folder name using current sanitization"""
    title = metadata.get('title', str(release_id))
    sanitized_title = sanitize_filename(title)
    return f"{release_id}_{sanitized_title}"

def choose_folder_to_keep(folders):
    """Choose which folder to keep based on current sanitization rules"""
    best_folder = None
    best_score = -1
    
    for folder in folders:
        score = 0
        
        # Load metadata to get original title
        metadata_file = folder / "metadata.json"
        if not metadata_file.exists():
            logger.warning(f"No metadata.json in {folder.name}, skipping")
            continue
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {folder.name}: {e}")
            continue
        
        # Get release ID and title
        release_id = folder.name.split("_")[0]
        correct_name = get_correct_folder_name(release_id, metadata)
        
        # Score based on how well it matches current sanitization
        if folder.name == correct_name:
            score += 100  # Perfect match
        
        # Check for completeness
        if (folder / "cover.jpg").exists():
            score += 10
        if (folder / "qrcode.png").exists():
            score += 5
        if (folder / "label.tex").exists():
            score += 5
        
        # Count audio files
        audio_files = list(folder.glob("*.opus")) + list(folder.glob("*.mp3")) + list(folder.glob("*.m4a"))
        score += len(audio_files)
        
        # Prefer newer folders (by modification time)
        score += folder.stat().st_mtime / 1000000  # Small weight for recency
        
        logger.debug(f"Folder {folder.name} scored {score}")
        
        if score > best_score:
            best_score = score
            best_folder = folder
    
    return best_folder

def cleanup_duplicates(library_path, dry_run=True):
    """Main cleanup function"""
    logger.separator("Duplicate Release Cleanup")
    
    duplicates = find_duplicate_releases(library_path)
    
    if not duplicates:
        logger.success("No duplicate releases found!")
        return
    
    logger.info(f"Found {len(duplicates)} releases with duplicate folders")
    
    total_folders_to_remove = 0
    
    for release_id, folders in duplicates.items():
        logger.info(f"\nProcessing release {release_id} ({len(folders)} folders):")
        
        for folder in folders:
            logger.info(f"  - {folder.name}")
        
        # Choose the best folder to keep
        folder_to_keep = choose_folder_to_keep(folders)
        
        if not folder_to_keep:
            logger.warning(f"Could not determine best folder for release {release_id}, skipping")
            continue
        
        folders_to_remove = [f for f in folders if f != folder_to_keep]
        
        logger.success(f"  → Keeping: {folder_to_keep.name}")
        
        for folder in folders_to_remove:
            logger.warning(f"  → Removing: {folder.name}")
            total_folders_to_remove += 1
            
            if not dry_run:
                try:
                    shutil.rmtree(folder)
                    logger.success(f"    ✓ Removed {folder.name}")
                except Exception as e:
                    logger.error(f"    ✗ Failed to remove {folder.name}: {e}")
    
    if dry_run:
        logger.info(f"\nDRY RUN: Would remove {total_folders_to_remove} duplicate folders")
        logger.info("Run with --execute to actually remove folders")
    else:
        logger.success(f"\nCleanup completed! Removed {total_folders_to_remove} duplicate folders")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cleanup duplicate releases caused by sanitization changes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually remove duplicate folders (default is dry-run mode)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    library_path = Path(config["LIBRARY_PATH"]).expanduser()
    
    if not library_path.exists():
        logger.error(f"Library path does not exist: {library_path}")
        sys.exit(1)
    
    logger.info(f"Library path: {library_path}")
    
    if args.execute:
        logger.warning("EXECUTE MODE: Will actually remove duplicate folders!")
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            logger.info("Cancelled")
            sys.exit(0)
    else:
        logger.info("DRY RUN MODE: Will only show what would be removed")
    
    cleanup_duplicates(library_path, dry_run=not args.execute)

if __name__ == "__main__":
    main()