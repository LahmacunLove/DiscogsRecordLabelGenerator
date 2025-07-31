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
from latex_generator import create_latex_label_file
from qr_generator import generate_qr_code_advanced
from utils import sanitize_filename
from tqdm import tqdm


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
            raise ValueError("Discogs-Token fehlt in der Config.")
        return discogs_client.Client("DiscogsDBLabelGen/0.1", user_token=token)

    def get_collection_release_ids(self):
      
       folder = self.discogs.user(self.username).collection_folders[0]  # "All" Folder
       release_ids = []
       
       logger.process("Loading all release IDs from Discogs collection...")
       page = 1  # start page?
       
       while True:
           releases = folder.releases.page(page)  # Holt Releases der aktuellen Seite
           # print(len(folder.releases.page(page)))
           for release in releases:
               release_ids.append(release.release.id)
       
           # Wenn die aktuelle Seite weniger als per_page Releases hat, könnten wir fertig sein
           if len(releases) < 50: # hier später auf 50 ändern, für ganze lib
               break
       
           page += 1
           time.sleep(1)  # Zeit für Discogs API-Limit
       
       return release_ids
   
    def clean_string_for_filename(self, name, replace_with="_"):
        # Remove anything not alphanumeric, dot, dash, or underscore
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replace_with, name)
        name = re.sub(r'\s+', '_', name)  # Optional: replace spaces
        return name.strip(replace_with)

    def get_local_release_ids(self):
        if not self.library_path.exists():
            return []
        local_ids = []
        for entry in self.library_path.iterdir():
            if entry.is_dir() and "_" in entry.name:
                try:
                    local_ids.append(int(entry.name.split("_")[0]))
                except ValueError:
                    pass
        return local_ids

    def get_diff(self):
        discogs_ids = set(self.get_collection_release_ids())
        local_ids = set(self.get_local_release_ids())
        new_ids = discogs_ids - local_ids
        removed_ids = local_ids - discogs_ids
        return new_ids, removed_ids

    
    def save_release_metadata(self, release_id, metadata):
        """Speichert die kompletten Metadaten eines Releases in einem Ordner und einer JSON-Datei."""
        # Erstelle einen Ordner für das Release basierend auf der ID und ggf. einem Titel
        # (kann auch mit der release_id als Name erfolgen)
        title = sanitize_filename(metadata.get('title', release_id))
        release_folder = self.library_path / f"{release_id}_{title}"
        release_folder.mkdir(parents=True, exist_ok=True)
        
        # Speichern der gesamten Metadaten als JSON-Datei
        metadata_path = release_folder / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    
        logger.success(f"Release {release_id} metadata saved") 
        

    def delete_release_folder(self, release_id):
        """Löscht einen Ordner, der ein Release enthält, falls das Release nicht mehr existiert."""
        # release_folder = self.library_path / f"{release_id}"
        if self.release_folder.exists() and self.release_folder.is_dir():
            print(f"Lösche Release: {release_id}")
            shutil.rmtree(self.release_folder)
            
    def convert_to_datetime(self,datetime_string):
        tz_offset = datetime.strptime(datetime_string[-5:], "%H:%M")
        return datetime.strptime(datetime_string[:-6], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=tz_offset.hour)


            
            
    def sync_releases(self, max_releases=None):
        """Vergleicht die Releases und speichert neue Releases oder löscht gelöschte Releases."""
        # Lokale IDs immer laden
        local_ids = set(self.get_local_release_ids())

        if max_releases:
            # Development/Limited Mode: Nur Metadaten abrufen wenn noch keine max_releases vorliegen
            if len(local_ids) >= max_releases:
                logger.info(f"Development mode: Already have {len(local_ids)} releases (>= {max_releases}), skipping Discogs API calls")
                logger.info("Continuing with existing local releases for processing...")
                releases_to_process = list(local_ids)[:max_releases]
                
                # Für bestehende Releases: Generiere immer neue LaTeX-Labels
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
                return  # Fertig - keine weiteren Sync-Operationen nötig
            else:
                # Nur jetzt Discogs Collection laden wenn wirklich nötig
                logger.info(f"Development mode: Have {len(local_ids)} releases, need {max_releases - len(local_ids)} more")
                logger.process("Loading Discogs collection for missing releases...")
                discogs_ids = set(self.get_collection_release_ids())
                
                missing_count = max_releases - len(local_ids)
                logger.info(f"Collection size: {len(discogs_ids)} total releases")
                
                # Nimm die ersten N Releases aus der Collection, aber überspringe die bereits vorhandenen
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
            # Normal Mode: Nur neue Releases verarbeiten - hier Discogs laden
            logger.process("Loading Discogs collection for comparison...")
            discogs_ids = set(self.get_collection_release_ids())
            releases_to_process = list(discogs_ids - local_ids)
            
            if not releases_to_process:
                logger.info("No new releases to process")
                return
                
        
        # Progress Bar für Release-Verarbeitung
        with tqdm(total=len(releases_to_process), desc="Processing releases", unit="release") as pbar:
            with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self.sync_single_release, release_id) for release_id in releases_to_process]
            
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        pbar.update(1)  # Fortschritt um 1 erhöhen
                    except Exception as e:
                        logger.error(f"Fehler beim Synchronisieren: {e}")
                        pbar.update(1)  # Auch bei Fehlern Fortschritt erhöhen


        # Gelöschte Releases entfernen
        # removed_ids = local_ids - discogs_ids
        # for release_id in removed_ids:
        #     print(f"Release entfernt: {release_id}")
        #     self.delete_release_folder(release_id)

            
            
    def sync_single_release(self, release_id):
        # Neue Releases speichern
        collectionElement = self.discogs.release(release_id)  # Holt die Metadaten hier stimmt was nicht
        timestamp = self.discogs.user(self.username).collection_items(release_id)[0].data['date_added']
        
        logger.debug(f"Processing release: {collectionElement.url}")
        
        try:
            logger.debug(f"Apple Music link: {collectionElement.apple}")
        except:
            pass
        # Metadaten sammeln
        metadata = {
            "title": collectionElement.title,
            "artist": [r.name for r in collectionElement.artists],
            "label": [label.name for label in collectionElement.labels],
            "genres": collectionElement.genres,
            "formats": collectionElement.formats[0] if collectionElement.formats else {},
            "year": collectionElement.year,
            "id": collectionElement.id,
            "timestamp": timestamp,
            "videos": [video.url for video in collectionElement.videos] if hasattr(collectionElement, 'videos') else []
        }

        # Tracklist sammeln
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
        
        # do all youtube stuff
        yt_searcher = youtube_handler.YouTubeMatcher(self.release_folder, False) # initiiere yt_module
        yt_searcher.match_discogs_release_youtube(metadata) # match metadata and save matches
        yt_searcher.audio_download_analyze(metadata) # download matches
        
        # create qr code with cover background
        generate_qr_code_advanced(self.release_folder, release_id, metadata)
        
        # create latex labels
        create_latex_label_file(self.release_folder, metadata)
    
    def regenerate_latex_label(self, release_id):
        """Regeneriert nur das LaTeX-Label für ein bestehendes Release ohne Sync-Operationen"""
        try:
            logger.debug(f"Regenerating label for release ID: {release_id}")
            
            # Finde Release-Ordner
            release_folder = None
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    release_folder = item
                    logger.debug(f"Found release folder: {release_folder.name}")
                    break
            else:
                logger.error(f"Release folder not found for ID: {release_id} in {self.library_path}")
                return False
            
            # Lade bestehende Metadaten
            metadata_file = release_folder / 'metadata.json'
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id} at {metadata_file}")
                return False
            
            logger.debug(f"Loading metadata from: {metadata_file}")
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Erstelle neues LaTeX-Label (überschreibt bestehende)
            logger.debug(f"Creating LaTeX label for: {metadata.get('title', 'Unknown')}")
            result = create_latex_label_file(str(release_folder), metadata)
            
            if result:
                logger.debug(f"✓ Successfully regenerated LaTeX label for release {release_id}")
                # Überprüfe ob die Datei wirklich erstellt wurde
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
        """Regeneriert LaTeX-Labels und/oder Waveforms für alle bestehenden Releases"""
        local_ids = set(self.get_local_release_ids())
        
        if not local_ids:
            logger.warning("No local releases found for regeneration")
            return
        
        logger.info(f"Found {len(local_ids)} local releases for regeneration")
        
        # Sortiere für konsistente Reihenfolge
        releases_to_process = sorted(list(local_ids))
        
        # Progress Bar für Regeneration
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
                
                # Logging für Erfolg/Fehler
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
        """Verarbeitet bestehende Releases offline ohne Discogs/YouTube Sync"""
        local_ids = set(self.get_local_release_ids())
        
        if not local_ids:
            logger.warning("No local releases found for offline processing")
            return
        
        logger.info(f"Found {len(local_ids)} local releases for offline processing")
        
        # Sortiere für konsistente Reihenfolge
        releases_to_process = sorted(list(local_ids))
        
        with tqdm(total=len(releases_to_process), desc="Processing offline", unit="release") as pbar:
            for release_id in releases_to_process:
                try:
                    # Finde Release-Ordner
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
                    
                    # Lade Metadaten
                    metadata_file = release_folder / 'metadata.json'
                    if not metadata_file.exists():
                        logger.warning(f"No metadata.json found for release {release_id}")
                        pbar.update(1)
                        continue
                    
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    logger.debug(f"Processing offline: {release_id}")
                    
                    # 1. Audio-Analyse (falls noch nicht vorhanden)
                    self._process_audio_analysis_offline(metadata)
                    
                    # 2. QR-Code Generierung (sowohl einfach als auch fancy)
                    generate_qr_code_advanced(self.release_folder, release_id, metadata)
                    
                    # 3. LaTeX Label erstellen/aktualisieren
                    create_latex_label_file(self.release_folder, metadata)
                    
                except Exception as e:
                    logger.error(f"Error processing release {release_id} offline: {e}")
                
                pbar.update(1)
        
        logger.success(f"Offline processing completed for {len(releases_to_process)} releases!")
    
    def _process_audio_analysis_offline(self, metadata):
        """Führt Audio-Analyse für existierende Dateien durch falls noch nicht vorhanden"""
        from analyzeSoundFile import analyzeAudioFileOrStream
        
        for track in metadata.get('tracklist', []):
            track_pos = track.get('position', '')
            if not track_pos:
                continue
            
            # Suche nach Audio-Datei
            audio_extensions = ['.opus', '.mp3', '.wav', '.m4a', '.ogg']
            audio_file = None
            
            for ext in audio_extensions:
                potential_file = self.release_folder / f"{track_pos}{ext}"
                if potential_file.exists():
                    audio_file = potential_file
                    break
            
            if not audio_file:
                continue
            
            # Prüfe ob Analyse bereits existiert
            analysis_file = self.release_folder / f"{track_pos}.json"
            waveform_file = self.release_folder / f"{track_pos}_waveform.png"
            
            if analysis_file.exists() and waveform_file.exists():
                continue  # Bereits analysiert
            
            try:
                logger.debug(f"Analyzing audio file: {audio_file.name}")
                analyzer = analyzeAudioFileOrStream(str(audio_file))
                
                # Analyse nur durchführen wenn noch nicht vorhanden
                if not analysis_file.exists():
                    analyzer.music_analyze()
                
                # Waveform nur generieren wenn noch nicht vorhanden
                if not waveform_file.exists():
                    analyzer.generate_waveform_gnuplot()
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {audio_file.name}: {e}")
    
    def regenerate_waveforms(self, release_id):
        """Regeneriert alle Waveforms für ein bestehendes Release"""
        try:
            # Finde Release-Ordner
            release_folder = None
            for item in self.library_path.iterdir():
                if item.is_dir() and item.name.startswith(f"{release_id}_"):
                    release_folder = item
                    break
            else:
                logger.error(f"Release folder not found for ID: {release_id}")
                return False
            
            # Lade Metadaten für Tracklist
            metadata_file = release_folder / 'metadata.json'
            if not metadata_file.exists():
                logger.error(f"No metadata.json found for release {release_id}")
                return False
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Finde alle Audio-Dateien und regeneriere Waveforms
            from analyzeSoundFile import analyzeAudioFileOrStream
            
            waveforms_generated = 0
            for track in metadata.get('tracklist', []):
                track_pos = track.get('position', '')
                if not track_pos:
                    continue
                
                # Suche nach Audio-Datei
                audio_file = None
                for ext in ['.opus', '.m4a', '.mp3', '.wav']:
                    potential_file = release_folder / f"{track_pos}{ext}"
                    if potential_file.exists():
                        audio_file = potential_file
                        break
                
                if audio_file:
                    try:
                        # Initialisiere Audio-Analyzer
                        analyzer = analyzeAudioFileOrStream(str(audio_file))
                        analyzer.load_audio()
                        
                        # Generiere Waveform
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
            

