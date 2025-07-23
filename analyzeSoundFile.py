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
import matplotlib.pyplot as plt



class analyzeAudioFileOrStream:
    def __init__(self, fileOrStream, sampleRate=44100, waveForm=False, bpmAnalysis=True, keyAnalysis=True, MfccAnalysis=False, overwrite=False, debug=False, ffmpeg=False):
        self.fileOrStream = fileOrStream
        self.sampleRate = sampleRate
        self.waveForm = waveForm
        self.bpmAnalysis = bpmAnalysis
        self.keyAnalysis = keyAnalysis
        self.overwrite = overwrite
        self.debug = debug
        self.get_ffmpeg_command()
        self.ffmpegUsage = ffmpeg
        self.MfccAnalysis = MfccAnalysis
        
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
            # self.duration = librosa.get_duration(y=self.audioData, sr=self.sampleRate)
            
        else:
            loader = es.MonoLoader(filename=self.fileOrStream)
            self.audioData = loader()
            self.duration = len(self.audioData)/self.sampleRate

        
        if self.debug:
            print(f"Datei geladen. Länge: {self.duration:.2f} Sekunden")

        # BPM analysieren
        if self.bpmAnalysis:
            self.analyzeBPM()
        # KEY analysieren
        if self.keyAnalysis:
            self.analyzeKey()
        # MFCC erstellen:
        if self.MfccAnalysis:    
            self.analyzeMFCC()
            

    def analyzeBPM(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")

        # ------- BPM (Tempo) Analyse -------
        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        self.bpm, _, _, _, _ = rhythm_extractor(self.audioData)
        print("BPM:", self.bpm)

        if self.debug:
            print(f"Erkannte BPM: {self.bpm}")
            
    def analyzeKey(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
    
        # ------- Tonart (Key) Analyse -------
        key_extractor = es.KeyExtractor()
        key, scale, strength = key_extractor(self.audioData)
    
        self.key = key
        self.scale = scale
        self.key_strength = strength
    
        if self.debug:
            print(f"Key: {key}, Scale: {scale}, Stärke: {strength}")
            
    def analyzeMFCC(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
    
        # Schritt 1: Frame- und Windowing
        frame_size = 1024
        hop_size = 512
    
        # Vorbereitung
        window = es.Windowing(type='hann')
        spectrum = es.Spectrum()
        mfcc = es.MFCC(numberCoefficients=13)
    
        mfccs = []
    
        # Iteriere über Frames
        for frame in essentia.standard.FrameGenerator(self.audioData, frameSize=frame_size, hopSize=hop_size, startFromZero=True):
            win = window(frame)
            spec = spectrum(win)
            mfcc_bands, mfcc_coeffs = mfcc(spec)
            mfccs.append(mfcc_coeffs)
    
        self.mfcc = mfccs
    
        print(f"MFCCs extrahiert: {len(mfccs)} Frames mit je {len(mfccs[0])} Koef.")
        if self.debug:
            print("Erste MFCC-Frame:", mfccs[0])  
            
            
    def analyzeDanceability(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        danceability_extractor = es.Danceability()
        self.danceability = danceability_extractor(self.audioData)
        print(f"Danceability: {self.danceability:.2f}")
        if self.debug:
            print(f"Danceability Score: {self.danceability:.2f}")

    def analyzeLoudness(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        loudness = es.Loudness()
        self.loudness_value = loudness(self.audioData)
        print(f"Loudness: {self.loudness_value:.2f} dB")
        if self.debug:
            print(f"Loudness Value: {self.loudness_value:.2f} dB")

    def analyzeDynamicRange(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        dyn_range_extractor = es.DynamicComplexity()
        self.dynamic_complexity = dyn_range_extractor(self.audioData)
        print(f"Dynamische Komplexität: {self.dynamic_complexity:.2f}")
        if self.debug:
            print(f"Dynamic Complexity: {self.dynamic_complexity:.2f}")

    def analyzeOnsets(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        onset_detector = es.OnsetDetection()
        envelope = es.Envelope()
        onsets = []
        # Einfacher Onset Detection über Frames
        for frame in es.FrameGenerator(self.audioData, frameSize=1024, hopSize=512):
            env = envelope(frame)
            onsets.append(onset_detector(env))
        self.onsets = onsets
        print(f"Onset Detection durchgeführt: {len(onsets)} Frames")
        if self.debug:
            print(f"Erste Onsets: {onsets[:10]}")

    def analyzeSpectralFeatures(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        window = es.Windowing(type='hann')
        spectrum = es.Spectrum()
        centroid = es.Centroid()
        spread = es.Spread()
        rolloff = es.Crest()
        flatness = es.FlatnessDB()
        flux = es.Flux()
        spectral_centroids = []
        spectral_spreads = []
        spectral_rolloffs = []
        spectral_flatnesses = []
        spectral_fluxes = []

        prev_spectrum = None

        for frame in es.FrameGenerator(self.audioData, frameSize=1024, hopSize=512):
            win = window(frame)
            spec = spectrum(win)
            spectral_centroids.append(centroid(spec))
            spectral_spreads.append(spread(spec))
            spectral_rolloffs.append(rolloff(spec))
            spectral_flatnesses.append(flatness(spec))
            if prev_spectrum is None:
                flux_value = 0
            else:
                flux_value = flux(prev_spectrum, spec)
            spectral_fluxes.append(flux_value)
            prev_spectrum = spec

        self.spectral_features = {
            'centroid': spectral_centroids,
            'spread': spectral_spreads,
            'rolloff': spectral_rolloffs,
            'flatness': spectral_flatnesses,
            'flux': spectral_fluxes
        }
        print(f"Spektrale Features extrahiert für {len(spectral_centroids)} Frames")
        if self.debug:
            print(f"Erster Spektralcentroid: {spectral_centroids[0]:.2f}")

    def analyzeChords(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        chords_extractor = es.ChordsDetection()
        chords = chords_extractor(self.audioData)
        self.chords = chords
        print(f"Akkorde extrahiert: {len(chords)}")
        if self.debug:
            print("Erste Akkorde:", chords[:10])

    def analyzeTonalClarity(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
        tonal_clarity_extractor = es.TonalClarity()
        tonal_clarity = tonal_clarity_extractor(self.audioData)
        self.tonal_clarity = tonal_clarity
        print(f"Tonal Clarity: {tonal_clarity:.2f}")
        if self.debug:
            print(f"Tonal Clarity Wert: {tonal_clarity:.2f}")
            
            
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
        
        
        # plt.xlabel("Zeit (Sekunden)")
        # plt.ylabel("Amplitude")
        # plt.title("Waveform")
        # plt.grid(True)
        plt.tight_layout()
        plt.show()

        if self.debug:
            print(f"Waveform geplottet: Länge {len(self.audioData)} Samples, Dauer {zeit[-1]:.2f} Sekunden")
            
            
    def analyzeMusicExtractor(self):
        if self.audioData is None:
            raise RuntimeError("Audio wurde noch nicht geladen.")
            
        # results_file = self.fileorStream
        results_file = "A1"

        extractor = es.MusicExtractor()
        features, _ = extractor(self.fileOrStream)

        # Beispiel für häufige AcousticBrainz-ähnliche Features
        self.bpm = features['rhythm.bpm']
        self.key = features['tonal.key.key']
        self.scale = features['tonal.key.scale']
        self.danceability = features['danceability']
        self.loudness = features['lowlevel.loudness']
        self.tonal_complexity = features.get('tonal.tonalComplexity', None)

        print(f"BPM: {self.bpm:.2f}")
        print(f"Tonart: {self.key} {self.scale}")
        print(f"Danceability: {self.danceability:.2f}")
        print(f"Loudness: {self.loudness:.2f}")
        if self.tonal_complexity is not None:
            print(f"Tonal Complexity: {self.tonal_complexity:.2f}")

        if self.debug:
            # Alle Keys ausgeben (kann sehr lang sein)
            print("Alle extrahierten Features:")
            for k, v in features.items():
                print(f"  {k}: {v}")
                
        es.YamlOutput(filename=results_file, format="json")(features)
