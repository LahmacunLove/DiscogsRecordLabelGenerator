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
            
            # Gnuplot-Script-Pfad (korrekt für src/ Struktur)
            gnuplot_script_path = os.path.join(os.path.dirname(__file__), "waveform.gnuplot")
            if not os.path.exists(gnuplot_script_path):
                logger.error(f"Gnuplot script not found: {gnuplot_script_path}")
                logger.debug(f"Searched at: {gnuplot_script_path}")
                logger.debug(f"__file__ directory: {os.path.dirname(__file__)}")
                return False
            
            # Erstelle temporäres gnuplot-Script mit korrektem Output-Pfad
            import tempfile
            temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.gnuplot', delete=False)
            
            # Lade Original-Script und setze korrekten Output-Pfad
            with open(gnuplot_script_path, 'r') as original:
                script_content = original.read()
            
            # Ersetze Output-Pfad im Script
            script_content = script_content.replace(
                "# Output wird von Command-Line gesetzt\n# set output 'waveform.png';",
                f"set output '{waveform_file}';"
            )
            
            temp_script.write(script_content)
            temp_script.close()
            
            # Gnuplot-Befehl mit temporärem Script
            gnuplot_command = ['gnuplot', temp_script.name]
            
            # FFmpeg-Prozess starten
            ffmpeg_pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Gnuplot-Prozess starten und FFmpeg-Output weiterleiten
            plot = subprocess.Popen(gnuplot_command, stdin=ffmpeg_pipe.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Warten bis beide Prozesse fertig sind
            ffmpeg_pipe.stdout.close()
            plot_output, plot_error = plot.communicate()
            ffmpeg_output, ffmpeg_error = ffmpeg_pipe.communicate()
            
            # Prüfe Ergebnisse
            if plot.returncode != 0:
                logger.error(f"Gnuplot error (return code {plot.returncode}): {plot_error.decode()}")
                return False
                
            if ffmpeg_pipe.returncode != 0:
                logger.error(f"FFmpeg error (return code {ffmpeg_pipe.returncode}): {ffmpeg_error.decode()}")
                return False
            
            # Prüfe ob die Datei erstellt wurde
            if os.path.exists(waveform_file) and os.path.getsize(waveform_file) > 0:
                logger.success(f"Waveform generated: {os.path.basename(waveform_file)}")
                # Cleanup temporäres Script
                try:
                    os.unlink(temp_script.name)
                except:
                    pass
                return True
            else:
                logger.error(f"Waveform generation failed - no output file created at {waveform_file}")
                if plot_error:
                    logger.debug(f"Gnuplot stderr: {plot_error.decode()}")
                if ffmpeg_error:
                    logger.debug(f"FFmpeg stderr: {ffmpeg_error.decode()}")
                # Cleanup temporäres Script
                try:
                    os.unlink(temp_script.name)
                except:
                    pass
                return False
                
        except Exception as e:
            logger.error(f"Error generating waveform: {e}")
            # Cleanup temporäres Script
            try:
                os.unlink(temp_script.name)
            except:
                pass
            return False
    
    def generate_waveform(self):
        """Generiert Waveform mit gnuplot (einzige Methode)"""
        return self.generate_waveform_gnuplot()
    