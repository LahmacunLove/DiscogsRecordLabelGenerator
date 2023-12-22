#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 22:52:38 2023

@author: ffx
"""



"""
1. analyze video file
2. visualize data (ffmpeg / gnuplot)
"""

import os
import sys
import shutil
import librosa
import numpy as np
import pandas as pd
import io
import subprocess
import soundfile as sf
import librosa.display
import keyfinder


databaseDIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + 'database'

# scan database for records:
records = next(os.walk(databaseDIR))[1]

# options:
waveformGen= True
keyAndBpmCHeck = True
sampleRate = 22050

# if firstRun:
for record in records:
    print("processing ID " + record + "\n")
    recordPath = databaseDIR + '/' + record
    
    files = os.listdir(recordPath)
    results = []
    for file in files:
        if ".m4a" in file:
            audioFile = recordPath + '/' + file
            print("file exists: " + audioFile)

            ffmpeg_command = ["ffmpeg", "-i", recordPath + '/' + file,
                            "-ac", "1", "-filter:a", "aresample="+str(sampleRate), "-map", "0:a", "-c:a", "pcm_s16le", "-f", "data", '-']
            ffmpeg_pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)            
            print('ffmpeg Done!!!')
            """ generate waveform: """
            if waveformGen: 
                gnuplot_command = ['gnuplot', '-persist', '-c', 'waveform.gnuplot', "set terminal png size 5000,500;\n", "set output 'blabla.png';\n;"]
                plot = subprocess.Popen(gnuplot_command, stdin=ffmpeg_pipe.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # plot.write("set terminal png size 5000,500;\n")
                plot.communicate("set terminal png size 5000,500;\n set output 'blabla.png';\n;") # inhalt funktioniert nicht, aber funktion ist wichtig um die plots richtig zu erstellen
                print("gnuplot done!")  
                
                if os.path.isfile("waveform.png"):
                    shutil.move("waveform.png", recordPath +'/'+ file[:-4]+ "_waveform.png")
                else:
                    pass
                
            else:
                pass
            
            
            if keyAndBpmCHeck:
                hop_length=512
                y, sr = sf.read(io.BytesIO(ffmpeg_pipe.stdout.read()), format='RAW', samplerate=sampleRate, channels=1, subtype="PCM_16", endian='LITTLE')
                onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
                
                bpm = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)[0]
                key = keyfinder.key(recordPath + '/' + file)
                
                results.append([file[:-4], str(int(np.round(bpm))), key.camelot()])
                
                
                
                
    results = pd.DataFrame(results, columns = ['pos', 'bpm', 'key']) 
    results = results.sort_values('pos')
    results.to_csv(recordPath + '/' + 'analyzed.csv', index=False)
