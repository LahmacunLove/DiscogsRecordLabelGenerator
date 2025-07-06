#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  5 15:10:24 2025

@author: ffx
"""

import time
import argparse
from mirror import DiscogsLibraryMirror
from pathlib import Path
from config import load_config
import discogs_client
from pytube import YouTube
import time
from yt_dlp import YoutubeDL


# library_mirror = DiscogsLibraryMirror() # connect zur lib

# release_id = 30685762
# metadata = library_mirror.discogs.release(release_id).data

config = load_config()

token = config["DISCOGS_USER_TOKEN"]
discogs_object = discogs_client.Client("DiscogsDBLabelGen/0.1", user_token=token)

me = discogs_object.identity()

collectionElement = discogs_object.release(15589261)  # Holt die Metadaten hier stimmt was nicht    


url = "https://www.youtube.com/watch?v=O9fV3JjlxVs"

start = time.time()
with YoutubeDL() as ydl:
    info = ydl.extract_info(url, download=False, process=True, force_generic_extractor=False)
    print("Titel:", info['title'])
end = time.time()
print(f"⏱️ Dauer: {end - start:.3f} Sekunden")    


 # user = self.discogs.identity()
 # self.username = user.username
 # folder = self.discogs.user(self.username).collection_folders[0]  # "All" Folder
 # release_ids = []