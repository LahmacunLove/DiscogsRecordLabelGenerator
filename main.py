#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created on Tue Sep 26 14:22:29 2023

@author: ffx
"""


import os
import sys
import time
import math
from datetime import datetime
from datetime import timedelta
import pickle
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats

# loading gc
import gc


import discogs_client
# from discogs_client.exceptions import HTTPError

from pytube import YouTube 
from fuzzywuzzy import fuzz

import shutil
import librosa
import io
import subprocess
import soundfile as sf
import librosa.display
import keyfinder
from pylatexenc.latexencode import unicode_to_latex

# animated_qrcode.py

import segno
from urllib.request import urlopen


script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
databaseDIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + 'database'

""" 
was gibts zu tun?

Alles hier zusammen führen
- latex zusammenführen, anordnung der sticker für jede seite passend machen (digitale tabelle anlegen mit ID's welche gedruckt wurden und abspeichern(!)')
- tabelle einlesen was gedruckt wurde um diese zu skippen
- record for record von discogs - zum ermöglichen von parallel processing
- check if video bereits da
- check if analyze bereits da / waveform / bpm / key
- unterscheidung bei videosuche für edits (!macht probleme, manchmal wird ein video zwei tracks zugeordnet, erfordert bessere unterscheidung)
- lesen von timestamp und filtern in record library
- eingabe von optionen zum starten aus terminal
- grafische oberfläche
- optionales lesen einer digitalen bibliothek, falls z.B. bandcamp alben auch abgelegt sind
- design des latex exports
- erstellen von stickern anhand von spezifischen IDs (anstelle der timestamp funktion)
- wahl des ordners der library von discogs (oder alle falls möglich als option?)
- genre auf label mitaufdrucken? oder evtl. noch rating?
- variablen reduzieren (KISS!) -- speicher freigeben (RAM bedarf reduzieren)
- routine einbauen, welche position NaN und leere Titel erkennt, bei einer platte ist auch unter pos leere tracks!!!
"""

def convert_to_datetime(datetime_string):
    tz_offset = datetime.strptime(datetime_string[-5:], "%H:%M")
    return datetime.strptime(datetime_string[:-6], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=tz_offset.hour)
        

print("starting discogs script\n")
# reading token from local file:
f = open(os.path.expanduser('~') + '/.config/discogs_token', "r")
discogs_token=f.read().strip()
f.close()


# connectiong to discogs:
d = discogs_client.Client('DiscogsRecordLabeler/0.1', user_token=discogs_token)
me = d.identity()

# user input for selecting the discogs folder to analyze:    
# for i in range(len(me.collection_folders)):
    # print(str(i+1) + '  -  ' + me.collection_folders[i].data['name'])
# folderSelection = int(input("select discogs folder to analyze:")) - 1


# request library from discogs:
# collection = me.collection_folders[folderSelection].releases
collection = me.collection_folders[5].releases

def crawlReleaseData(collectionElement,timestampOfRecord, databaseDIR):
    
    elementDirectory = databaseDIR + '/' + str(collectionElement.id)
    
    if not os.path.exists(elementDirectory):
        os.makedirs(elementDirectory)
    
    # retrieve Metadata
    if not os.path.isfile(elementDirectory + '/' + 'metadata' ):
        metaData = {
            "title": collectionElement.title,
            "artist": [r.name for r in collectionElement.artists],
            "label": [label.name for label in collectionElement.labels],
            "genres": collectionElement.genres,
            "formats": collectionElement.formats[0],
            "year": collectionElement.year,
            "id": collectionElement.id,
            "timestamp": timestampOfRecord,
            "videos" : [video.url for video in collectionElement.videos]
            }
        with open(elementDirectory + '/' + 'metadata', 'wb') as fp:
            pickle.dump(metaData, fp)
            # print('metadata saved successfully to file')
    else: #if metadata alread there, skip it!
        pass
    
    # retrieve Tracklist 
    if not os.path.isfile(elementDirectory + '/' + 'tracklist.csv' ):
        # print("tracklist nicht vorhanden")
        # generate tracktable:
        tracklist = []
        for track in collectionElement.tracklist:
            tracklist.append([track.position, track.title, ','.join([r.name for r in track.artists]),track.duration])
        #convert to pandas:
        tracklist = np.array(tracklist)
        tracklist = pd.DataFrame(tracklist, columns=['pos', 'title', 'artist', 'duration'])
        # save to file (which was not existing:)
        tracklist.to_csv(elementDirectory + '/' + 'tracklist.csv', index=False)
    else:
        pass
    
    # retrieve Cover Image:
    if not os.path.isfile(elementDirectory + '/' + 'cover.jpg' ):
        try:
            imageURL = collectionElement.images[0]['uri']
        except:
            imageURL = ''
        
        if imageURL != '':
            try:
                print("downloading Cover of " + str(collectionElement.id))
                urllib.request.urlretrieve(imageURL, elementDirectory + '/' + 'cover.jpg')
            except:
                pass
        else:
            pass
    return

def video_info(yt):
    ytTitle = yt.title
    ytLength = int(yt.length)
    ytArtist = yt.author
    return ytTitle, ytLength, ytArtist

def retrieveYoutubeMetadata(videos):
    # request, process and return metadata of youtube videos
    # if len(videos) > 0:
    videoTitles = []
    videoLengths = []
    videoArtists = []
    for videoURI in videos:
        try:
            yt = YouTube(videoURI)
            ytData = video_info(yt)        
            videoTitles.append(ytData[0])
            videoLengths.append(ytData[1])
            videoArtists.append(ytData[2])
        except:
            videoTitles.append(np.nan)
            videoLengths.append(np.nan)
            videoArtists.append(np.nan)
            pass
    return np.column_stack((videos,videoTitles,videoArtists,videoLengths))


def duplicates(arr):
    return [elem in arr[:i] for i, elem in enumerate(arr)]


def matchVideosWithTracklist(tracklist,metadata,databaseDIR):
    videos = retrieveYoutubeMetadata(metadata["videos"])
    tracklist.artist.fillna(' & '.join(metadata["artist"]), inplace=True)
    recordPath = databaseDIR + '/' + str(metadata['id'])    
    
    for video in videos:
        if video[3] !=  "nan":
            pass
        else:
            pass

    videos = np.c_[videos,np.empty((videos.shape[0],1))] # add empty column
    videos[:,4] = [np.nan for value in videos[:,4]] # set column to nan
    videos = np.c_[videos,np.empty((videos.shape[0],1))] # add empty column
    videos[:,5] = [np.nan for value in videos[:,5]] # set column to nan
    videos = np.array(videos, dtype=object)
    
    for i in range(len(videos)):
        video = videos[i]
        stringCompareResultsOfTrack =  []
        
        for j in range(len(tracklist)):
            trackArtist = tracklist.artist[j]
            trackTitle = tracklist.title[j]
            
            # erzeuge vergleiche:
            resultA = fuzz.partial_ratio(trackArtist + ' - ' + trackTitle, video[2] + ' - ' + video[1])
            resultB = fuzz.partial_ratio(trackTitle, video[1])
            resultC = fuzz.token_sort_ratio(trackArtist + ' - ' + trackTitle, video[1])
            resultD = fuzz.token_sort_ratio(trackTitle, video[1])
            
            stringCompareResultsOfTrack.append([resultA,resultB, resultC, resultD])
        
        stringCompareResultsOfTrack = np.array(stringCompareResultsOfTrack)
        
        """get highest match of title / string comparision:"""
        index_max = np.argmax([sum(result) for result in stringCompareResultsOfTrack])
        
        # Check if any value in this match is at least 95
        if any(num >= 95  for num in stringCompareResultsOfTrack[index_max]):
            videos[i][4] = tracklist.pos[index_max]
            videos[i][5] = stringCompareResultsOfTrack[index_max]
        else:
            # print(stringCompareResultsOfTrack)
            pass

    # download videos:
    for video in videos:
        if video[4] != np.nan and video[4] != 'nan':
            filename = video[4]+'.m4a'
            if not os.path.isfile(databaseDIR + '/'+ str(metadata['id']) + '/' + filename):
                try:
                    url = video[0]
                    yt = YouTube(url)
                    youtube = yt.streams.get_by_itag(140) # m4a stream
                    youtube.download(recordPath + '/',filename=video[4] +'.m4a')
                except:
                    pass
            else:
                pass
        else:
            pass
                
    # adjust duration of track if not in tracklist and duration is available for youtube video
    if tracklist.duration.isna: #check if there is nan in the tracklist durations
        for video in videos:
            if tracklist.loc[tracklist['pos'] == video[4]].isna and video[3] != 'nan': #check for nan in particular row
                duration = time.strftime("%M:%S", time.gmtime(int(float(video[3]))))
                tracklist.loc[tracklist['pos'] == video[4],'duration'] = duration
                pass
            else:
                pass
        tracklist.to_csv(recordPath + '/' + 'tracklist.csv', index=False) # save to tracklist file
    else:
        pass 
        
    return


def downloadYoutube(collectionElement, databaseDIR):
    elementID = str(collectionElement.id)
    if os.path.exists(databaseDIR + '/' + elementID):
        tracklist = pd.read_csv(databaseDIR + '/' + elementID + '/' +  'tracklist.csv')
        # Read dictionary pkl file
        with open(databaseDIR + '/' + elementID + '/' + 'metadata', 'rb') as fp:
            metadata = pickle.load(fp)
            matchVideosWithTracklist(tracklist, metadata, databaseDIR)
    else:
        pass
    return



def analyzeDownloadedVideos(collectionElement, databaseDIR):
    
    """read old analyzed.csv file:"""
    try:
        analyzed = pd.read_csv(databaseDIR + '/' + str(collectionElement.id) + '/' + 'analyzed.csv')
    except FileNotFoundError: 
        analyzed = pd.DataFrame(columns=['pos', 'bpm', 'key'])
    
    """compare with FILES(!) and only analyze slots which have not yet been analyzed: """
    
    
    recordPath = databaseDIR + '/' + str(collectionElement.id)
    #get downloaded youtube videos on local disk:
    files = [file for file in os.listdir(recordPath) if file.endswith(".m4a")]
    
    # options:
    waveformGen= True
    keyAndBpmCHeck = True
    sampleRate = 44100
    # sampleRate = 22050
    
    results = []
    
    for file in files:
        if file.endswith(".m4a") and file[:-4] not in analyzed.pos.unique():
            # set ffmpeg command:
            ffmpeg_command = ["ffmpeg", "-i", recordPath + '/' + file,
                            "-ac", "1", "-filter:a", "aresample="+str(sampleRate), "-map", "0:a", "-c:a", "pcm_s16le", "-f", "data", '-']
            # ffmpeg_command = ["ffmpeg", "-i", recordPath + '/' + file,
                            # "-ac", "1", "-filter:a", "-map", "0:a", "-c:a", "pcm_s16le", "-f", "data", '-']
            # run ffmpeg command pipe:
            ffmpeg_pipe = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)            
            """ generate waveform: """
            if waveformGen: 
                if not os.path.isfile(recordPath +'/'+ file[:-4]+ "_waveform.png"):
                    #define gnuplot command:
                    gnuplot_command = ['gnuplot', '-persist', '-c', 'waveform.gnuplot', "set terminal png size 5000,500;\n", "set output 'blabla.png';\n;"]
                    #start gnuplot as subprocess:
                    plot = subprocess.Popen(gnuplot_command, stdin=ffmpeg_pipe.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    #send gnuplot command and end process:
                    plot.communicate("set terminal png size 5000,500;\n set output 'blabla.png';\n;") # inhalt funktioniert nicht, aber ist wichtig um die plots richtig zu erstellen
                    del plot
                    #move waveform file to record folder and rename it:
                    if os.path.isfile("waveform.png"):
                        shutil.move("waveform.png", recordPath +'/'+ file[:-4]+ "_waveform.png")
                    else:
                        pass
                else:
                    pass
            else:
                pass
            
            if keyAndBpmCHeck:
                # print("bpm check")
                hop_length=512
                y, sr = sf.read(io.BytesIO(ffmpeg_pipe.stdout.read()), format='RAW', samplerate=sampleRate, channels=1, subtype="PCM_16", endian='LITTLE')
                # print("2")
                onset_env = librosa.onset.onset_strength(y=y, sr=sampleRate, hop_length=hop_length)
                # print("3")
                                
                bpm = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)[0]
                print(bpm)
                key = keyfinder.key(recordPath + '/' + file)
                
                results.append([file[:-4], str(int(np.round(bpm))), key.camelot()])
                

                # Convert to scalar
                tempo = bpm.item()
                prior = scipy.stats.uniform(30, 300)
                utempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr, prior=prior)
                utempo = utempo.item()
                # dtempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr,
                               # aggregate=None)
                # prior_lognorm = scipy.stats.lognorm(loc=np.log(120), scale=120, s=1)
                # dtempo_lognorm = librosa.feature.tempo(onset_envelope=onset_env, sr=sr,
                               # aggregate=None,
                               # prior=prior_lognorm)
                
                # Compute 2-second windowed autocorrelation
                hop_length = 512
                ac = librosa.autocorrelate(onset_env, max_size=2 * sr // hop_length)
                freqs = librosa.tempo_frequencies(len(ac), sr=sr,
                                                  hop_length=hop_length)
                # Plot on a BPM axis.  We skip the first (0-lag) bin.
                fig, ax = plt.subplots()
                ax.semilogx(freqs[1:], librosa.util.normalize(ac)[1:],
                             label='Onset autocorrelation', base=2)
                ax.axvline(tempo, 0, 1, alpha=0.75, linestyle='--', color='r',
                            label='Tempo (default prior): {:.2f} BPM'.format(tempo))
                ax.axvline(utempo, 0, 1, alpha=0.75, linestyle=':', color='g',
                            label='Tempo (uniform prior): {:.2f} BPM'.format(utempo))
                ax.set(xlabel='Tempo (BPM)', title='Static tempo estimation: '+ collectionElement.title + ' - ' + file[:-4])
                ax.grid(True)
                ax.legend()
                # plt.show()
                plt.savefig(recordPath + '/' + 'static_tempo_est_' + file[:-4] + '.pdf', bbox_inches='tight')
                # plt.show()
                plt.close()
                del ac, utempo, prior, tempo, bpm, key, onset_env, y, sr, ffmpeg_pipe
                
                # fig, ax = plt.subplots()
                # tg = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr,
                #                                hop_length=hop_length)
                # librosa.display.specshow(tg, x_axis='time', y_axis='tempo', cmap='magma', ax=ax)
                # ax.plot(librosa.times_like(dtempo), dtempo,
                #          color='c', linewidth=1.5, label='Tempo estimate (default prior)')
                # ax.plot(librosa.times_like(dtempo_lognorm), dtempo_lognorm,
                #          color='c', linewidth=1.5, linestyle='--',
                #          label='Tempo estimate (lognorm prior)')
                # ax.set(title='Dynamic tempo estimation')
                # ax.legend()
                # plt.show()
                # plt.close()
            if 'ffmpeg_pipe' in locals():
                del ffmpeg_pipe
            else:
                pass
        else:
            # print("wurde bereits analysiert")
            pass
                
    results = pd.DataFrame(results, columns = ['pos', 'bpm', 'key']) 
    results = results.sort_values('pos')
    results = pd.concat([analyzed, results], ignore_index=True)
    results.to_csv(recordPath + '/' + 'analyzed.csv', index=False)
    
    return


def createQRCode(collectionElement, databaseDIR):
    if os.path.isfile(databaseDIR + '/' + str(collectionElement.id) + '/' + "cover.jpg"):
        # print("cover existiert")
        if not os.path.isfile(databaseDIR + '/' + str(collectionElement.id) + '/' + 'qrcode.png'):
            #create qr code:
            slts_qrcode = segno.make_qr('discogs.com/release/' + str(collectionElement.id), error='l')
            #save qr code with cover in background:
            slts_qrcode.to_artistic(
                background=databaseDIR + '/' + str(collectionElement.id) + '/' + 'cover.jpg',
                target=databaseDIR + '/' + str(collectionElement.id) + '/' + 'qrcode.png',
                scale=10
            )
        else:
            pass # qr code existiert
    else:
        pass # kein cover (hier vlt. dann ein qr code anlegen ohne cover?)
    return

def inplace_change(filename, old_string, new_string):
    # Safely read the input filename using 'with'
    with open(filename) as f:
        s = f.read()
        if old_string not in s:
            print('"{old_string}" not found in {filename}.'.format(**locals()))
            return
        
        # Safely write the changed content, if found in the file
    with open(filename, 'w') as f:
        print('Changing "{old_string}" to "{new_string}" in {filename}'.format(**locals()))
        s = s.replace(old_string, new_string)
        f.write(s)
    return

def createLatexLabelFile(collectionElement, databaseDIR):
    recordPath = databaseDIR + '/' + str(collectionElement.id)
    if os.path.isfile(recordPath + '/' + 'label.tex'):
        # print("label wird erstellt")
        #read metadata:
        with open((recordPath + '/' + 'metadata'), 'rb') as fp:
            metadata = pickle.load(fp)
        # read tracklist:
        tracklist = pd.read_csv(recordPath + '/' + 'tracklist.csv' )
        # read analyze results:
        analyzedData = pd.read_csv(recordPath + '/' + 'analyzed.csv' )
        #merge data:
        trackDF = tracklist.merge(analyzedData, how='left')
        
        """ replace nan with empty strings: """    
        trackDF = trackDF.replace(np.nan, '')
        trackDF = trackDF.applymap(unicode_to_latex)
        
        """ add waveform: """
        trackDF["waveform"] = np.nan
        for ind in trackDF.index:
            if os.path.isfile(recordPath + '/' + trackDF.pos[ind]+ '.m4a'):
                filepath = recordPath + '/' + trackDF.pos[ind]+ '_waveform.png'
                trackDF.at[ind, 'waveform'] = '\\includegraphics[width=2cm]{' + filepath + '}'
            else:
                pass
            
        # create pandas style for table
        trackDFStyle = trackDF.style.hide(axis="index")\
                .hide(names=True)\
                .hide(axis="columns")\
                .format(na_rep='', precision=0)

        # get rid of the artist / various artist problem:
        if len(tracklist.artist.unique()) ==  1:
        #     print("alles kein problem")
            trackDFStyle = trackDFStyle.hide_columns(subset=["artist"])
        else:
            trackDF.title = trackDF.title +' / ' + trackDF.artist
            trackDFStyle = trackDFStyle.hide_columns(subset=["artist"])
            
        latex = trackDFStyle.to_latex(\
                    column_format="@{}lXlllc@{}", \
                    # hrules=True, \
                    multirow_align="t",\
                    multicol_align="r")
                
        """ extract year: """
        year = metadata["timestamp"].strftime("%Y")
        
        with open(recordPath + '/' + 'label.tex', 'w') as f:
            f.write(#\
                "\
                    \\begin{fitbox}{8cm}{4.5cm} \n \
                    \\textbf{" + unicode_to_latex(', '.join(metadata["artist"])) + "} \\newline \n \
                        " + unicode_to_latex(metadata["title"]) + "\n \
                    \\vfill \n \
                    % \\begin{minipage}{8cm} \n \
                    \\scriptsize \n ")
            for line in latex:
                f.write(line)
            f.write(" \
                    %\\end{minipage} \n \
                \\vfill \n \
                \\raggedright \\tinyb{ " + unicode_to_latex(', '.join(metadata["label"])) + ', ' + year + ', releaseID: ' + str(metadata["id"]) +"}\n \
                \\end{fitbox}")
                
        inplace_change(recordPath + '/' + 'label.tex', "\\begin{tabular}", "\\begin{tabularx}{8.5cm}")
        inplace_change(recordPath + '/' + 'label.tex', "\\end{tabular}", "\\end{tabularx}")
                    
    else:
        print("label schon vorhanden")
        pass
    
    return


# for i in range(len(collection)):
for i in range(0,20):
    print("processing id: " + str(collection[i].data['id']) + '  --  ' + collection[i].release.title)
    # print(unicode_to_latex(collection[i].release.title))
    timestampRecordAdded = convert_to_datetime(collection[i].data['date_added'])
    
    print("retrieving metadata from discogs")
    crawlReleaseData(collection[i].release,timestampRecordAdded, databaseDIR)
    
    print("downloading videos from youtube:")
    downloadYoutube(collection[i].release, databaseDIR)
    
    print("analyze videos:")
    analyzeDownloadedVideos(collection[i].release, databaseDIR)
    
    print("create qr codes:")
    createQRCode(collection[i].release, databaseDIR)
    
    print("creating latex label file for record:")
    createLatexLabelFile(collection[i].release, databaseDIR)
    print()
     
    # get the current collection 
    # thresholds as a tuple
    print("Garbage collection thresholds:",
                        gc.get_threshold())
    collected = gc.collect()
    print("Garbage collector: collected",
          "%d objects." % collected)
    print()

    
    
def combineLatex(databaseDIR, exportDIR):
    records = next(os.walk(databaseDIR))[1]
    stickersToPrint = len(records)
    stickersToPrint = 15
    pagesToPrint = math.ceil(stickersToPrint / 10)
    
    with open(exportDIR + '/' + 'output.tex', 'w') as f:
        latexPreamble = open(script_directory + '/' + 'functions' + '/' +'latexPreamble.tex', 'r')
        for line in latexPreamble:
            f.write(line)
        latexPreamble.close()
        
        release = 0
        x,y,p = 0,0,0
        
        for p in range(0,pagesToPrint):
            if release > len(records):
                break    
            f.write("\\begin{tikzpicture}[thick,font=\Large] \n")
            for y in range(0,5):
                if release > len(records):
                    break    
                for x in [0,1]:
                    release = (x+1) + (y*2) + (p*10)
                    if release > len(records):
                        break                        
                    xPos = 4.1 * x
                    yPos = y * -2
                    #frame:
                    f.write("\t\\draw[rounded corners=0.5cm] ("+str(xPos)+" in, "+str(yPos)+" in) rectangle +(4in,2in);\n")
                    #qr code:
                    f.write("\\node[right,align=left] at ("+str(xPos + 3.3)+" in, +" + str(yPos-0.36+2)+" in ){\
     \includegraphics[width=1.5cm]{../database/" + str(records[release-1]) + '/' + "qrcode.png}\
     };\n")                    
                    #text:
                    f.write("\t\\node[right,align=left] at ("+str(xPos) + " in, " + str(yPos+1) + " in){\n\t\t\t")
                    # f.write("release: " + str(release))
                    # f.write("\t\\input{../database/22233/label.tex}\n \t \t \t")
                    f.write("\t\\input{../database/" + str(records[release-1]) + "/label.tex}\n \t \t \t")
                    f.write("};\n")

            f.write("\\end{tikzpicture}\n\\clearpage\n")
        f.write("\
\end{document}\n\
")
    
    return

exportDIR = script_directory + '/' + 'export'
test = combineLatex(databaseDIR, exportDIR)