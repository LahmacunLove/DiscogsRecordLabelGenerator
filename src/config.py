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
    # Load the configuration file and read it as JSON
    config_file = Path(config_path).expanduser()
    
    # Check if the configuration file exists
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    # Load the configuration file
    with open(config_file, "r") as f:
        config = json.load(f)

    # If LIBRARY_PATH contains variables, expand them
    if "LIBRARY_PATH" in config:
        config["LIBRARY_PATH"] = os.path.expandvars(config["LIBRARY_PATH"])
    
    print("Configuration loaded.")
    return config

def get_config_path():
    """Return the path to the configuration file"""
    return Path("~/.config/discogsDBLabelGen/discogs.env").expanduser()
    