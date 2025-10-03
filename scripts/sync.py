#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discogs Record Label Generator - CLI Sync Tool

Command-line interface for syncing Discogs library and generating labels.
Replaces GUI with CLI options and sensible defaults.

@author: ffx
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add src/ to Python path (go up one level from scripts/ to project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import load_config, get_config_path
from mirror import DiscogsLibraryMirror
from logger import logger
from latex_generator import combine_latex_labels


def create_config(token, library_path, bandcamp_path=None):
    """Create or update configuration file"""
    config_file = get_config_path()
    config_dir = config_file.parent

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Prepare configuration
    config = {
        "DISCOGS_USER_TOKEN": token,
        "LIBRARY_PATH": str(Path(library_path).expanduser().resolve()),
    }

    if bandcamp_path:
        config["BANDCAMP_PATH"] = str(Path(bandcamp_path).expanduser().resolve())

    # Write configuration
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    logger.success(f"Configuration saved to {config_file}")
    return config


def validate_config(config):
    """Validate that required configuration values are present"""
    required_fields = ["DISCOGS_USER_TOKEN", "LIBRARY_PATH"]
    missing = [field for field in required_fields if not config.get(field)]

    if missing:
        logger.error(f"Missing required configuration fields: {', '.join(missing)}")
        return False

    return True


def sync_library(mode="dev", max_releases=None, dryrun=False):
    """Sync Discogs library to local filesystem"""
    logger.separator("Starting Library Sync")
    logger.info(f"Mode: {mode}")

    if dryrun:
        logger.info("DRY RUN MODE: No API calls or downloads will be made")

    # Initialize mirror (reads config internally)
    mirror = DiscogsLibraryMirror()

    logger.info(f"Library Path: {mirror.library_path}")

    # Set mode
    if mode == "dev":
        mirror.dev_mode = True
        if max_releases:
            mirror.max_releases = max_releases

    # Sync library
    try:
        if dryrun:
            mirror.process_existing_releases_offline()
            logger.success("Dry run processing completed")
        else:
            mirror.sync_releases(max_releases=max_releases)
            logger.success("Library sync completed successfully")

        return mirror
    except KeyboardInterrupt:
        logger.warning("Sync interrupted by user")
        return None
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise


def generate_labels(
    mirror, output_dir=None, max_labels=None, specific_release=None, since_date=None
):
    """Generate LaTeX labels from synced library"""
    if not mirror:
        logger.error("No mirror available for label generation")
        return False

    logger.separator("Generating Labels")

    # Use library path from the mirror
    library_path = str(mirror.library_path)

    if not output_dir:
        output_dir = str(mirror.library_path.parent / "vinyl_labels")

    logger.info(f"Output directory: {output_dir}")

    # Generate master document with all labels
    success = combine_latex_labels(
        library_path=library_path,
        output_dir=output_dir,
        max_labels=max_labels,
        specific_release=specific_release,
        since_date=since_date,
    )

    if success:
        logger.success("📋 Labels generated successfully!")
        logger.info(f"📁 Output: {output_dir}")

        # Check for generated files
        output_path = Path(output_dir)
        tex_files = list(output_path.glob("*.tex"))
        pdf_files = list(output_path.glob("*.pdf"))

        if tex_files:
            logger.info(f"Generated {len(tex_files)} LaTeX files")
        if pdf_files:
            logger.info(f"Generated {len(pdf_files)} PDF files")
    else:
        logger.error("Label generation failed")

    return success


def main():
    """Main entry point for sync CLI"""
    parser = argparse.ArgumentParser(
        description="Sync Discogs library and generate vinyl labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync library and generate labels (development mode)
  %(prog)s --token YOUR_TOKEN --library ~/Music/Discogs --dev

  # Full sync with all releases
  %(prog)s --token YOUR_TOKEN --library ~/Music/Discogs

  # Dry run (process existing releases only)
  %(prog)s --dryrun

  # Configure and sync
  %(prog)s --token YOUR_TOKEN --library ~/Music/Discogs --configure
  %(prog)s --sync

  # Generate labels only (no sync)
  %(prog)s --labels-only --max-labels 10
        """,
    )

    # Configuration options
    config_group = parser.add_argument_group("configuration")
    config_group.add_argument("--token", help="Discogs API token")
    config_group.add_argument(
        "--library", help="Path to library directory", default="~/DiscogsLibrary"
    )
    config_group.add_argument(
        "--bandcamp", help="Path to Bandcamp directory (optional)"
    )
    config_group.add_argument(
        "--configure", action="store_true", help="Save configuration and exit"
    )

    # Sync options
    sync_group = parser.add_argument_group("sync options")
    sync_group.add_argument(
        "--sync", action="store_true", help="Sync library from Discogs"
    )
    sync_group.add_argument(
        "--dev", action="store_true", help="Development mode (limited releases)"
    )
    sync_group.add_argument(
        "--max", type=int, help="Maximum number of releases to process"
    )
    sync_group.add_argument(
        "--dryrun",
        action="store_true",
        help="Dry run mode (process existing releases only)",
    )

    # Label generation options
    label_group = parser.add_argument_group("label generation")
    label_group.add_argument(
        "--labels", action="store_true", help="Generate labels after sync"
    )
    label_group.add_argument(
        "--labels-only", action="store_true", help="Generate labels without syncing"
    )
    label_group.add_argument("--output", help="Output directory for labels")
    label_group.add_argument(
        "--max-labels", type=int, help="Maximum number of labels to generate"
    )
    label_group.add_argument("--release", help="Generate label for specific release ID")
    label_group.add_argument(
        "--since", help="Generate labels for releases added since date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Handle configuration
    if args.token or args.configure:
        if not args.token:
            parser.error("--token is required when using --configure")

        config = create_config(
            token=args.token, library_path=args.library, bandcamp_path=args.bandcamp
        )

        if args.configure:
            logger.success(
                "Configuration saved. You can now run sync without --token and --library"
            )
            return 0
    else:
        # Load existing configuration
        try:
            config = load_config()
        except FileNotFoundError:
            logger.error(
                "No configuration found. Please run with --token and --library first, or use --configure"
            )
            logger.info(
                "Example: sync.py --token YOUR_TOKEN --library ~/Music/Discogs --configure"
            )
            return 1

    # Validate configuration
    if not validate_config(config):
        return 1

    # Determine what to do
    mirror = None

    # Default behavior: sync + generate labels if no specific flags
    if not any([args.sync, args.labels, args.labels_only, args.dryrun]):
        args.sync = True
        args.labels = True

    # Sync library
    if args.sync or args.dryrun:
        try:
            mirror = sync_library(
                mode="dev" if args.dev else "full",
                max_releases=args.max,
                dryrun=args.dryrun,
            )

            if not mirror:
                return 1
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return 1

    # Generate labels
    if args.labels or args.labels_only:
        # For labels-only mode, need to load the mirror
        if args.labels_only and not mirror:
            logger.info("Loading existing library for label generation...")
            try:
                mirror = DiscogsLibraryMirror()
                # No need to explicitly load - mirror reads from filesystem
            except Exception as e:
                logger.error(f"Failed to load library: {e}")
                return 1

        if mirror:
            success = generate_labels(
                mirror=mirror,
                output_dir=args.output,
                max_labels=args.max_labels,
                specific_release=args.release,
                since_date=args.since,
            )

            if not success:
                return 1

    logger.success("✨ All operations completed successfully!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
