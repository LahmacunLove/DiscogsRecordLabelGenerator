#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Wed Jul 23 13:31:13 2025

@author: ffx
"""

import os
import librosa
import time
import shutil

import subprocess
import numpy as np
# import keyfinder



class analyzeAudioFileOrStream:
    def __init__(self, fileOrStream, sampleRate=44100, waveForm=False, bpmAnalysis=True, keyAnalysis=True, overwrite=False, debug=False, ffmpeg=False):
        self.fileOrStream = fileOrStream
        self.sampleRate = sampleRate
        self.waveForm = waveForm
        self.bpmAnalysis = bpmAnalysis
        self.keyAnalysis = keyAnalysis
        self.overwrite = overwrite
        self.debug = debug
        self.get_ffmpeg_command()
        self.ffmpegUsage = ffmpeg
        
        self.audioData = None
        self.duration = None
        self.bpm = None
        self.key = None
        
    def get_ffmpeg_command(self):
        """
        Gibt den vollständigen Pfad zum ffmpeg-Befehl zurück, falls vorhanden.
        Gibt None zurück, wenn ffmpeg nicht installiert oder nicht im PATH ist.
        """
        self.ffmpeg_path = shutil.which("ffmpeg")
        

    def readAudioFile(self, ffmpegUsage=False):
        # Prüfen, ob Datei existiert
        if not os.path.isfile(self.fileOrStream):
            raise FileNotFoundError(f"Datei nicht gefunden: {self.fileOrStream}")
        
        if self.debug:
            print(f"Lade Datei: {self.fileOrStream}")
        
        # Audio laden
        if self.ffmpegUsage and self.ffmpeg_path !=  None:
            print("nutze ffmpeg")
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', self.fileOrStream,
                '-f', 'f32le',       # 32-bit float little endian (librosa-kompatibel)
                '-acodec', 'pcm_f32le',
                '-ar', str(self.sampleRate),      # Ziel-Samplerate (optional)
                '-ac', '1',          # Mono
                '-hide_banner',
                '-loglevel', 'error',
                '-'
            ]
            
            # FFmpeg starten und den Audio-Stream einlesen
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
            
            # Audio-Rohdaten in NumPy-Array laden
            self.rawAudioStream = process.stdout.read()
            self.audioData = np.frombuffer(self.rawAudioStream, dtype=np.float32)
            self.duration = librosa.get_duration(y=self.audioData, sr=self.sampleRate)
            
        else:
            self.audioData, _ = librosa.load(self.fileOrStream, sr=self.sampleRate, mono=True)
            self.duration = librosa.get_duration(y=self.audioData, sr=self.sampleRate)    
        
        if self.debug:
            print(f"Datei geladen. Länge: {self.duration:.2f} Sekunden")

        # BPM analysieren
        if self.bpmAnalysis:
            self.analyzeBPM()

        # Weitere Analysen (Key etc.) könntest du hier ergänzen...

    def analyzeBPM(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")

        tempo, _ = librosa.beat.beat_track(y=self.audioData, sr=self.sampleRate)
        self.bpm = tempo

        if self.debug:
            print(f"Erkannte BPM: {self.bpm}")

