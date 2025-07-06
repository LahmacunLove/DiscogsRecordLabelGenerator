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
import urllib.request
import youtube_handler


import json
import shutil
import re

class DiscogsLibraryMirror:
    def __init__(self):
        self.config = load_config()
        self.discogs = self._init_discogs_client()
        self.library_path = Path(self.config["LIBRARY_PATH"]).expanduser()
        self.user = self.discogs.identity()
        self.username = self.user.username

    def _init_discogs_client(self):
        token = self.config.get("DISCOGS_USER_TOKEN")
        if not token:
            raise ValueError("Discogs-Token fehlt in der Config.")
        return discogs_client.Client("DiscogsDBLabelGen/0.1", user_token=token)

    def get_collection_release_ids(self):
      
       folder = self.discogs.user(self.username).collection_folders[0]  # "All" Folder
       release_ids = []
       
       print("Lade alle releaseIDs von Collection...")
       page = 1  # start page?
       
       while True:
           releases = folder.releases.page(page)  # Holt Releases der aktuellen Seite
           # print(len(folder.releases.page(page)))
           for release in releases:
               release_ids.append(release.release.id)
       
           # Wenn die aktuelle Seite weniger als per_page Releases hat, könnten wir fertig sein
           if len(releases) < 100: # hier später auf 50 ändern, für ganze lib
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
        release_folder = self.library_path / f"{release_id}_{metadata.get('title', release_id)}"
        release_folder.mkdir(parents=True, exist_ok=True)
        
        # Speichern der gesamten Metadaten als JSON-Datei
        metadata_path = release_folder / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    
        print(f"Release {release_id} gespeichert.") 
        

    def delete_release_folder(self, release_id):
        """Löscht einen Ordner, der ein Release enthält, falls das Release nicht mehr existiert."""
        # release_folder = self.library_path / f"{release_id}"
        if self.release_folder.exists() and self.release_folder.is_dir():
            print(f"Lösche Release: {release_id}")
            shutil.rmtree(self.release_folder)
            
    def convert_to_datetime(self,datetime_string):
        tz_offset = datetime.strptime(datetime_string[-5:], "%H:%M")
        return datetime.strptime(datetime_string[:-6], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=tz_offset.hour)
            
            
    def sync_single_release(self, release_id):
        # Neue Releases speichern
        collectionElement = self.discogs.release(release_id)  # Holt die Metadaten hier stimmt was nicht
        timestamp = self.discogs.user(self.username).collection_items(release_id)[0].data['date_added']
        
        print(collectionElement.url)
        
        try:
            print(collectionElement.apple)
            
            print("done")
        except:
            pass
        # Metadaten sammeln
        metaData = {
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
            
        metaData["tracklist"] = tracklist
        
        self.release_folder = self.library_path / f"{release_id}_{metaData.get('title', release_id)}" 
        
        # do all discogs stuff
        self.save_release_metadata(release_id, metaData)
        self.saveCoverArt(release_id, metaData)
        
        # do all youtube stuff (comparision with apple music? i there metadata?)
        yt_searcher = youtube_handler.YouTubeMatcher()
        # yt_searcher.fetch_release_metadata(metaData["videos"])
        yt_searcher.download(metaData, self.release_folder)
        
            
            
        # yt_searcher.match_discogs_videos_to_tracks(metaData, output_path=self.release_folder)
        # yt_searcher.search_release_tracks(release_id, metaData, self.release_folder )

        # analyze track
        
        # create LaTeX snippet?
            # - qr code
        
        # out of loop, create LaTeX full sheet
        
        return
        
        
    def saveCoverArt(self, release_id, metaData):
        try:
            imageURL = self.discogs.release(release_id).images[0]['uri']
        except:
            imageURL = None
            
        if imageURL !=  None:
            try:
                print("downloading Cover of " + str(release_id))
                
                # urllib.request.urlretrieve(imageURL, os.path.join(elementDirectory, "cover.jpg"))
                req = urllib.request.Request(
                    imageURL,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
    
                with urllib.request.urlopen(req) as response, \
                    open(os.path.join(self.release_folder, "cover.jpg"), 'wb') as out_file:
                    out_file.write(response.read())
            except:
                pass
        return
            
            
            
    def sync_releases(self):
        """Vergleicht die Releases und speichert neue Releases oder löscht gelöschte Releases."""
        # IDs von Discogs und lokalen Releases
        discogs_ids = set(self.get_collection_release_ids())
        local_ids = set(self.get_local_release_ids())

        # Neue Releases speichern
        new_ids = discogs_ids - local_ids
        for release_id in new_ids:
            print(f"Neues Release gefunden: {release_id}")
            self.sync_single_release(release_id)

        # Gelöschte Releases entfernen
        removed_ids = local_ids - discogs_ids
        for release_id in removed_ids:
            print(f"Release entfernt: {release_id}")
            self.delete_release_folder(release_id)
