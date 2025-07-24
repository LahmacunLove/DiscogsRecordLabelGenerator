#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Wed Jul 23 13:31:13 2025

@author: ffx
"""

import os
# import librosa
# import time
import shutil

import subprocess
import numpy as np
# import keyfinder
import essentia
import essentia.standard as es

from pylab import plot, show, figure, imshow
# %matplotlib inline
import matplotlib.pyplot as plt
import matplotlib.colors as colors



class analyzeAudioFileOrStream:
    def __init__(self, fileOrStream, sampleRate=44100, plotWaveform=False, musicExtractor=True, plotSpectogram=True, debug=True):
        self.fileOrStream = fileOrStream
        self.sampleRate = sampleRate
        self.debug = debug
        self.musicExtractor = musicExtractor
        self.plotWaveform = plotWaveform
        self.plotSpectogram = plotSpectogram
        self.get_ffmpeg_command()
        
        self.audioData = None
        self.duration = None
        self.bpm = None
        self.key = None
        
    def analyzeMusicExtractor(self):
        features, features_frames = es.MusicExtractor(lowlevelStats=['mean', 'stdev'],
                                                      rhythmStats=['mean', 'stdev'],
                                                      tonalStats=['mean', 'stdev'])(self.fileOrStream)
        #set filename for json export:
        filename = os.path.splitext(self.fileOrStream)[0] + '.json'
        # export data to json:
        es.YamlOutput(filename=filename, format="json")(features)
        
        if self.plotSpectogram:
            filename = os.path.splitext(self.fileOrStream)[0] + '_Mel-spectogram.png'
            plt.rcParams['figure.figsize'] = (15, 6) # set plot sizes to something larger than default

            imshow(features_frames['lowlevel.melbands128'].T,
                   aspect='auto', origin='lower', interpolation='none', norm=colors.LogNorm())
            plt.title("Mel-spectrogram (128 bins)")
            plt.savefig(filename, bbox_inches='tight')
            
            filename = os.path.splitext(self.fileOrStream)[0] + '_HPCP_chromatogram.png'
            imshow(features_frames['tonal.hpcp'].T,
                   aspect='auto', origin='lower', interpolation='none', norm=colors.LogNorm())
            plt.title("HPCP (chroma) 36 bins)")
            plt.savefig(filename, bbox_inches='tight')
            
        return


        
        
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
            # self.duration = librosa.get_duration(y=self.audioData, sr=self.sampleRate)
            
        else:
            loader = es.MonoLoader(filename=self.fileOrStream)
            self.audioData = loader()
            self.duration = len(self.audioData)/self.sampleRate

        
        if self.debug:
            print(f"Datei geladen. Länge: {self.duration:.2f} Sekunden")

            
    def plotWaveform(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")

        # Zeitachse in Sekunden berechnen
        zeit = np.arange(len(self.audioData)) / self.sampleRate

        plt.figure(figsize=(12, 4))
        plt.plot(zeit, self.audioData, color='black')
        
        # Keine Achsen, kein Rahmen, kein Grid
        plt.axis('off')
        plt.gca().set_frame_on(False)
        
        plt.tight_layout(pad=0)
        plt.show()
        
        plt.tight_layout()
        plt.show()

        if self.debug:
            print(f"Waveform geplottet: Länge {len(self.audioData)} Samples, Dauer {zeit[-1]:.2f} Sekunden")
    