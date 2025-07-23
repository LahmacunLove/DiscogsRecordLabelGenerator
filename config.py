#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 19:25:45 2025

@author: ffx
"""

import os
from pathlib import Path
import json

def load_config(config_path="~/.config/discogsDBLabelGen/discogs.env"):
    # Lade die Konfigurationsdatei und lese sie als JSON
    config_file = Path(config_path).expanduser()
    
    # Überprüfen, ob die Konfigurationsdatei existiert
    if not config_file.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {config_file}")
    
    # Lade die Konfigurationsdatei
    with open(config_file, "r") as f:
        config = json.load(f)

    # Wenn der Pfad LIBRARY_PATH enthält, löse $HOME auf
    if "LIBRARY_PATH" in config:
        config["LIBRARY_PATH"] = os.path.expandvars(config["LIBRARY_PATH"])
    
    print("Config geladen.")
    return config

    