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
from logger import logger
import time



class analyzeAudioFileOrStream:
    def __init__(self, fileOrStream, sampleRate=44100, plotWaveform=False, musicExtractor=True, plotSpectogram=True, debug=True):
        self.fileOrStream = fileOrStream
        self.sampleRate = sampleRate
        self.debug = debug
        self.musicExtractor = musicExtractor
        self.plotWaveform = plotWaveform
        self.plotSpectogram = plotSpectogram
        self.get_ffmpeg_command()
        self.get_gnuplot_path()
        
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
        
    def get_gnuplot_path(self):
        """
        Prüft, ob gnuplot installiert ist. Falls ja, gibt gnuplot zurück, falls nein, gibt None zurück.
        
        Returns:
        - str: Pfad zu gnuplot oder None
        """
        self.gnuplot_path = shutil.which("gnuplot")
        

    def readAudioFile(self, ffmpegUsage=False):
        # Prüfen, ob Datei existiert
        if not os.path.isfile(self.fileOrStream):
            raise FileNotFoundError(f"Datei nicht gefunden: {self.fileOrStream}")
        
        if self.debug:
            print(f"Lade Datei: {self.fileOrStream}")
        
        # Audio laden
        if ffmpegUsage and hasattr(self, 'ffmpeg_path') and self.ffmpeg_path is not None:
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
    
    def generate_waveform_gnuplot(self):
        """Generiert Waveform mit gnuplot (schnellste Methode aus altem Code)"""
        if not hasattr(self, 'gnuplot_path') or self.gnuplot_path is None:
            logger.warning("gnuplot not found in PATH - skipping waveform generation")
            return False
            
        # Prüfe ob Audio-Datei existiert
        if not os.path.isfile(self.fileOrStream):
            logger.error(f"Audio file not found: {self.fileOrStream}")
            return False
            
        # Pfad für Waveform-PNG
        waveform_file = os.path.splitext(self.fileOrStream)[0] + "_waveform.png"
        
        # Prüfe ob bereits existiert
        if os.path.exists(waveform_file):
            logger.debug(f"Waveform already exists: {os.path.basename(waveform_file)}")
            return True
            
        try:
            logger.process(f"Generating waveform with gnuplot: {os.path.basename(waveform_file)}")
            
            # FFmpeg für PCM-Daten (16-bit für gnuplot)
            ffmpeg_command = [
                "ffmpeg", "-i", self.fileOrStream,
                "-ac", "1", 
                "-filter:a", f"aresample={self.sampleRate}",
                "-map", "0:a", 
                "-c:a", "pcm_s16le", 
                "-f", "data", 
                "-hide_banner", "-loglevel", "error",
                '-'
            ]
            
            # Gnuplot-Befehl
            gnuplot_script_path = os.path.join(os.path.dirname(__file__), "waveform.gnuplot")
            if not os.path.exists(gnuplot_script_path):
                logger.error(f"Gnuplot script not found: {gnuplot_script_path}")
                return False
                
            gnuplot_command = [
                'gnuplot', '-persist', '-c', gnuplot_script_path
            ]
            
            # FFmpeg-Prozess starten
            ffmpeg_pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Gnuplot-Prozess starten und FFmpeg-Output weiterleiten
            plot = subprocess.Popen(gnuplot_command, stdin=ffmpeg_pipe.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Warten bis beide Prozesse fertig sind
            ffmpeg_pipe.stdout.close()
            plot_output, plot_error = plot.communicate()
            ffmpeg_pipe.wait()
            
            # Waveform-Datei zum korrekten Ort verschieben
            if os.path.isfile("waveform.png"):
                shutil.move("waveform.png", waveform_file)
                logger.debug(f"Waveform generated: {os.path.basename(waveform_file)}")
                return True
            else:
                if plot_error:
                    logger.error(f"Gnuplot error: {plot_error.decode()}")
                logger.error("Waveform generation failed - no output file created")
                return False
                
        except Exception as e:
            logger.error(f"Error generating waveform: {e}")
            return False
    
    def generate_waveform_essentia(self):
        """Generiert Waveform mit Essentia und matplotlib (Alternative zu gnuplot)"""
        if not hasattr(self, 'audioData') or self.audioData is None:
            logger.warning("No audio data loaded - loading audio first")
            try:
                self.readAudioFile(ffmpegUsage=False)
            except Exception as e:
                logger.error(f"Failed to load audio for Essentia waveform: {e}")
                return False
        
        # Pfad für Waveform-PNG
        waveform_file = os.path.splitext(self.fileOrStream)[0] + "_waveform_essentia.png"
        
        # Prüfe ob bereits existiert
        if os.path.exists(waveform_file):
            logger.debug(f"Essentia waveform already exists: {os.path.basename(waveform_file)}")
            return True
        
        try:
            start_time = time.time()
            logger.process(f"Generating Essentia waveform: {os.path.basename(waveform_file)}")
            
            # Erstelle Zeitachse
            duration = len(self.audioData) / self.sampleRate
            time_axis = np.linspace(0, duration, len(self.audioData))
            
            # Downsampling für Performance (optional)
            downsample_factor = max(1, len(self.audioData) // 2500)  # Max 2500 Punkte für Waveform
            if downsample_factor > 1:
                audio_downsampled = self.audioData[::downsample_factor]
                time_downsampled = time_axis[::downsample_factor]
            else:
                audio_downsampled = self.audioData
                time_downsampled = time_axis
            
            # Erstelle Plot mit gleichen Dimensionen wie gnuplot (2500x250)
            plt.figure(figsize=(10, 1), dpi=250)  # 2500x250 px bei 250 DPI
            plt.plot(time_downsampled, audio_downsampled, color='black', linewidth=0.5)
            
            # Entferne alle Achsen und Rahmen (wie gnuplot Version)
            plt.axis('off')
            plt.gca().set_frame_on(False)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
            
            # Speichere als PNG
            plt.savefig(waveform_file, 
                       bbox_inches='tight', 
                       pad_inches=0, 
                       facecolor='white',
                       edgecolor='none',
                       dpi=250)
            plt.close()  # Wichtig: Schließe Plot um Memory zu sparen
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            logger.debug(f"Essentia waveform generated in {generation_time:.2f}s: {os.path.basename(waveform_file)}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Essentia waveform: {e}")
            return False
    
    def generate_both_waveforms_benchmark(self):
        """Generiert beide Waveform-Arten und vergleicht Performance"""
        if not os.path.isfile(self.fileOrStream):
            logger.error(f"Audio file not found: {self.fileOrStream}")
            return False
            
        logger.info(f"🏁 Starting waveform generation benchmark for: {os.path.basename(self.fileOrStream)}")
        
        # Test gnuplot Methode
        gnuplot_start = time.time()
        gnuplot_success = self.generate_waveform_gnuplot()
        gnuplot_time = time.time() - gnuplot_start
        
        # Test Essentia Methode
        essentia_start = time.time()
        essentia_success = self.generate_waveform_essentia()
        essentia_time = time.time() - essentia_start
        
        # Vergleiche Performance
        logger.info("📊 Waveform Generation Benchmark Results:")
        logger.info(f"   🔧 gnuplot method: {gnuplot_time:.3f}s {'✅' if gnuplot_success else '❌'}")
        logger.info(f"   🎵 Essentia method: {essentia_time:.3f}s {'✅' if essentia_success else '❌'}")
        
        if gnuplot_success and essentia_success:
            speed_ratio = gnuplot_time / essentia_time
            if speed_ratio > 1:
                logger.info(f"   🏆 Essentia is {speed_ratio:.1f}x faster than gnuplot")
            else:
                logger.info(f"   🏆 gnuplot is {1/speed_ratio:.1f}x faster than Essentia")
        
        return gnuplot_success or essentia_success
    