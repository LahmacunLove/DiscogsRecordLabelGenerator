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

    def find_bandcamp_release(self, metadata):
        """Find matching Bandcamp release using catalog numbers, artist, and title"""
        bandcamp_path = self.config.get("BANDCAMP_PATH")
        if not bandcamp_path:
            logger.debug("No BANDCAMP_PATH configured")
            return None
        
        bandcamp_path = Path(bandcamp_path).expanduser()
        if not bandcamp_path.exists():
            logger.debug(f"Bandcamp path does not exist: {bandcamp_path}")
            return None
        
        # Extract metadata for matching
        artists = metadata.get('artist', [])
        title = metadata.get('title', '')
        catalog_numbers = metadata.get('catalog_numbers', [])
        
        logger.debug(f"Searching Bandcamp for: {artists} - {title} (catalog: {catalog_numbers})")
        
        # Strategy 1: Try matching by catalog number first (most reliable)
        if catalog_numbers:
            for catno in catalog_numbers:
                catno_clean = catno.replace('-', '').replace(' ', '').lower()
                pattern = f"**/*{catno_clean}*"
                matches = glob.glob(str(bandcamp_path / pattern), recursive=True)
                for match in matches:
                    match_path = Path(match)
                    if match_path.is_dir():
                        logger.info(f"Found Bandcamp release by catalog number {catno}: {match_path}")
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
                    f"**/{artist_clean} - {title_clean}*"
                ]
                
                for pattern in patterns:
                    matches = glob.glob(str(bandcamp_path / pattern), recursive=True)
                    for match in matches:
                        match_path = Path(match)
                        if match_path.is_dir():
                            logger.info(f"Found Bandcamp release by title match: {match_path}")
                            return match_path
        
        logger.debug(f"No Bandcamp release found for: {artists} - {title}")
        return None

    def get_bandcamp_audio_files(self, bandcamp_folder):
        """Get all audio files from a Bandcamp folder"""
        if not bandcamp_folder or not bandcamp_folder.exists():
            return []
        
        audio_extensions = ['.flac', '.wav', '.mp3', '.m4a', '.aiff', '.alac']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(bandcamp_folder.glob(f"*{ext}"))
            audio_files.extend(bandcamp_folder.glob(f"**/*{ext}"))
        
        # Sort by filename for consistent ordering
        audio_files.sort(key=lambda x: x.name.lower())
        
        logger.debug(f"Found {len(audio_files)} audio files in Bandcamp folder: {bandcamp_folder}")
        return audio_files

    def copy_bandcamp_audio_to_release_folder(self, bandcamp_folder, metadata):
        """Copy Bandcamp audio files to release folder with proper naming"""
        audio_files = self.get_bandcamp_audio_files(bandcamp_folder)
        if not audio_files:
            return False
        
        tracklist = metadata.get('tracklist', [])
        if not tracklist:
            logger.warning("No tracklist available for Bandcamp audio matching")
            return False
        
        logger.info(f"Copying {len(audio_files)} Bandcamp audio files to release folder")
        
        # Create simple mapping: assume audio files are in track order
        copied_count = 0
        for i, audio_file in enumerate(audio_files):
            if i >= len(tracklist):
                logger.warning(f"More audio files than tracks in tracklist, stopping at {i}")
                break
            
            track = tracklist[i]
            track_position = track.get('position', str(i+1))
            
            # Determine target filename with original extension
            target_filename = f"{track_position}{audio_file.suffix}"
            target_path = self.release_folder / target_filename
            
            try:
                # Copy the high-quality audio file
                import shutil
                shutil.copy2(audio_file, target_path)
                logger.success(f"Copied Bandcamp audio: {audio_file.name} → {target_filename}")
                copied_count += 1
                
            except Exception as e:
                logger.error(f"Failed to copy {audio_file.name}: {e}")
                return False
        
        logger.success(f"Successfully copied {copied_count} Bandcamp audio files")
        return copied_count > 0

    def analyze_bandcamp_audio(self, metadata, download_only=False):
        """Analyze Bandcamp audio files if analysis is enabled"""
        if download_only:
            return
        
        # Import audio analyzer
        from analyzeSoundFile import analyzeAudioFileOrStream
        
        for track in metadata.get('tracklist', []):
            track_position = track.get('position', '')
            if not track_position:
                continue
            
            # Find the audio file
            audio_file = None
            for ext in ['.flac', '.wav', '.mp3', '.m4a', '.aiff', '.alac']:
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
                    logger.debug(f"Running Essentia analysis for Bandcamp audio: {audio_file.name}")
                    analyzer = analyzeAudioFileOrStream(
                        fileOrStream=str(audio_file),
                        sampleRate=44100,
                        plotWaveform=False,
                        musicExtractor=True,
                        plotSpectogram=True,
                        debug=False
                    )
                    analyzer.readAudioFile(ffmpegUsage=False)
                    analyzer.analyzeMusicExtractor()
                
                # Perform waveform generation (independent task)
                if waveform_needed:
                    logger.debug(f"Generating waveform for Bandcamp audio: {audio_file.name}")
                    # Create separate analyzer if not already created
                    if analyzer is None:
                        analyzer = analyzeAudioFileOrStream(
                            fileOrStream=str(audio_file),
                            sampleRate=44100,
                            plotWaveform=False,
                            musicExtractor=False,  # No need for music analysis
                            plotSpectogram=False,  # No need for spectrograms
                            debug=False
                        )
                        analyzer.readAudioFile(ffmpegUsage=False)
                    
                    analyzer.generate_waveform_gnuplot()
                
            except Exception as e:
                logger.warning(f"Failed to analyze Bandcamp audio {audio_file.name}: {e}")
                continue

    def get_collection_release_ids(self):
      
       folder = self.discogs.user(self.username).collection_folders[0]  # "All" Folder
       release_ids = []
       
       logger.process("Loading all release IDs from Discogs collection...")
       page = 1  # start page?
       
       while True:
           releases = folder.releases.page(page)  # Get releases of current page
           # print(len(folder.releases.page(page)))
           for release in releases:
               release_ids.append(release.release.id)
       
           # If current page has fewer than per_page releases, we might be done
           if len(releases) < 50: # change to 50 later for entire library
               break
       
           page += 1
           time.sleep(1)  # Wait for Discogs API rate limit
       
       return release_ids
   
    def clean_string_for_filename(self, name, replace_with="_"):
        # Remove anything not alphanumeric, dot, dash, or underscore
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replace_with, name)
        name = re.sub(r'\s+', '_', name)  # Optional: replace spaces
        return name.strip(replace_with)

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
                        logger.debug(f"Release {entry.name} incomplete - will be reprocessed")
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
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            tracklist = metadata.get('tracklist', [])
            if not tracklist:
                # No tracks expected, but basic files should exist
                return True
            
            # Check each track for complete processing
            for track in tracklist:
                track_pos = track.get('position', '')
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
            logger.debug(f"Error checking release completeness for {release_dir.name}: {e}")
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
        title = sanitize_filename(metadata.get('title', release_id))
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
            
    def convert_to_datetime(self,datetime_string):
        tz_offset = datetime.strptime(datetime_string[-5:], "%H:%M")
        return datetime.strptime(datetime_string[:-6], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=tz_offset.hour)


            
            
    def sync_releases(self, max_releases=None, download_only=False, discogs_only=False, progress_callback=None):
        """Compares releases and saves new releases or deletes removed releases."""
        # Always load local IDs
        local_ids = set(self.get_local_release_ids())

        if max_releases:
            # Development/Limited Mode: Only fetch metadata if we don't have max_releases yet
            if len(local_ids) >= max_releases:
                logger.info(f"Development mode: Already have {len(local_ids)} releases (>= {max_releases}), skipping Discogs API calls")
                logger.info("Continuing with existing local releases for processing...")
                releases_to_process = list(local_ids)[:max_releases]
                
                # For existing releases: Always generate new LaTeX labels
                logger.process("Regenerating LaTeX labels for existing releases...")
                logger.info(f"Will regenerate labels for {len(releases_to_process)} releases: {list(releases_to_process)[:3]}...")
                with tqdm(total=len(releases_to_process), desc="Updating labels", unit="release") as pbar:
                    for release_id in releases_to_process:
                        success = self.regenerate_latex_label(release_id)
                        if success:
                            logger.debug(f"✓ Label regenerated for {release_id}")
                        else:
                            logger.warning(f"✗ Failed to regenerate label for {release_id}")
                        pbar.update(1)
                logger.success("Label regeneration completed!")
                return  # Done - no further sync operations needed
            else:
                # Only now load Discogs collection if really necessary
                logger.info(f"Development mode: Have {len(local_ids)} releases, need {max_releases - len(local_ids)} more")
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
                
                logger.info(f"Development mode: Will process {len(releases_to_process)} new releases")
            
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
            # Use fewer workers but still benefit from I/O concurrency
            optimal_workers = min(3, max(1, len(releases_to_process) // 10))
            logger.debug(f"Discogs-only mode: using {optimal_workers} workers (rate limit: 60/min)")
        else:
            optimal_workers, effective_cores, logical_cores, ht_detected = get_optimal_workers(min_workers=2, max_percentage=0.6)
            
            if ht_detected:
                logger.debug(f"Hyperthreading detected: {logical_cores} logical → {effective_cores} physical cores")
            logger.debug(f"Using {optimal_workers} workers for release processing")
        
        # Use ThreadPoolExecutor for Discogs-only mode due to rate limits
        executor_class = concurrent.futures.ThreadPoolExecutor if discogs_only else concurrent.futures.ProcessPoolExecutor
        
        if progress_callback:
            # GUI mode - use callback for progress reporting
            with executor_class(max_workers=optimal_workers) as executor:
                futures = [executor.submit(self.sync_single_release, release_id, download_only, discogs_only) for release_id in releases_to_process]
                completed = 0
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        completed += 1
                        progress_callback(completed, len(releases_to_process), mode_desc)
                    except Exception as e:
                        logger.error(f"Error during synchronization: {e}")
                        completed += 1
                        progress_callback(completed, len(releases_to_process), mode_desc)
        else:
            # Console mode - use tqdm
            with tqdm(total=len(releases_to_process), desc=mode_desc, unit="release") as pbar:
                with executor_class(max_workers=optimal_workers) as executor:
                    futures = [executor.submit(self.sync_single_release, release_id, download_only, discogs_only) for release_id in releases_to_process]
                
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            pbar.update(1)  # Increase progress by 1
                        except Exception as e:
                            logger.error(f"Error during synchronization: {e}")
                            pbar.update(1)  # Also increase progress on errors


        # Remove deleted releases
        # removed_ids = local_ids - discogs_ids
        # for release_id in removed_ids:
        #     print(f"Release removed: {release_id}")
        #     self.delete_release_folder(release_id)

            
            
    def sync_single_release(self, release_id, download_only=False, discogs_only=False):
        # Save new releases
        collectionElement = self.discogs.release(release_id)  # Get metadata here something is wrong
        timestamp = self.discogs.user(self.username).collection_items(release_id)[0].data['date_added']
        
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
                if hasattr(label, 'data') and 'catno' in label.data:
                    catno = label.data['catno']
                    if catno and catno.strip():
                        catalog_numbers.append(catno.strip())
                # Try direct attribute access (newer API versions)
                elif hasattr(label, 'catno') and label.catno:
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
            "formats": collectionElement.formats[0] if collectionElement.formats else {},
            "year": collectionElement.year,
            "id": collectionElement.id,
            "timestamp": timestamp,
            "videos": [video.url for video in collectionElement.videos] if hasattr(collectionElement, 'videos') else []
        }

        # Collect tracklist
        tracklist = []
        for track in collectionElement.tracklist:
            track_artists = ', '.join([r.name for r in track.artists]) if hasattr(track, 'artists') else ''
            tracklist.append({
                "position": track.position,
                "title": track.title,
                "artist": track_artists,
                "duration": track.duration
            })
            
        metadata["tracklist"] = tracklist
        
        title = sanitize_filename(metadata.get('title', release_id))
        self.release_folder = self.library_path / f"{release_id}_{title}" 
        
        # do all discogs stuff
        # save metadata
        self.save_release_metadata(release_id, metadata)
        # save coverart
        self.save_cover_art(release_id, metadata)
        
        # Discogs-only mode: skip audio processing entirely
        if discogs_only:
            logger.info(f"📀 Discogs-only mode: metadata and covers saved for {release_id}")
            return
        
        # Check for Bandcamp high-quality audio first
        bandcamp_folder = self.find_bandcamp_release(metadata)
        used_bandcamp = False
        
        if bandcamp_folder:
            logger.info(f"🎵 Found Bandcamp release: {bandcamp_folder}")
            if self.copy_bandcamp_audio_to_release_folder(bandcamp_folder, metadata):
                logger.success(f"✅ Using high-quality Bandcamp audio for {release_id}")
                used_bandcamp = True
                
                if not download_only:
                    # Analyze Bandcamp audio files
                    self.analyze_bandcamp_audio(metadata, download_only=False)
            else:
                logger.warning("⚠️ Failed to copy Bandcamp audio, falling back to YouTube")
        
        # Fallback to YouTube if no Bandcamp or if copy failed
        if not used_bandcamp:
            logger.info(f"🎬 Using YouTube audio for {release_id}")
            yt_searcher = youtube_handler.YouTubeMatcher(self.release_folder, False) # initialize yt_module
            yt_searcher.match_discogs_release_youtube(metadata) # match metadata and save matches
            
            if download_only:
                # Download-only mode: only download audio files without analysis
                logger.info(f"[{release_id}] Download-only mode: downloading audio without analysis")
                yt_searcher.audio_download_only(metadata)
            else:
                # Normal mode: download and analyze
                yt_searcher.audio_download_analyze(metadata) # download matches
        
        if not download_only:
            # create qr code with cover background
            generate_qr_code_advanced(self.release_folder, release_id, metadata)
            
            # create latex labels
            create_latex_label_file(self.release_folder, metadata)
    
    def regenerate_latex_label(self, release_id):
        """Regenerates only the LaTeX label for an existing release without sync operations"""
        try:
            logger.debug(f"Regenerating label for release ID: {release_id}")
            
            # Find release folder
            release_folder = None
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    release_folder = item
                    logger.debug(f"Found release folder: {release_folder.name}")
                    break
            else:
                logger.error(f"Release folder not found for ID: {release_id} in {self.library_path}")
                return False
            
            # Load existing metadata
            metadata_file = release_folder / 'metadata.json'
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id} at {metadata_file}")
                return False
            
            logger.debug(f"Loading metadata from: {metadata_file}")
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Create new LaTeX label (overwrites existing)
            logger.debug(f"Creating LaTeX label for: {metadata.get('title', 'Unknown')}")
            result = create_latex_label_file(str(release_folder), metadata)
            
            if result:
                logger.debug(f"✓ Successfully regenerated LaTeX label for release {release_id}")
                # Check if file was really created
                label_file = release_folder / 'label.tex'
                if label_file.exists():
                    logger.debug(f"✓ label.tex file exists at: {label_file}")
                else:
                    logger.warning(f"✗ label.tex file NOT found at: {label_file}")
                return True
            else:
                logger.warning(f"✗ create_latex_label_file returned False for {release_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error regenerating LaTeX label for {release_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        # yt_searcher.search_release_tracks(release_id, metaData, self.release_folder )

        # analyze track
    
    def regenerate_existing_files(self, regenerate_labels=False, regenerate_waveforms=False):
        """Regenerates LaTeX labels and/or waveforms for all existing releases"""
        local_ids = set(self.get_local_release_ids())
        
        if not local_ids:
            logger.warning("No local releases found for regeneration")
            return
        
        logger.info(f"Found {len(local_ids)} local releases for regeneration")
        
        # Sort for consistent order
        releases_to_process = sorted(list(local_ids))
        
        # Progress bar for regeneration
        desc = []
        if regenerate_labels:
            desc.append("labels")
        if regenerate_waveforms:
            desc.append("waveforms")
        desc_str = " & ".join(desc)
        
        with tqdm(total=len(releases_to_process), desc=f"Regenerating {desc_str}", unit="release") as pbar:
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
                        logger.debug(f"✓ Labels & waveforms regenerated for {release_id}")
                    else:
                        logger.warning(f"✗ Partial failure for {release_id} - Labels: {success_labels}, Waveforms: {success_waveforms}")
                elif regenerate_labels:
                    if success_labels:
                        logger.debug(f"✓ Label regenerated for {release_id}")
                    else:
                        logger.warning(f"✗ Failed to regenerate label for {release_id}")
                elif regenerate_waveforms:
                    if success_waveforms:
                        logger.debug(f"✓ Waveforms regenerated for {release_id}")
                    else:
                        logger.warning(f"✗ Failed to regenerate waveforms for {release_id}")
                
                pbar.update(1)
        
        logger.success(f"Regeneration completed for {len(releases_to_process)} releases!")
    
    def process_existing_releases_offline(self):
        """Processes existing releases offline without Discogs/YouTube sync"""
        local_ids = set(self.get_local_release_ids())
        
        if not local_ids:
            logger.warning("No local releases found for offline processing")
            return
        
        logger.info(f"Found {len(local_ids)} local releases for offline processing")
        
        # Sort for consistent order
        releases_to_process = sorted(list(local_ids))
        
        with tqdm(total=len(releases_to_process), desc="Processing offline", unit="release") as pbar:
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
                    metadata_file = release_folder / 'metadata.json'
                    if not metadata_file.exists():
                        logger.warning(f"No metadata.json found for release {release_id}")
                        pbar.update(1)
                        continue
                    
                    with open(metadata_file, 'r', encoding='utf-8') as f:
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
        
        logger.success(f"Offline processing completed for {len(releases_to_process)} releases!")
    
    def _process_audio_analysis_offline(self, metadata):
        """Performs audio analysis for existing files if not already present"""
        from analyzeSoundFile import analyzeAudioFileOrStream
        
        for track in metadata.get('tracklist', []):
            track_pos = track.get('position', '')
            if not track_pos:
                continue
            
            # Search for audio file
            audio_extensions = ['.opus', '.mp3', '.wav', '.m4a', '.ogg']
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
                        debug=False
                    )
                    analyzer.readAudioFile(ffmpegUsage=False)
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
                            debug=False
                        )
                        analyzer.readAudioFile(ffmpegUsage=False)
                    
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
            metadata_file = release_folder / 'metadata.json'
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id}")
                return False
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Find all audio files and regenerate waveforms
            from analyzeSoundFile import analyzeAudioFileOrStream
            
            waveforms_generated = 0
            for track in metadata.get('tracklist', []):
                track_pos = track.get('position', '')
                if not track_pos:
                    continue
                
                # Search for audio file
                audio_file = None
                for ext in ['.opus', '.m4a', '.mp3', '.wav']:
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
                            logger.warning(f"✗ Failed to generate waveform for track {track_pos}")
                    except Exception as e:
                        logger.warning(f"Error generating waveform for track {track_pos}: {e}")
                else:
                    logger.debug(f"No audio file found for track {track_pos}")
            
            logger.debug(f"Generated {waveforms_generated} waveforms for release {release_id}")
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
        
        
    def save_cover_art(self, release_id, metadata):
        """Downloads all available cover images for a release"""
        
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
                image_url = image['uri']
                
                # First image keeps original name, others get indexed
                if i == 0:
                    filename = "cover.jpg"
                else:
                    filename = f"cover_{i+1}.jpg"
                    
                image_path = os.path.join(self.release_folder, filename)
                
                # Skip if file already exists
                if os.path.isfile(image_path):
                    logger.debug(f"Image already exists: {filename}")
                    continue
                
                logger.download(f"Cover art {i+1}/{len(images)} for release {release_id}: {filename}")
                
                req = urllib.request.Request(
                    image_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
    
                with urllib.request.urlopen(req) as response, \
                    open(image_path, 'wb') as out_file:
                    out_file.write(response.read())
                    
                logger.success(f"Downloaded: {filename}")
                    
            except Exception as e:
                logger.warning(f"Failed to download image {i+1}: {e}")
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
            metadata_file = release_folder / 'metadata.json'
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id}")
                return False
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            logger.info(f"Processing release offline: {metadata.get('title', 'Unknown Title')}")
            
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
            
