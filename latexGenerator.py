#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  9 11:42:46 2023

@author: ffx
"""

import sys
import os
import numpy as np
import pandas as pd
from tabulate import tabulate
from datetime import datetime

import qrcode
import qrcode.image.svg

import ffmpeg


def get_duration_ffmpeg(file_path):
   probe = ffmpeg.probe(file_path)
   stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
   duration = float(stream['duration'])
   return duration



databaseDIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + 'database'

# scan database for records:
records = next(os.walk(databaseDIR))[1]

""" parsing metadata """
for record in records:
    print("processing ID " + record + "\n")
    recordPath = databaseDIR + '/' + record
    
            
    file = open(recordPath + '/' + "metadata", 'r')
    line=file.readline()
    metadata={}
    tracks = pd.read_csv(recordPath + '/' + "tracktable.csv")
    tracks = tracks.replace(np.nan, '')
    while line != '\n':
        metadata[line.strip().split(',')[0]] = line.strip().split(',')[1]
        line=file.readline()
    while True:      
        if "#cover#" in line:
            covers = []
            line = file.readline()
            while line != '\n':
                covers.append(line.strip())
                line = file.readline()  
                if not line:
                    break
        elif "#videos#" in line:
            videos = []
            line = file.readline()
            while line != '\n':
                videos.append(line.strip())
                line = file.readline()
                if not line:
                    break
        else:
            line = file.readline()
            
        if not line:
            break
        
    videos = np.array(videos)
    """ done parsing Metadata"""
    
    # read analyzed data:
    if os.path.isfile(recordPath + '/' + "analyzed.csv"):
        analyzedData = pd.read_csv(recordPath + '/' + 'analyzed.csv' )
        
    # merg analyzed data from youtube and tracklist:
    trackDF = pd.merge(tracks, analyzedData, on='pos', how='left')
    
    """ if duration is empty but tracks are available, load duration from files: """
    for ind in trackDF.index:
        if trackDF.duration[ind]== '' and trackDF.bpm[ind] !=  'nan':
            try:
                filename = recordPath + '/' + trackDF.pos[ind] + '.m4a'
                seconds = get_duration_ffmpeg(filename)
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)
                trackDF.at[ind, 'duration'] = ("%02d:%02d" % (minutes, seconds))
                trackDF.at[ind,'bpm'] = trackDF.bpm[ind].astype('int')
            except:
                pass
            
        else:
            pass
        
        
    """ correct bpm values to int """

    trackDF["waveform"] = np.nan
    for ind in trackDF.index:
        if os.path.isfile(recordPath + '/' + trackDF.pos[ind]+ '.m4a'):
            filepath = recordPath + '/' + trackDF.pos[ind]+ '_waveform.png'
            trackDF.at[ind, 'waveform'] = '\\includegraphics[width=2cm]{' + filepath + '}'
        else:
            pass
    
    cols = trackDF.columns.tolist()
    
    """ here später noch filter einstlelen für eine platte mit leeren strings (universal artist)"""
    # trackDF['title'] = trackDF['title'] + '  (' + trackDF['artist'] + ')'
    # trackDF['title'] = ' \\tinyb{'  + '\\makecell{' + trackDF['title'] + '  \\\\  (' + trackDF['artist'] + ')}}'
    trackDF['title'] = ' \\tinyb{'  + '\\makecell{' + trackDF['title'] + '  (' + trackDF['artist'] + ')}}'
    trackDF = trackDF.drop('artist',axis=1)
    
    """ replace nan with empty strings: """    
    trackDF = trackDF.replace(np.nan, '')
    
    trackDF.style.format(
     formatter="${}$".format).hide(
        axis=0).to_latex(
        buf="latex.tex")
            
    test = trackDF.style.hide(axis="index")\
            .hide(names=True)\
            .hide(axis="columns")\
            .format(na_rep='MISS', precision=0) \
            .to_latex(\
                column_format="@{}llllll@{}", \
                # hrules=True, \
                multirow_align="t",\
                multicol_align="r")
    

    """ create QR code for record: """
    link = 'discogs.com/release/' + str(metadata['id'])
    img = qrcode.make(link)
    with open(recordPath + '/' + 'qrcode.png', 'wb') as qr:
        img.save(qr)
        
        
    """ extract year: """
    year = metadata["timestamp"][0:4]
    
    
    with open(recordPath + '/' + 'label.tex', 'w') as f:
        f.write("\
                \\includegraphics[width=1cm]{" + recordPath + '/' + "qrcode.png} \
         }; \
        \\node[right,align=left] at (0.1 in,1 in ){ \n  \
          \\begin{fitbox}{12cm}{4cm} \n \
    \\textbf{" + metadata["artist"]+ "} \\\\ % \\[0.25\\baselineskip] \n \
    " + metadata["title"] +" \\\\ \n \
    \\vspace{.1\\baselineskip} \n \
      \\begin{minipage}{6cm} \n \
        \\scriptsize \n ")
        for line in test:
            f.write(line)
        
        f.write("   \\end{minipage} \n \
            \\vspace{.2\\baselineskip} \\\\ \n \
            \\raggedright \\tinyb{ " + metadata["label"] + ', ' + year + ', releaseID: ' + metadata["id"] +"} \\\\ \
            \\end{fitbox} \n \
            }; \n ")

                
                
