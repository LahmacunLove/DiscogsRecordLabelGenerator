#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 17:04:49 2025

@author: ffx
"""

import os
import librosa
import time
import shutil

import subprocess
import numpy as np
from analyzeSoundFile import analyzeAudioFileOrStream
import matplotlib.pyplot as plt
import essentia
import essentia.standard as es

   
#%%  Analysiere Datei in librosa mit gegebener Klasse:

soundfile = "/home/ffx/.cache/discogsLibary/discogsLib/10765213_When Lobster Comes Home/A1.opus"

































#%%

# only librosa:
start_time = time.time()
analyzer = analyzeAudioFileOrStream(soundfile, debug=True, bpmAnalysis=False, MfccAnalysis=False, keyAnalysis=False,  sampleRate=44100)
analyzer.readAudioFile()

# analyzer.analyzeBPM()
# analyzer.analyzeKey()
# analyzer.analyzeDanceability()
# analyzer.analyzeDynamicRange()
# analyzer.analyzeOnsets()
# analyzer.analyzeSpectralFeatures()
# analyzer.analyzeChords()
# analyzer.analyzeTonalClarity()
# analyzer.plotWaveform()
analyzer.analyzeMusicExtractor()

duration = time.time() - start_time
# Ausgabe der Dauer
print("--------------------------------")
print(f"datei einlsen hat {duration:.2f} Sekunden benötigt.\n\n")
