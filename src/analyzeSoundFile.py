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
    def __init__(
        self,
        fileOrStream,
        sampleRate=44100,
        plotWaveform=False,
        musicExtractor=True,
        plotSpectogram=True,
        debug=True,
    ):
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
        import tempfile

        # Check if file is Opus format - Essentia's MusicExtractor doesn't support Opus
        file_to_analyze = self.fileOrStream
        temp_wav_file = None

        if self.fileOrStream.lower().endswith(".opus"):
            # Convert Opus to temporary WAV file for Essentia
            if hasattr(self, "ffmpeg_path") and self.ffmpeg_path is not None:
                logger.debug(
                    f"Converting Opus to WAV for Essentia analysis: {os.path.basename(self.fileOrStream)}"
                )

                # Create temporary WAV file
                temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_wav_path = temp_wav_file.name
                temp_wav_file.close()

                # Convert Opus to WAV using FFmpeg
                ffmpeg_cmd = [
                    self.ffmpeg_path,
                    "-i",
                    self.fileOrStream,
                    "-ar",
                    str(self.sampleRate),
                    "-ac",
                    "1",  # Mono
                    "-y",  # Overwrite output file
                    "-loglevel",
                    "error",
                    temp_wav_path,
                ]

                try:
                    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                    file_to_analyze = temp_wav_path
                    logger.debug(f"Temporary WAV created: {temp_wav_path}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
                    # Clean up temp file
                    try:
                        os.unlink(temp_wav_path)
                    except:
                        pass
                    raise
            else:
                logger.error(
                    "FFmpeg not available - cannot convert Opus file for Essentia"
                )
                raise RuntimeError("FFmpeg required for Opus file analysis")

        try:
            # Run MusicExtractor on the file (original or converted WAV)
            features, features_frames = es.MusicExtractor(
                lowlevelStats=["mean", "stdev"],
                rhythmStats=["mean", "stdev"],
                tonalStats=["mean", "stdev"],
            )(file_to_analyze)

            # set filename for json export (use original filename, not temp WAV):
            filename = os.path.splitext(self.fileOrStream)[0] + ".json"
            # export data to json:
            es.YamlOutput(filename=filename, format="json")(features)

            if self.plotSpectogram:
                filename = (
                    os.path.splitext(self.fileOrStream)[0] + "_Mel-spectogram.png"
                )
                plt.rcParams["figure.figsize"] = (
                    15,
                    6,
                )  # set plot sizes to something larger than default

                imshow(
                    features_frames["lowlevel.melbands128"].T,
                    aspect="auto",
                    origin="lower",
                    interpolation="none",
                    norm=colors.LogNorm(),
                )
                plt.title("Mel-spectrogram (128 bins)")
                plt.savefig(filename, bbox_inches="tight")

                filename = (
                    os.path.splitext(self.fileOrStream)[0] + "_HPCP_chromatogram.png"
                )
                imshow(
                    features_frames["tonal.hpcp"].T,
                    aspect="auto",
                    origin="lower",
                    interpolation="none",
                    norm=colors.LogNorm(),
                )
                plt.title("HPCP (chroma) 36 bins)")
                plt.savefig(filename, bbox_inches="tight")

        finally:
            # Clean up temporary WAV file if it was created
            if temp_wav_file is not None:
                try:
                    os.unlink(temp_wav_path)
                    logger.debug(f"Cleaned up temporary WAV file")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary WAV file: {e}")

        return

    def get_ffmpeg_command(self):
        """
        Returns the full path to the ffmpeg command if available.
        Returns None if ffmpeg is not installed or not in PATH.
        """
        self.ffmpeg_path = shutil.which("ffmpeg")

    def get_gnuplot_path(self):
        """
        Checks if gnuplot is installed. If yes, returns gnuplot, if no, returns None.

        Returns:
        - str: Path to gnuplot or None
        """
        self.gnuplot_path = shutil.which("gnuplot")

    def readAudioFile(self, ffmpegUsage=False):
        # Check if file exists
        if not os.path.isfile(self.fileOrStream):
            raise FileNotFoundError(f"File not found: {self.fileOrStream}")

        if self.debug:
            print(f"Loading file: {self.fileOrStream}")

        # Load audio
        if (
            ffmpegUsage
            and hasattr(self, "ffmpeg_path")
            and self.ffmpeg_path is not None
        ):
            print("using ffmpeg")

            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                self.fileOrStream,
                "-f",
                "f32le",  # 32-bit float little endian (librosa-compatible)
                "-acodec",
                "pcm_f32le",
                "-ar",
                str(self.sampleRate),  # Target sample rate (optional)
                "-ac",
                "1",  # Mono
                "-hide_banner",
                "-loglevel",
                "error",
                "-",
            ]

            # Start FFmpeg and read the audio stream
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)

            # Load raw audio data into NumPy array
            self.rawAudioStream = process.stdout.read()
            self.audioData = np.frombuffer(self.rawAudioStream, dtype=np.float32)
            # self.duration = librosa.get_duration(y=self.audioData, sr=self.sampleRate)

        else:
            loader = es.MonoLoader(filename=self.fileOrStream)
            self.audioData = loader()
            self.duration = len(self.audioData) / self.sampleRate

        if self.debug:
            print(f"File loaded. Length: {self.duration:.2f} seconds")

    def plotWaveform(self):
        if self.audioData is None:
            raise RuntimeError("Audio has not been loaded yet.")

        # Calculate time axis in seconds
        time_axis = np.arange(len(self.audioData)) / self.sampleRate

        plt.figure(figsize=(12, 4))
        plt.plot(time_axis, self.audioData, color="black")

        # No axes, no frame, no grid
        plt.axis("off")
        plt.gca().set_frame_on(False)

        plt.tight_layout(pad=0)
        plt.show()

        plt.tight_layout()
        plt.show()

        if self.debug:
            print(
                f"Waveform plotted: Length {len(self.audioData)} samples, Duration {time_axis[-1]:.2f} seconds"
            )

    def generate_waveform_gnuplot(self):
        """Generates waveform with gnuplot (fastest method from old code)"""
        if not hasattr(self, "gnuplot_path") or self.gnuplot_path is None:
            logger.warning("gnuplot not found in PATH - skipping waveform generation")
            return False

        # Check if audio file exists
        if not os.path.isfile(self.fileOrStream):
            logger.error(f"Audio file not found: {self.fileOrStream}")
            return False

        # Path for waveform PNG
        waveform_file = os.path.splitext(self.fileOrStream)[0] + "_waveform.png"

        # Check if already exists
        if os.path.exists(waveform_file):
            logger.debug(f"Waveform already exists: {os.path.basename(waveform_file)}")
            return True

        try:
            logger.process(
                f"Generating waveform with gnuplot: {os.path.basename(waveform_file)}"
            )

            # FFmpeg for PCM data (16-bit for gnuplot)
            ffmpeg_command = [
                "ffmpeg",
                "-i",
                self.fileOrStream,
                "-ac",
                "1",
                "-filter:a",
                f"aresample={self.sampleRate}",
                "-map",
                "0:a",
                "-c:a",
                "pcm_s16le",
                "-f",
                "data",
                "-hide_banner",
                "-loglevel",
                "error",
                "-",
            ]

            # Gnuplot script path (correct for src/ structure)
            gnuplot_script_path = os.path.join(
                os.path.dirname(__file__), "waveform.gnuplot"
            )
            if not os.path.exists(gnuplot_script_path):
                logger.error(f"Gnuplot script not found: {gnuplot_script_path}")
                logger.debug(f"Searched at: {gnuplot_script_path}")
                logger.debug(f"__file__ directory: {os.path.dirname(__file__)}")
                return False

            # Create temporary gnuplot script with correct output path
            import tempfile

            temp_script = tempfile.NamedTemporaryFile(
                mode="w", suffix=".gnuplot", delete=False
            )

            # Load original script and set correct output path
            with open(gnuplot_script_path, "r") as original:
                script_content = original.read()

            # Replace output path in script with correct gnuplot quoting
            # Gnuplot requires double quotes for paths with special characters
            gnuplot_safe_path = waveform_file.replace("\\", "\\\\").replace('"', '\\"')
            script_content = script_content.replace(
                "# Output wird von Command-Line gesetzt\n# set output 'waveform.png';",
                f'set output "{gnuplot_safe_path}";',
            )

            temp_script.write(script_content)
            temp_script.close()

            # Gnuplot command with temporary script
            gnuplot_command = ["gnuplot", temp_script.name]

            # Start FFmpeg process
            ffmpeg_pipe = subprocess.Popen(
                ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Start gnuplot process and forward FFmpeg output
            plot = subprocess.Popen(
                gnuplot_command,
                stdin=ffmpeg_pipe.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait until both processes are finished
            ffmpeg_pipe.stdout.close()
            plot_output, plot_error = plot.communicate()
            ffmpeg_output, ffmpeg_error = ffmpeg_pipe.communicate()

            # Check results
            if plot.returncode != 0:
                logger.error(
                    f"Gnuplot error (return code {plot.returncode}): {plot_error.decode()}"
                )
                return False

            if ffmpeg_pipe.returncode != 0:
                logger.error(
                    f"FFmpeg error (return code {ffmpeg_pipe.returncode}): {ffmpeg_error.decode()}"
                )
                return False

            # Check if the file was created
            if os.path.exists(waveform_file) and os.path.getsize(waveform_file) > 0:
                logger.success(f"Waveform generated: {os.path.basename(waveform_file)}")
                # Cleanup temporary script
                try:
                    os.unlink(temp_script.name)
                except:
                    pass
                return True
            else:
                logger.error(
                    f"Waveform generation failed - no output file created at {waveform_file}"
                )
                if plot_error:
                    logger.debug(f"Gnuplot stderr: {plot_error.decode()}")
                if ffmpeg_error:
                    logger.debug(f"FFmpeg stderr: {ffmpeg_error.decode()}")
                # Cleanup temporary script
                try:
                    os.unlink(temp_script.name)
                except:
                    pass
                return False

        except Exception as e:
            logger.error(f"Error generating waveform: {e}")
            # Cleanup temporary script
            try:
                os.unlink(temp_script.name)
            except:
                pass
            return False

    def generate_waveform(self):
        """Generates waveform with gnuplot (only method)"""
        return self.generate_waveform_gnuplot()
