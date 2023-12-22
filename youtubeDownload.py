#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 22:52:38 2023

@author: ffx
"""

import os
import sys
import numpy as np
import pandas as pd
from pytube import YouTube 
from fuzzywuzzy import fuzz


def video_info(yt):
    ytTitle = yt.title
    ytLength = int(yt.length)
    return ytTitle, ytLength

databaseDIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + 'database'
records = next(os.walk(databaseDIR))[1]

# if firstRun:
for record in records:
    print("--matching and downloading avail. Videos of recordID: " + record)
    recordPath = databaseDIR + '/' + record
    
    tracks = pd.read_csv(recordPath + '/' + "tracktable.csv")
    tracks = tracks.replace(np.nan, '')
    file = open(recordPath + '/' + "metadata", 'r')
    line=file.readline()
    metadata={}
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
    """ done parsing """
    
    if len(videos) > 0:
        # request and process videotitles from youtube
        videoTitles = []
        videoLengths = []
        for videoURI in videos:
            try:
                yt = YouTube(videoURI)
                ytData = video_info(yt)        
                videoTitles.append(ytData[0])
                videoLengths.append(ytData[1])
            except:
                videoTitles.append(np.nan)
                videoLengths.append(np.nan)
                pass
            
        videos = np.column_stack((videos,videoTitles,videoLengths))
        # tracks = np.array(tracks)    
        correctVideos = []
        # for i in range(len(tracks)):
        for i, row in tracks.iterrows():
            print("processing Track: " + tracks.pos[i])
            track = row
            
            # set artist for each track if there is none set from the tracklist (universal artist for whole record)            
            if track[2] ==  "  ":
                track[2] = metadata["artist"]
            else:
                pass
            
            resultsOftrack = []
            for j in range(len(videos)):
                video = videos[j]
                artist = track[2]
                # print(artist.isspace())
                if artist == '' or artist.isspace():
                    artist = metadata["artist"]
                title = track[1]
                # print(track[2] + "and: "+ track[1])
                resultA = fuzz.partial_ratio(artist + ' - ' + track[1], video[1])
                resultB = fuzz.partial_ratio(track[1], video[1])
                resultC = fuzz.token_sort_ratio(artist + ' - ' + track[1], video[1])
                resultD = fuzz.token_sort_ratio(track[1], video[1])
                # print(resultA, resultB, resultC, resultD)
                resultsOftrack.append(max(resultA,resultB, resultC, resultD))
            
            resultsOftrack = np.array(resultsOftrack)
            # print(max(resultsOftrack))
            maxIndex = (np.argmax(resultsOftrack))
            # print(maxIndex)
            
            if resultsOftrack[maxIndex] >= 90:
                correctVideos.append(videos[maxIndex][0])
                link = videos[maxIndex][0]
                yt = YouTube(link)

                """ select type of stream by itag 140 (m4a - only audio) """                
                # print(yt.streams.filter(only_audio=True))
                try:
                    video = yt.streams.get_by_itag(140)
                    # print("download video of track: " + track)
                    video.download(recordPath + '/')
                except:
                    pass
                
                if os.path.isfile(recordPath + '/' + videos[maxIndex][1]+".mp4"):
                    position = track[0]
                    os.rename(recordPath + '/' + videos[maxIndex][1]+".mp4", recordPath + '/' + track[0]+'.m4a')
                else:
                    content = os.listdir(recordPath)
                    for file in content:
                        if ".mp4" in file:
                            os.rename(recordPath + '/' + file, recordPath + '/' + track[0]+'.m4a')
                        else:
                            pass
                    
                    pass
                
            else:
                correctVideos.append('NaN')
                # print("not matched:")
                # # print(max(resultsOftrack))
                # # print("tracklist: " + tracks[j][2] + ' - ' + tracks[j][1])
                # # print("videotitle: " + videos[maxIndex][1])
                # # print("examples:")
                # # print(fuzz.ratio(track[2] + ' - ' + track[1], videos[maxIndex][1]))
                # print(fuzz.token_sort_ratio(track[2] + ' - ' + track[1], videos[maxIndex][1]))
                # print(fuzz.token_sort_ratio(track[1], videos[maxIndex][1]))
                # print(fuzz.partial_ratio(track[1], videos[maxIndex][1]))
                # print(fuzz.partial_ratio(track[2] + ' - ' + track[1], videos[maxIndex][1]))
                # # print(jellyfish.levenshtein_distance(track[1], videos[maxIndex][1]))
                # # print(jellyfish.damerau_levenshtein_distance(track[1], videos[maxIndex][1]))
                # print("")
    else:
        pass
    
    print("\n")
