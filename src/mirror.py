#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  5 22:44:08 2025

@author: ffx
"""

import os
import time
from pathlib import Path
import discogs_client
from config import load_config
from datetime import datetime
from datetime import timedelta
import re
import urllib.request
import youtube_handler
import concurrent.futures
import threading
import json
import shutil
import re
from logger import logger
from cpu_utils import get_optimal_workers
from latex_generator import create_latex_label_file
from qr_generator import generate_qr_code_advanced
from utils import sanitize_filename
from tqdm import tqdm
import glob
from thread_monitor import ThreadMonitor, WorkerProgressTracker


class DiscogsLibraryMirror:
    def __init__(self):
        self.config = load_config()
        self.discogs = self._init_discogs_client()
        self.library_path = Path(self.config["LIBRARY_PATH"]).expanduser()
        self.user = self.discogs.identity()
        self.username = self.user.username
        logger.info(f"Library path: {self.library_path}")

    def _init_discogs_client(self):
        token = self.config.get("DISCOGS_USER_TOKEN")
        if not token:
            raise ValueError("Discogs token missing in config.")
        return discogs_client.Client("DiscogsDBLabelGen/0.1", user_token=token)

    def find_bandcamp_release(self, metadata, tracker=None):
        """Find matching Bandcamp release using catalog numbers, artist, and title"""
        if tracker:
            tracker.update_step("Searching Bandcamp library", 36)

        bandcamp_path = self.config.get("BANDCAMP_PATH")
        if not bandcamp_path:
            logger.debug("No BANDCAMP_PATH configured")
            return None

        bandcamp_path = Path(bandcamp_path).expanduser()
        if not bandcamp_path.exists():
            logger.debug(f"Bandcamp path does not exist: {bandcamp_path}")
            return None

        # Extract metadata for matching
        artists = metadata.get("artist", [])
        title = metadata.get("title", "")
        catalog_numbers = metadata.get("catalog_numbers", [])

        logger.debug(
            f"Searching Bandcamp for: {artists} - {title} (catalog: {catalog_numbers})"
        )

        # Strategy 1: Try matching by catalog number first (most reliable)
        if catalog_numbers:
            for catno in catalog_numbers:
                catno_clean = catno.replace("-", "").replace(" ", "").lower()
                pattern = f"**/*{catno_clean}*"
                matches = glob.glob(str(bandcamp_path / pattern), recursive=True)
                for match in matches:
                    match_path = Path(match)
                    if match_path.is_dir():
                        logger.info(
                            f"Found Bandcamp release by catalog number {catno}: {match_path}"
                        )
                        return match_path

        # Strategy 2: Try matching by artist and album title
        if artists and title:
            for artist in artists:
                # Clean artist and title for pattern matching
                artist_clean = sanitize_filename(artist).lower()
                title_clean = sanitize_filename(title).lower()

                # Try various folder name patterns commonly used in Bandcamp downloads
                patterns = [
                    f"**/*{artist_clean}*{title_clean}*",
                    f"**/*{title_clean}*{artist_clean}*",
                    f"**/{artist_clean}*/{title_clean}*",
                    f"**/{artist_clean} - {title_clean}*",
                ]

                for pattern in patterns:
                    matches = glob.glob(str(bandcamp_path / pattern), recursive=True)
                    for match in matches:
                        match_path = Path(match)
                        if match_path.is_dir():
                            logger.info(
                                f"Found Bandcamp release by title match: {match_path}"
                            )
                            return match_path

        logger.debug(f"No Bandcamp release found for: {artists} - {title}")
        return None

    def get_bandcamp_audio_files(self, bandcamp_folder):
        """Get all audio files from a Bandcamp folder"""
        if not bandcamp_folder or not bandcamp_folder.exists():
            return []

        audio_extensions = [".flac", ".wav", ".mp3", ".m4a", ".aiff", ".alac"]
        audio_files = []

        for ext in audio_extensions:
            audio_files.extend(bandcamp_folder.glob(f"*{ext}"))
            audio_files.extend(bandcamp_folder.glob(f"**/*{ext}"))

        # Sort by filename for consistent ordering
        audio_files.sort(key=lambda x: x.name.lower())

        logger.debug(
            f"Found {len(audio_files)} audio files in Bandcamp folder: {bandcamp_folder}"
        )
        return audio_files

    def copy_bandcamp_audio_to_release_folder(
        self, bandcamp_folder, metadata, tracker=None
    ):
        """Copy Bandcamp audio files to release folder with proper naming"""
        if tracker:
            tracker.update_step("Preparing Bandcamp files", 41)

        audio_files = self.get_bandcamp_audio_files(bandcamp_folder)
        if not audio_files:
            return False

        tracklist = metadata.get("tracklist", [])
        if not tracklist:
            logger.warning("No tracklist available for Bandcamp audio matching")
            return False

        logger.info(
            f"Copying {len(audio_files)} Bandcamp audio files to release folder"
        )

        # Create simple mapping: assume audio files are in track order
        copied_count = 0
        total_files = min(len(audio_files), len(tracklist))

        for i, audio_file in enumerate(audio_files):
            if tracker and total_files > 0:
                progress = 42 + (i / total_files) * 8  # 42-50% range
                tracker.update_step(
                    f"Copying Bandcamp file {i + 1}/{total_files}", progress
                )
            if i >= len(tracklist):
                logger.warning(
                    f"More audio files than tracks in tracklist, stopping at {i}"
                )
                break

            track = tracklist[i]
            track_position = track.get("position", str(i + 1))

            # Determine target filename with original extension
            target_filename = f"{track_position}{audio_file.suffix}"
            target_path = self.release_folder / target_filename

            try:
                # Copy the high-quality audio file
                import shutil

                shutil.copy2(audio_file, target_path)
                logger.success(
                    f"Copied Bandcamp audio: {audio_file.name} → {target_filename}"
                )
                copied_count += 1

            except Exception as e:
                logger.error(f"Failed to copy {audio_file.name}: {e}")
                return False

        logger.success(f"Successfully copied {copied_count} Bandcamp audio files")
        return copied_count > 0

    def analyze_bandcamp_audio(self, metadata, download_only=False, tracker=None):
        """Analyze Bandcamp audio files if analysis is enabled"""
        if download_only:
            return

        # Import audio analyzer
        from analyzeSoundFile import analyzeAudioFileOrStream

        tracklist = metadata.get("tracklist", [])
        total_tracks = len(tracklist)

        for track_idx, track in enumerate(tracklist):
            if tracker and total_tracks > 0:
                progress = 70 + (track_idx / total_tracks) * 15  # 70-85% range
                tracker.update_step(
                    f"Analyzing Bandcamp track {track_idx + 1}/{total_tracks}", progress
                )

            track_position = track.get("position", "")
            if not track_position:
                continue

            # Find the audio file
            audio_file = None
            for ext in [".flac", ".wav", ".mp3", ".m4a", ".aiff", ".alac"]:
                potential_file = self.release_folder / f"{track_position}{ext}"
                if potential_file.exists():
                    audio_file = potential_file
                    break

            if not audio_file:
                continue

            # Check what analysis is needed
            analysis_file = self.release_folder / f"{track_position}.json"
            waveform_file = self.release_folder / f"{track_position}_waveform.png"

            analysis_needed = not analysis_file.exists()
            waveform_needed = not waveform_file.exists()

            if not analysis_needed and not waveform_needed:
                continue  # Already analyzed

            try:
                analyzer = None

                # Perform Essentia analysis (independent task)
                if analysis_needed:
                    logger.debug(
                        f"Running Essentia analysis for Bandcamp audio: {audio_file.name}"
                    )
                    analyzer = analyzeAudioFileOrStream(
                        fileOrStream=str(audio_file),
                        sampleRate=44100,
                        plotWaveform=False,
                        musicExtractor=True,
                        plotSpectogram=True,
                        debug=False,
                    )
                    analyzer.readAudioFile(ffmpegUsage=True)
                    analyzer.analyzeMusicExtractor()

                # Perform waveform generation (independent task)
                if waveform_needed:
                    logger.debug(
                        f"Generating waveform for Bandcamp audio: {audio_file.name}"
                    )
                    # Create separate analyzer if not already created
                    if analyzer is None:
                        analyzer = analyzeAudioFileOrStream(
                            fileOrStream=str(audio_file),
                            sampleRate=44100,
                            plotWaveform=False,
                            musicExtractor=False,  # No need for music analysis
                            plotSpectogram=False,  # No need for spectrograms
                            debug=False,
                        )
                        analyzer.readAudioFile(ffmpegUsage=True)

                    analyzer.generate_waveform_gnuplot()

            except Exception as e:
                logger.warning(
                    f"Failed to analyze Bandcamp audio {audio_file.name}: {e}"
                )
                continue

    def get_collection_release_ids(self):
        folder = self.discogs.user(self.username).collection_folders[0]  # "All" Folder
        release_ids = []

        logger.process("Loading all release IDs from Discogs collection...")
        page = 1  # start page?

        while True:
            logger.info(f"Fetching page {page} from Discogs API...")
            releases = folder.releases.page(page)  # Get releases of current page

            for release in releases:
                release_ids.append(release.release.id)

            logger.info(f"Downloaded {len(release_ids)} release IDs so far...")

            # If current page has fewer than per_page releases, we might be done
            if len(releases) < 50:  # change to 50 later for entire library
                break

            page += 1
            time.sleep(1)  # Wait for Discogs API rate limit

        logger.success(f"Loaded {len(release_ids)} release IDs from Discogs collection")
        return release_ids

    def clean_string_for_filename(self, name, replace_with="_"):
        # Remove anything not alphanumeric, dot, dash, or underscore
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replace_with, name)
        name = re.sub(r"\s+", "_", name)  # Optional: replace spaces
        return name.strip(replace_with)

    def get_all_local_release_ids(self):
        """Get ALL release IDs that have at least metadata.json (for label regeneration)."""
        if not self.library_path.exists():
            return []
        local_ids = []
        for entry in self.library_path.iterdir():
            if entry.is_dir() and "_" in entry.name:
                try:
                    release_id = int(entry.name.split("_")[0])

                    # Only check for metadata.json existence
                    metadata_file = entry / "metadata.json"
                    if metadata_file.exists():
                        local_ids.append(release_id)
                    else:
                        logger.debug(
                            f"Release {entry.name} has no metadata.json - skipping"
                        )
                except ValueError:
                    pass
        return local_ids

    def get_local_release_ids(self):
        """Get release IDs that are completely processed through all pipeline steps."""
        if not self.library_path.exists():
            return []
        local_ids = []
        for entry in self.library_path.iterdir():
            if entry.is_dir() and "_" in entry.name:
                try:
                    release_id = int(entry.name.split("_")[0])

                    # Check for complete processing pipeline
                    if self._is_release_complete(entry):
                        local_ids.append(release_id)
                    else:
                        logger.debug(
                            f"Release {entry.name} incomplete - will be reprocessed"
                        )
                except ValueError:
                    pass
        return local_ids

    def _is_release_complete(self, release_dir):
        """Check if a release has completed all processing steps."""
        try:
            # Step 1: Metadata from Discogs
            metadata_file = release_dir / "metadata.json"
            if not metadata_file.exists():
                return False

            # Step 1b: Cover image
            cover_file = release_dir / "cover.jpg"
            if not cover_file.exists():
                return False

            # Step 1c: QR code
            qr_file = release_dir / "qrcode.png"
            if not qr_file.exists():
                return False

            # Step 1d: Fancy QR code
            qr_fancy_file = release_dir / "qrcode_fancy.png"
            if not qr_fancy_file.exists():
                return False

            # Step 2: YouTube videos matched
            yt_matches_file = release_dir / "yt_matches.json"
            if not yt_matches_file.exists():
                return False

            # Load metadata to get expected tracks
            import json

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            tracklist = metadata.get("tracklist", [])
            if not tracklist:
                # No tracks expected, but basic files should exist
                return True

            # Check each track for complete processing
            for track in tracklist:
                track_pos = track.get("position", "")
                if not track_pos:
                    continue

                # Step 3: Audio downloaded
                audio_file = release_dir / f"{track_pos}.opus"
                if not audio_file.exists():
                    return False

                # Step 4: Analysis JSON
                analysis_file = release_dir / f"{track_pos}.json"
                if not analysis_file.exists():
                    return False

                # Step 5: Spectrograms
                mel_spectro = release_dir / f"{track_pos}_Mel-spectogram.png"
                hpcp_spectro = release_dir / f"{track_pos}_HPCP_chromatogram.png"
                if not mel_spectro.exists() or not hpcp_spectro.exists():
                    return False

                # Step 6: Waveform
                waveform_file = release_dir / f"{track_pos}_waveform.png"
                if not waveform_file.exists():
                    return False

            # Step 7: LaTeX file
            latex_file = release_dir / "label.tex"
            if not latex_file.exists():
                return False

            # All steps complete!
            return True

        except Exception as e:
            logger.debug(
                f"Error checking release completeness for {release_dir.name}: {e}"
            )
            return False

    def get_diff(self):
        discogs_ids = set(self.get_collection_release_ids())
        local_ids = set(self.get_local_release_ids())
        new_ids = discogs_ids - local_ids
        removed_ids = local_ids - discogs_ids
        return new_ids, removed_ids

    def save_release_metadata(self, release_id, metadata):
        """Saves the complete metadata of a release in a folder and JSON file."""
        # Create a folder for the release based on the ID and possibly a title
        # (can also be done with the release_id as name)
        title = sanitize_filename(metadata.get("title", release_id))
        release_folder = self.library_path / f"{release_id}_{title}"
        release_folder.mkdir(parents=True, exist_ok=True)

        # Save all metadata as JSON file
        metadata_path = release_folder / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        logger.success(f"Release {release_id} metadata saved")

    def delete_release_folder(self, release_id):
        """Deletes a folder containing a release if the release no longer exists."""
        # release_folder = self.library_path / f"{release_id}"
        if self.release_folder.exists() and self.release_folder.is_dir():
            print(f"Deleting release: {release_id}")
            shutil.rmtree(self.release_folder)

    def convert_to_datetime(self, datetime_string):
        tz_offset = datetime.strptime(datetime_string[-5:], "%H:%M")
        return datetime.strptime(datetime_string[:-6], "%Y-%m-%dT%H:%M:%S") + timedelta(
            hours=tz_offset.hour
        )

    def sync_releases(
        self,
        max_releases=None,
        download_only=False,
        discogs_only=False,
        progress_callback=None,
    ):
        """Compares releases and saves new releases or deletes removed releases."""
        # Always load local IDs
        local_ids = set(self.get_local_release_ids())

        if max_releases:
            # Development/Limited Mode: Only fetch metadata if we don't have max_releases yet
            if len(local_ids) >= max_releases:
                logger.info(
                    f"Development mode: Already have {len(local_ids)} releases (>= {max_releases}), skipping Discogs API calls"
                )
                logger.info("Continuing with existing local releases for processing...")
                releases_to_process = list(local_ids)[:max_releases]

                # For existing releases: Always generate new LaTeX labels
                logger.process("Regenerating LaTeX labels for existing releases...")
                logger.info(
                    f"Will regenerate labels for {len(releases_to_process)} releases: {list(releases_to_process)[:3]}..."
                )
                with tqdm(
                    total=len(releases_to_process),
                    desc="Updating labels",
                    unit="release",
                ) as pbar:
                    for release_id in releases_to_process:
                        success = self.regenerate_latex_label(release_id)
                        if success:
                            logger.debug(f"✓ Label regenerated for {release_id}")
                        else:
                            logger.warning(
                                f"✗ Failed to regenerate label for {release_id}"
                            )
                        pbar.update(1)
                logger.success("Label regeneration completed!")
                return  # Done - no further sync operations needed
            else:
                # Only now load Discogs collection if really necessary
                logger.info(
                    f"Development mode: Have {len(local_ids)} releases, need {max_releases - len(local_ids)} more"
                )
                logger.process("Loading Discogs collection for missing releases...")
                discogs_ids = set(self.get_collection_release_ids())

                missing_count = max_releases - len(local_ids)
                logger.info(f"Collection size: {len(discogs_ids)} total releases")

                # Take the first N releases from the collection, but skip those already present
                all_discogs_ids = list(discogs_ids)
                releases_to_process = []
                for release_id in all_discogs_ids:
                    if release_id not in local_ids:
                        releases_to_process.append(release_id)
                        if len(releases_to_process) >= missing_count:
                            break

                logger.info(
                    f"Development mode: Will process {len(releases_to_process)} new releases"
                )

            if not releases_to_process:
                logger.info("No releases to process")
                return
        else:
            # Normal Mode: Only process new releases - load Discogs here
            logger.process("Loading Discogs collection for comparison...")
            discogs_ids = set(self.get_collection_release_ids())
            releases_to_process = list(discogs_ids - local_ids)

            if not releases_to_process:
                logger.info("No new releases to process")
                return

        # Progress bar for release processing
        if discogs_only:
            mode_desc = "Syncing Discogs metadata"
        elif download_only:
            mode_desc = "Downloading releases"
        else:
            mode_desc = "Processing releases"

        # Get optimal workers for release processing (I/O intensive)
        if discogs_only:
            # For Discogs-only mode: limit workers due to API rate limits (60/min = 1/sec)
            # Use more workers for better I/O concurrency while staying under rate limits
            optimal_workers = min(8, max(2, len(releases_to_process) // 5))
            logger.debug(
                f"Discogs-only mode: using {optimal_workers} workers (rate limit: 60/min)"
            )
        else:
            optimal_workers, effective_cores, logical_cores, ht_detected = (
                get_optimal_workers(min_workers=2, max_percentage=0.85)
            )

            if ht_detected:
                logger.debug(
                    f"Hyperthreading detected: {logical_cores} logical → {effective_cores} physical cores"
                )
            logger.debug(f"Using {optimal_workers} workers for release processing")

        # Use ThreadPoolExecutor for Discogs-only mode due to rate limits
        # Also use ThreadPoolExecutor in console mode (no callback) because ThreadMonitor requires shared memory
        use_threads = discogs_only or (progress_callback is None)
        executor_class = (
            concurrent.futures.ThreadPoolExecutor
            if use_threads
            else concurrent.futures.ProcessPoolExecutor
        )

        if progress_callback:
            # Use callback for progress reporting
            with executor_class(max_workers=optimal_workers) as executor:
                futures = [
                    executor.submit(
                        self.sync_single_release,
                        release_id,
                        download_only,
                        discogs_only,
                    )
                    for release_id in releases_to_process
                ]
                completed = 0

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        completed += 1
                        progress_callback(
                            completed, len(releases_to_process), mode_desc
                        )
                    except Exception as e:
                        logger.error(f"Error during synchronization: {e}")
                        completed += 1
                        progress_callback(
                            completed, len(releases_to_process), mode_desc
                        )
        else:
            # Console mode - use ThreadMonitor for live visualization
            monitor = ThreadMonitor(
                total_releases=len(releases_to_process),
                num_workers=optimal_workers,
                mode_desc=mode_desc,
            )

            # Create a mapping of worker threads to IDs
            worker_id_map = {}
            worker_id_lock = threading.Lock()
            next_worker_id = [0]  # Use list to make it mutable in nested function

            def sync_with_monitoring(release_id, download_only, discogs_only):
                """Wrapper to add monitoring to sync_single_release"""
                # Assign worker ID
                thread_id = threading.current_thread().ident
                with worker_id_lock:
                    if thread_id not in worker_id_map:
                        worker_id_map[thread_id] = next_worker_id[0]
                        next_worker_id[0] += 1
                    worker_id = worker_id_map[thread_id]

                tracker = WorkerProgressTracker(monitor, worker_id)

                try:
                    # Check for shutdown before starting
                    if tracker.check_shutdown():
                        return None

                    # Call the original sync function with tracking
                    result = self.sync_single_release_monitored(
                        release_id, download_only, discogs_only, tracker
                    )

                    if not tracker.check_shutdown():
                        tracker.complete()
                    return result

                except Exception as e:
                    tracker.error(str(e))
                    raise

            # Use Live display context
            from rich.live import Live
            from rich.console import Console

            console = Console()

            try:
                # Install log handler to capture messages in the UI
                monitor.install_log_handler()

                with Live(
                    monitor._build_display(), console=console, refresh_per_second=10
                ) as live:
                    with executor_class(max_workers=optimal_workers) as executor:
                        futures = [
                            executor.submit(
                                sync_with_monitoring,
                                release_id,
                                download_only,
                                discogs_only,
                            )
                            for release_id in releases_to_process
                        ]

                        completed_futures = 0
                        for future in concurrent.futures.as_completed(futures):
                            if monitor.is_shutdown_requested():
                                # Cancel remaining futures
                                for f in futures:
                                    f.cancel()
                                break

                            try:
                                result = future.result()
                                completed_futures += 1
                            except Exception as e:
                                logger.error(f"Error during synchronization: {e}")
                                completed_futures += 1

                            # Update display after each completion
                            live.update(monitor._build_display())

                    # Wait for executor to fully shut down
                    # This ensures all threads have finished and updated their state

                # Final update after executor context exits
                time.sleep(0.1)  # Brief pause to ensure all state updates are visible

                # Build final display one more time to ensure 100% is shown
                final_display = monitor._build_display()
                console.print(final_display)

                # Print summary
                if monitor.is_shutdown_requested():
                    console.print("\n[bold yellow]⚠️  Shutdown completed[/]")
                else:
                    console.print(f"\n[bold green]✅ All releases processed![/]")

                console.print(
                    f"[bold]Completed:[/] {monitor.completed_count}/{monitor.total_releases}"
                )
                if monitor.error_count > 0:
                    console.print(f"[bold red]Errors:[/] {monitor.error_count}")

                # Clear message that sync phase is complete
                console.print(
                    "\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]"
                )
                console.print("[bold green]✅ Sync phase complete![/]")
                console.print(
                    "[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]\n"
                )

            except KeyboardInterrupt:
                monitor._signal_handler(None, None)
                console.print("\n[bold yellow]⚠️  Interrupted by user[/]")
            finally:
                # Remove log handler to restore normal logging
                monitor.remove_log_handler()

        # Remove deleted releases
        # removed_ids = local_ids - discogs_ids
        # for release_id in removed_ids:
        #     print(f"Release removed: {release_id}")
        #     self.delete_release_folder(release_id)

    def sync_single_release(self, release_id, download_only=False, discogs_only=False):
        """Original sync method without monitoring - for callback mode"""
        return self.sync_single_release_monitored(
            release_id, download_only, discogs_only, None
        )

    def sync_single_release_monitored(
        self, release_id, download_only=False, discogs_only=False, tracker=None
    ):
        """Sync a single release with optional progress tracking"""

        # Initialize tracking
        if tracker:
            tracker.set_release(release_id, f"Release {release_id}")
            tracker.update_step("Checking existing metadata", 5)

        # Check if metadata.json already exists to avoid unnecessary Discogs API calls
        title_placeholder = str(release_id)  # Temporary title for folder detection
        potential_folders = [
            f
            for f in self.library_path.iterdir()
            if f.is_dir() and f.name.startswith(f"{release_id}_")
        ]

        metadata = None
        if potential_folders:
            # Found existing folder - check for metadata.json
            release_folder = potential_folders[0]
            metadata_file = release_folder / "metadata.json"
            if metadata_file.exists():
                # Load existing metadata instead of calling Discogs API
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    logger.debug(
                        f"Using existing metadata for release {release_id} (avoiding Discogs API call)"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to load existing metadata for {release_id}, fetching from Discogs: {e}"
                    )
                    metadata = None

        # Only call Discogs API if we don't have metadata
        if metadata is None:
            if tracker:
                tracker.update_step("Fetching metadata from Discogs", 10)

            # Save new releases
            collectionElement = self.discogs.release(
                release_id
            )  # Get metadata here something is wrong
            timestamp = (
                self.discogs.user(self.username)
                .collection_items(release_id)[0]
                .data["date_added"]
            )

            logger.debug(f"Processing release: {collectionElement.url}")

            try:
                logger.debug(f"Apple Music link: {collectionElement.apple}")
            except:
                pass
            # Extract catalog numbers from labels
            catalog_numbers = []
            for label in collectionElement.labels:
                try:
                    # Try to get catalog number from label data
                    if hasattr(label, "data") and "catno" in label.data:
                        catno = label.data["catno"]
                        if catno and catno.strip():
                            catalog_numbers.append(catno.strip())
                    # Try direct attribute access (newer API versions)
                    elif hasattr(label, "catno") and label.catno:
                        catalog_numbers.append(label.catno.strip())
                except Exception as e:
                    logger.debug(f"Could not extract catalog number from label: {e}")
                    continue

            # Collect metadata
            metadata = {
                "title": collectionElement.title,
                "artist": [r.name for r in collectionElement.artists],
                "label": [label.name for label in collectionElement.labels],
                "catalog_numbers": catalog_numbers,
                "genres": collectionElement.genres,
                "formats": collectionElement.formats[0]
                if collectionElement.formats
                else {},
                "year": collectionElement.year,
                "release_id": release_id,
                "id": collectionElement.id,
                "timestamp": timestamp,
                "videos": [video.url for video in collectionElement.videos]
                if hasattr(collectionElement, "videos")
                else [],
            }

            # Collect tracklist
            tracklist = []
            for track in collectionElement.tracklist:
                track_artists = (
                    ", ".join([r.name for r in track.artists])
                    if hasattr(track, "artists")
                    else ""
                )
                # Clean track position by removing leading/trailing whitespace
                clean_position = track.position.strip() if track.position else ""
                tracklist.append(
                    {
                        "position": clean_position,
                        "title": track.title,
                        "artist": track_artists,
                        "duration": track.duration,
                    }
                )
            metadata["tracklist"] = tracklist

        title = sanitize_filename(metadata.get("title", release_id))
        self.release_folder = self.library_path / f"{release_id}_{title}"

        # Update tracker with actual title
        if tracker:
            tracker.set_release(release_id, title)
            tracker.update_step("Saving metadata", 20)

        # do all discogs stuff
        # save metadata
        self.save_release_metadata(release_id, metadata)
        if tracker:
            tracker.add_file(str(self.release_folder / "metadata.json"))
        # save coverart
        self.save_cover_art(release_id, metadata, tracker)
        if tracker:
            cover_files = list(self.release_folder.glob("cover.*"))
            if cover_files:
                tracker.add_file(str(cover_files[0]))

        # Discogs-only mode: skip audio processing entirely
        if discogs_only:
            if tracker:
                tracker.update_step("Completed (Discogs-only)", 100)
            logger.info(
                f"📀 Discogs-only mode: metadata and covers saved for {release_id}"
            )
            return

        # Check for Bandcamp high-quality audio first
        if tracker:
            tracker.update_step("Checking for Bandcamp audio", 35)
        bandcamp_folder = self.find_bandcamp_release(metadata, tracker)
        used_bandcamp = False

        if bandcamp_folder:
            if tracker:
                tracker.update_step("Copying Bandcamp audio", 40)
            logger.info(f"🎵 Found Bandcamp release: {bandcamp_folder}")
            if self.copy_bandcamp_audio_to_release_folder(
                bandcamp_folder, metadata, tracker
            ):
                logger.success(f"✅ Using high-quality Bandcamp audio for {release_id}")
                used_bandcamp = True

                if tracker:
                    audio_files = list(self.release_folder.glob("*.flac")) + list(
                        self.release_folder.glob("*.mp3")
                    )
                    for audio_file in audio_files[:3]:  # Show first 3 files
                        tracker.add_file(str(audio_file))

                if not download_only:
                    if tracker:
                        tracker.update_step("Analyzing Bandcamp audio", 70)
                    # Analyze Bandcamp audio files
                    self.analyze_bandcamp_audio(
                        metadata, download_only=False, tracker=tracker
                    )
            else:
                logger.warning(
                    "⚠️ Failed to copy Bandcamp audio, falling back to YouTube"
                )

        # Fallback to YouTube if no Bandcamp or if copy failed
        if not used_bandcamp:
            if tracker:
                tracker.update_step("Searching YouTube", 45)
            logger.info(f"🎬 Using YouTube audio for {release_id}")
            yt_searcher = youtube_handler.YouTubeMatcher(
                self.release_folder, False, tracker
            )  # initialize yt_module
            yt_searcher.match_discogs_release_youtube(
                metadata
            )  # match metadata and save matches

            if download_only:
                if tracker:
                    tracker.update_step("Downloading YouTube audio", 60)
                # Download-only mode: only download audio files without analysis
                logger.info(
                    f"[{release_id}] Download-only mode: downloading audio without analysis"
                )
                yt_searcher.audio_download_only(metadata)
                if tracker:
                    audio_files = list(self.release_folder.glob("*.opus")) + list(
                        self.release_folder.glob("*.m4a")
                    )
                    for audio_file in audio_files[:3]:
                        tracker.add_file(str(audio_file))
            else:
                if tracker:
                    tracker.update_step("Downloading & analyzing YouTube audio", 60)
                # Normal mode: download and analyze
                yt_searcher.audio_download_analyze(metadata)  # download matches
                if tracker:
                    audio_files = list(self.release_folder.glob("*.opus")) + list(
                        self.release_folder.glob("*.m4a")
                    )
                    for audio_file in audio_files[:3]:
                        tracker.add_file(str(audio_file))

        if not download_only:
            if tracker:
                tracker.update_step("Generating QR code", 85)
            # create qr code with cover background
            generate_qr_code_advanced(
                self.release_folder, release_id, metadata, tracker
            )
            if tracker:
                qr_files = list(self.release_folder.glob("*qr*.png"))
                if qr_files:
                    tracker.add_file(str(qr_files[0]))

            if tracker:
                tracker.update_step("Creating LaTeX label", 95)
            # create latex labels
            create_latex_label_file(self.release_folder, metadata, tracker)
            if tracker:
                tracker.add_file(str(self.release_folder / "label.tex"))

    def regenerate_latex_label(self, release_id):
        """Regenerates only the LaTeX label for an existing release without sync operations"""
        try:
            logger.debug(f"Regenerating label for release ID: {release_id}")

            # Find all matching release folders
            matching_folders = []
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    matching_folders.append(item)

            if not matching_folders:
                logger.error(
                    f"Release folder not found for ID: {release_id} in {self.library_path}"
                )
                return False

            # Handle multiple folders - process ALL matching folders
            if len(matching_folders) > 1:
                folder_names = [f.name for f in matching_folders]
                logger.warning(
                    f"Multiple directories found for ID {release_id}: {folder_names}"
                )
                logger.info(
                    f"Processing labels for all {len(matching_folders)} folders"
                )

            all_success = True
            for release_folder in matching_folders:
                logger.debug(f"Processing folder: {release_folder.name}")

                # Load existing metadata
                metadata_file = release_folder / "metadata.json"
                if not metadata_file.exists():
                    logger.error(
                        f"No metadata.json found for release {release_id} at {metadata_file}"
                    )
                    all_success = False
                    continue

                logger.debug(f"Loading metadata from: {metadata_file}")
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # Create new LaTeX label (overwrites existing)
                logger.debug(
                    f"Creating LaTeX label for: {metadata.get('title', 'Unknown')}"
                )
                result = create_latex_label_file(str(release_folder), metadata)

                if result:
                    logger.debug(
                        f"✓ Successfully regenerated LaTeX label for release {release_id} in {release_folder.name}"
                    )
                    # Check if file was really created
                    label_file = release_folder / "label.tex"
                    if label_file.exists():
                        logger.debug(f"✓ label.tex file exists at: {label_file}")
                    else:
                        logger.warning(f"✗ label.tex file NOT found at: {label_file}")
                        all_success = False
                else:
                    logger.warning(
                        f"✗ create_latex_label_file returned False for {release_id} in {release_folder.name}"
                    )
                    all_success = False

            return all_success

        except Exception as e:
            logger.error(f"Error regenerating LaTeX label for {release_id}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

        # yt_searcher.search_release_tracks(release_id, metaData, self.release_folder )

        # analyze track

    def regenerate_existing_files(
        self, regenerate_labels=False, regenerate_waveforms=False, max_releases=None
    ):
        """Regenerates LaTeX labels and/or waveforms for existing releases"""

        # For label regeneration, use all releases with metadata.json (not just complete ones)
        if regenerate_labels and not regenerate_waveforms:
            local_ids = set(self.get_all_local_release_ids())
        else:
            # For waveforms or combined regeneration, use only complete releases
            local_ids = set(self.get_local_release_ids())

        if not local_ids:
            logger.warning("No local releases found for regeneration")
            return

        # Sort for consistent order
        releases_to_process = sorted(list(local_ids))

        # Apply max_releases limit if specified
        if max_releases is not None:
            releases_to_process = releases_to_process[:max_releases]
            logger.info(
                f"Found {len(local_ids)} local releases, processing first {len(releases_to_process)} due to --max limit"
            )
        else:
            logger.info(f"Found {len(local_ids)} local releases for regeneration")

        # Progress bar for regeneration
        desc = []
        if regenerate_labels:
            desc.append("labels")
        if regenerate_waveforms:
            desc.append("waveforms")
        desc_str = " & ".join(desc)

        with tqdm(
            total=len(releases_to_process),
            desc=f"Regenerating {desc_str}",
            unit="release",
        ) as pbar:
            for release_id in releases_to_process:
                success_labels = True
                success_waveforms = True

                if regenerate_labels:
                    success_labels = self.regenerate_latex_label(release_id)

                if regenerate_waveforms:
                    success_waveforms = self.regenerate_waveforms(release_id)

                # Logging for success/failure
                if regenerate_labels and regenerate_waveforms:
                    if success_labels and success_waveforms:
                        logger.debug(
                            f"✓ Labels & waveforms regenerated for {release_id}"
                        )
                    else:
                        logger.warning(
                            f"✗ Partial failure for {release_id} - Labels: {success_labels}, Waveforms: {success_waveforms}"
                        )
                elif regenerate_labels:
                    if success_labels:
                        logger.debug(f"✓ Label regenerated for {release_id}")
                    else:
                        logger.warning(f"✗ Failed to regenerate label for {release_id}")
                elif regenerate_waveforms:
                    if success_waveforms:
                        logger.debug(f"✓ Waveforms regenerated for {release_id}")
                    else:
                        logger.warning(
                            f"✗ Failed to regenerate waveforms for {release_id}"
                        )

                pbar.update(1)

        logger.success(
            f"Regeneration completed for {len(releases_to_process)} releases!"
        )

    def process_existing_releases_offline(self):
        """Processes existing releases offline without Discogs/YouTube sync"""
        local_ids = set(self.get_local_release_ids())

        if not local_ids:
            logger.warning("No local releases found for offline processing")
            return

        logger.info(f"Found {len(local_ids)} local releases for offline processing")

        # Sort for consistent order
        releases_to_process = sorted(list(local_ids))

        with tqdm(
            total=len(releases_to_process), desc="Processing offline", unit="release"
        ) as pbar:
            for release_id in releases_to_process:
                try:
                    # Find release folder
                    release_folder = None
                    for item in self.library_path.iterdir():
                        if item.is_dir() and item.name.startswith(f"{release_id}_"):
                            release_folder = item
                            break

                    if not release_folder:
                        logger.warning(f"Release folder not found for ID: {release_id}")
                        pbar.update(1)
                        continue

                    self.release_folder = release_folder

                    # Load metadata
                    metadata_file = release_folder / "metadata.json"
                    if not metadata_file.exists():
                        logger.warning(
                            f"No metadata.json found for release {release_id}"
                        )
                        pbar.update(1)
                        continue

                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    logger.debug(f"Processing offline: {release_id}")

                    # 1. Audio analysis (if not already present)
                    self._process_audio_analysis_offline(metadata)

                    # 2. QR code generation (both simple and fancy)
                    generate_qr_code_advanced(self.release_folder, release_id, metadata)

                    # 3. Create/update LaTeX label
                    create_latex_label_file(self.release_folder, metadata)

                except Exception as e:
                    logger.error(f"Error processing release {release_id} offline: {e}")

                pbar.update(1)

        logger.success(
            f"Offline processing completed for {len(releases_to_process)} releases!"
        )

    def _process_audio_analysis_offline(self, metadata):
        """Performs audio analysis for existing files if not already present"""
        from analyzeSoundFile import analyzeAudioFileOrStream

        for track in metadata.get("tracklist", []):
            track_pos = track.get("position", "")
            if not track_pos:
                continue

            # Search for audio file
            audio_extensions = [".opus", ".mp3", ".wav", ".m4a", ".ogg"]
            audio_file = None

            for ext in audio_extensions:
                potential_file = self.release_folder / f"{track_pos}{ext}"
                if potential_file.exists():
                    audio_file = potential_file
                    break

            if not audio_file:
                continue

            # Check if analysis already exists
            analysis_file = self.release_folder / f"{track_pos}.json"
            waveform_file = self.release_folder / f"{track_pos}_waveform.png"

            if analysis_file.exists() and waveform_file.exists():
                continue  # Already analyzed

            try:
                analysis_needed = not analysis_file.exists()
                waveform_needed = not waveform_file.exists()

                analyzer = None

                # Perform Essentia analysis (independent task)
                if analysis_needed:
                    logger.debug(f"Running Essentia analysis for: {audio_file.name}")
                    analyzer = analyzeAudioFileOrStream(
                        fileOrStream=str(audio_file),
                        sampleRate=44100,
                        plotWaveform=False,
                        musicExtractor=True,
                        plotSpectogram=True,
                        debug=False,
                    )
                    analyzer.readAudioFile(ffmpegUsage=True)
                    analyzer.analyzeMusicExtractor()

                # Perform waveform generation (independent task)
                if waveform_needed:
                    logger.debug(f"Generating waveform for: {audio_file.name}")
                    # Create separate analyzer if not already created
                    if analyzer is None:
                        analyzer = analyzeAudioFileOrStream(
                            fileOrStream=str(audio_file),
                            sampleRate=44100,
                            plotWaveform=False,
                            musicExtractor=False,  # No need for music analysis
                            plotSpectogram=False,  # No need for spectrograms
                            debug=False,
                        )
                        analyzer.readAudioFile(ffmpegUsage=True)

                    analyzer.generate_waveform_gnuplot()

            except Exception as e:
                logger.warning(f"Failed to analyze {audio_file.name}: {e}")

    def regenerate_waveforms(self, release_id):
        """Regenerates all waveforms for an existing release"""
        try:
            # Find release folder
            release_folder = None
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    release_folder = item
                    break
            else:
                logger.error(f"Release folder not found for ID: {release_id}")
                return False

            # Load metadata for tracklist
            metadata_file = release_folder / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id}")
                return False

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Find all audio files and regenerate waveforms
            from analyzeSoundFile import analyzeAudioFileOrStream

            waveforms_generated = 0
            for track in metadata.get("tracklist", []):
                track_pos = track.get("position", "")
                if not track_pos:
                    continue

                # Search for audio file
                audio_file = None
                for ext in [".opus", ".m4a", ".mp3", ".wav"]:
                    potential_file = release_folder / f"{track_pos}{ext}"
                    if potential_file.exists():
                        audio_file = potential_file
                        break

                if audio_file:
                    try:
                        # Initialize audio analyzer
                        analyzer = analyzeAudioFileOrStream(str(audio_file))
                        analyzer.load_audio()

                        # Generate waveform
                        if analyzer.generate_waveform():
                            waveforms_generated += 1
                            logger.debug(f"✓ Generated waveform for track {track_pos}")
                        else:
                            logger.warning(
                                f"✗ Failed to generate waveform for track {track_pos}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error generating waveform for track {track_pos}: {e}"
                        )
                else:
                    logger.debug(f"No audio file found for track {track_pos}")

            logger.debug(
                f"Generated {waveforms_generated} waveforms for release {release_id}"
            )
            return waveforms_generated > 0

        except Exception as e:
            logger.error(f"Error regenerating waveforms for {release_id}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

        # create LaTeX snippet?
        # - qr code

        # out of loop, create LaTeX full sheet

        return

    def save_cover_art(self, release_id, metadata, tracker=None):
        """Downloads all available cover images for a release"""

        # Check if primary cover already exists - if so, skip API call entirely
        primary_cover_path = os.path.join(self.release_folder, "cover.jpg")
        if os.path.isfile(primary_cover_path):
            logger.debug(
                f"Primary cover already exists for release {release_id}, skipping Discogs API call"
            )
            return

        if tracker:
            tracker.update_step("Fetching cover art metadata", 28)

        try:
            release = self.discogs.release(release_id)
            images = release.images
        except:
            images = []

        if not images:
            logger.debug(f"No images available for release {release_id}")
            return

        logger.debug(f"Found {len(images)} image(s) for release {release_id}")

        # Download all images with proper naming
        for i, image in enumerate(images):
            try:
                if tracker:
                    progress = (
                        30 + (i / len(images)) * 5
                    )  # 30-35% range for cover downloads
                    tracker.update_step(
                        f"Downloading cover art {i + 1}/{len(images)}", progress
                    )

                image_url = image["uri"]

                # First image keeps original name, others get indexed
                if i == 0:
                    filename = "cover.jpg"
                else:
                    filename = f"cover_{i + 1}.jpg"

                image_path = os.path.join(self.release_folder, filename)

                # Skip if file already exists
                if os.path.isfile(image_path):
                    logger.debug(f"Image already exists: {filename}")
                    continue

                logger.download(
                    f"Cover art {i + 1}/{len(images)} for release {release_id}: {filename}"
                )

                req = urllib.request.Request(
                    image_url, headers={"User-Agent": "Mozilla/5.0"}
                )

                with (
                    urllib.request.urlopen(req) as response,
                    open(image_path, "wb") as out_file,
                ):
                    out_file.write(response.read())

                logger.success(f"Downloaded: {filename}")

            except Exception as e:
                logger.warning(f"Failed to download image {i + 1}: {e}")
                continue

        return

    def process_single_release_offline(self, release_id):
        """Process a single release offline without Discogs/YouTube sync"""
        try:
            # Find release folder
            release_folder = None
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    release_folder = item
                    break
            else:
                logger.error(f"Release folder not found for ID: {release_id}")
                return False

            # Load metadata
            metadata_file = release_folder / "metadata.json"
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id}")
                return False

            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            logger.info(
                f"Processing release offline: {metadata.get('title', 'Unknown Title')}"
            )

            # Set release folder for other methods
            self.release_folder = release_folder

            # Process audio analysis
            self._process_audio_analysis_offline(metadata)

            # Generate LaTeX label and QR code
            self._generate_latex_label(metadata)
            self._generate_qr_code(metadata)

            logger.success(f"✅ Completed offline processing for release {release_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing release {release_id} offline: {e}")
            return False
